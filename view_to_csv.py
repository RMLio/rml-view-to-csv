"""
This module holds the View-to-CSV-Convertor class which is responsible for converting an RML mapping containing views
to an RML mapping without views. All views are materialized as CSV files and added to the resulting RML mapping as
conventional logical sources.
"""

import argparse
import sys
from collections import defaultdict
from io import StringIO

import pandas as pd
from rdflib import Graph, Literal, BNode

import util
from namespaces import *
from ref_object_map_to_view import ref_object_map_to_view
from util import *


class ViewToCsvConvertor:
    """
    Converts an RML Mapping file from a file with views to a file without views.
    Also Materializes the views as CSV files.
    """

    def __init__(self, mapping: str, output_dir: str, old_rml: bool = False, optimize: bool = False,
                 no_ref_object_map: bool = False):
        """Create an instance of the ViewToCsvConvertor class.

        Parameters
        ----------
        mapping : str
            The mapping file that will be converted.
        output_dir: str
            Directory to which the output is saved
        old_rml : bool
            Enables the use of old RML namespaces and vocabulary in the resulting mapping file.
        optimize : bool
            Enables the optimization of the materialized view based on the triples maps.
        """
        self.mapping = resolve_path(mapping)
        self.output_dir = resolve_path(output_dir, True)
        self.old_rml = old_rml
        self.optimize = optimize
        self.no_ref_object_map = no_ref_object_map
        self.logical_views = {}
        self.logical_sources = {}
        self.fields = {}
        self.joins = {}
        self.materialized_logical_views = {}
        self.g = Graph()

    def read_mapping(self) -> None:
        """Read the mapping file and store useful data in self.mapping_info

        """
        self.g.parse(self.mapping)

        if self.no_ref_object_map:
            ref_object_map_to_view(self.g)
            self.g.serialize(destination='./no-ref-object-map.ttl', encoding='utf-8')
        field_results = self.g.query(queries.fields)
        for row in field_results:
            self.fields.setdefault(row.Field, {'id': row.Field, 'name': row.Name.value, 'parent': row.Parent,
                                               'children': set(), 'reference_formulation': None, 'iterator': None,
                                               'iterable': False})
            if row.Parent in self.logical_views:
                # to indicate that the parent is the root iterator
                self.fields[row.Field]['parent'] = '<it>'
            else:
                self.fields[row.Field]['parent'] = row.Parent
            if row.Constant:
                self.fields[row.Field]['constant'] = row.Constant.value
            if row.Reference:
                self.fields[row.Field]['reference'] = row.Reference.value
            if row.Template:
                self.fields[row.Field]['template'] = row.Template.value
            if row.Child:
                self.fields[row.Field]['children'].add(row.Child)
            if row.ReferenceFormulation:
                self.fields[row.Field]['reference_formulation'] = row.ReferenceFormulation
            if row.Iterator:
                self.fields[row.Field]['iterator'] = row.Iterator
            # add default iterator for JSON
            if self.fields[row.Field]['reference_formulation'] \
                and 'JSONPath' in self.fields[row.Field]['reference_formulation']  \
                and not self.fields[row.Field]['iterator']:
                self.fields[row.Field]['iterator'] = '$'
            # if a field has a reference_formulation or an iterator, it is an iterable field
            if self.fields[row.Field]['iterator'] or self.fields[row.Field]['reference_formulation'] :
                self.fields[row.Field]['iterable'] = True
            else:
                self.fields[row.Field]['reference_formulation'] = 'EXPRESSION'
        source_results = self.g.query(queries.sources)
        for row in source_results:
            self.logical_sources.setdefault(row.LogicalSource, {'id': row.LogicalSource,
                                                                'reference_formulation': RML2['Fields'],
                                                                'iterator': RML2['row']})
            if row.Source:
                self.logical_sources[row.LogicalSource]['source'] = row.Source.value
            if row.ReferenceFormulation:
                self.logical_sources[row.LogicalSource]['reference_formulation'] = row.ReferenceFormulation
            if row.Iterator:
                self.logical_sources[row.LogicalSource]['iterator'] = row.Iterator.value

        view_results = self.g.query(queries.views)
        for row in view_results:
            self.logical_views.setdefault(row.LogicalView, {'id': row.LogicalView, 'fields': set(), 'joins': set()})
            self.logical_views[row.LogicalView]['logical_source'] = row.LogicalSource
            self.logical_views[row.LogicalView]['fields'].add(row.Field)
            # add any enherited reference formulations to the fields
            nested_fields = []
            for field in self.logical_views[row.LogicalView]['fields']:
                # at the first level add the reference formulation of the logical source
                if not self.fields[field]['reference_formulation']:
                    self.fields[field]['reference_formulation'] = self.logical_sources[row.LogicalSource][
                        'reference_formulation']
                # add nested fields
                for new_field in self.fields[field]['children']:
                    nested_fields.append(new_field)
            while nested_fields:
                field = nested_fields.pop(0)
                if not self.fields[field]['reference_formulation']:
                    self.fields[field]['reference_formulation'] = self.fields[self.fields[field]['parent']][
                        'reference_formulation']
                for new_field in self.fields[field]['children']:
                    nested_fields.append(new_field)
            if row.Join:
                self.logical_views[row.LogicalView]['joins'].add(row.Join)
            if self.optimize:
                self.logical_views[row.LogicalView]['used_references'] = util.get_all_references_per_view(self.g,
                                                                                                          row.LogicalView)
                self.logical_views[row.LogicalView]['remove_duplicates'] = util.safe_removal_of_duplicates(self.g,
                                                                                                           row.LogicalView)

        def add_join(_row, _join_type):
            # join type according to the keys in pandas merge: left_join = 'left', inner_join = 'inner'
            self.joins.setdefault(_row.Join, {'child_logical_view': _row.ChildLogicalView,
                                              'parent_logical_view': _row.ParentLogicalView,
                                              'fields': set(),
                                              'join_conditions': {},
                                              'join_type': _join_type})
            self.joins[_row.Join]['fields'].add(_row.Field)
            self.joins[_row.Join]['join_conditions'][_row.JoinCondition] = {'parent': _row.Parent.value,
                                                                            'child': _row.Child.value}

        left_join_results = self.g.query(queries.left_joins)
        for row in left_join_results:
            add_join(row, 'left')

        inner_join_results = self.g.query(queries.inner_joins)
        for row in inner_join_results:
            add_join(row, 'inner')

    def get_parent_df(self, parent_view: dict, fields_from_join: dict, join_values_right: list) -> pd.DataFrame:
        if parent_view['id'] not in self.materialized_logical_views:
            df = self.materialize_logical_view(parent_view)
        else:
            source = self.materialized_logical_views[parent_view['id']]
            types = defaultdict(lambda: str)
            df = pd.read_csv(source, usecols=list(fields_from_join.keys()) + join_values_right, dtype=types)
        # giving the join condition a recognizable name, so this column can be deleted after the join action
        for join_value_right in join_values_right:
            df[join_value_right + '_parent_join_condition_value'] = df.loc[:, join_values_right]
        df.rename(columns=fields_from_join, inplace=True)
        return df

    def materialize_logical_view(self, logical_view: dict) -> pd.DataFrame:
        """Materialize logical view as CSV file

        Parameters
        ----------
        logical_view : dict
            The dictionary containing the information about the logical view
        """
        df = pd.DataFrame()

        logical_source = self.logical_sources[logical_view['logical_source']]

        if logical_source['reference_formulation'] == RML2['Fields']:
            if logical_source['id'] not in self.materialized_logical_views.keys():
                self.materialize_logical_view(logical_source['id'])
            df = self.make_view_from_csv(self.materialized_logical_views[logical_source['id']], logical_view)
        elif 'CSV' in logical_source['reference_formulation']:
            df = self.make_view_from_csv(logical_source['source'], logical_view)
        elif 'JSONPath' in logical_source['reference_formulation']:
            df = self.make_view_from_json(logical_source['source'], logical_source['iterator'], logical_view)
        elif 'XPath' in logical_source['reference_formulation']:
            raise Exception("XPath not implemented")
        # add fields from join
        for join_key in logical_view['joins']:
            join = self.joins[join_key]
            parent_logical_view = self.logical_views[join['parent_logical_view']]
            fields_parent = get_fields_for_renaming(join['fields'], self.fields)
            join_conditions = join['join_conditions']
            join_values_left = []
            join_values_right = []
            for join_condition in join_conditions.values():
                join_values_left.append(join_condition['child'])
                join_values_right.append(join_condition['parent'])

            # get parent view df
            if parent_logical_view['id'] not in self.materialized_logical_views:
                parent_df = self.materialize_logical_view(parent_logical_view)
            else:
                source = self.materialized_logical_views[parent_logical_view['id']]
                types = defaultdict(lambda: str)
                parent_df = pd.read_csv(source, usecols=list(fields_parent.keys()) + join_values_right, dtype=types)
            # giving the join condition a recognizable name, so this column can be deleted after the join action
            join_values_right_suffixed = [join_value_right + '_parent_join_condition_value' for join_value_right in
                                          join_values_right]
            for join_value_right in join_values_right:
                parent_df[join_value_right + '_parent_join_condition_value'] = parent_df.loc[:, join_values_right]

            parent_df.rename(columns=fields_parent, inplace=True)
            # remove unnecessary columns
            for col in parent_df.columns:
                if col not in list(fields_parent.values()) + join_values_right_suffixed:
                    del parent_df[col]

            # groupby on parent join keys > we need lists to add the indexes after the join
            parent_df = parent_df.groupby(join_values_right_suffixed).agg(pd.Series.tolist).reset_index()
            # add index
            for field_name in fields_parent.values():
                parent_df[field_name + '.#'] = parent_df[field_name].apply(add_iteration_index)
            explode_list = parent_df.columns.tolist()
            for column in explode_list:
                if column in join_values_right_suffixed:
                    explode_list.remove(column)
            parent_df = parent_df.explode(explode_list)

            # join
            df = pd.merge(df, parent_df, left_on=join_values_left, right_on=join_values_right_suffixed,
                          how=join['join_type'], suffixes=('', '_parent'))

            for join_value_right_suffixed in join_values_right_suffixed:
                del df[join_value_right_suffixed]

            # after every join: remove unnecessary fields and duplicates
            if self.optimize:
                for col in df.columns:
                    if col not in logical_view['used_references']:
                        del df[col]
                if logical_view['remove_duplicates']:
                    df = df.drop_duplicates(ignore_index=True)

        # at the end one more check to remove unnecessary field and duplicates
        if self.optimize:
            # after every join: remove unnecessary fields and duplicate
            for col in df.columns:
                if col not in logical_view['used_references']:
                    del df[col]
            if logical_view['remove_duplicates']:
                df = df.drop_duplicates(ignore_index=True)

        filename = os.path.join(self.output_dir, 'view' + str(len(self.materialized_logical_views)) + '.csv')
        # moving the # column to the second column because RMLMapper cannot handle # as first column
        df.insert(1, '#', df.pop('#'))
        df.to_csv(filename, index=False, encoding='utf-8')
        self.materialized_logical_views[logical_view['id']] = filename
        return df

    def add_fields(self, df, fields_to_be_added):
        if fields_to_be_added:
            siblings = fields_to_be_added.pop(0)
            siblings = list(siblings)
            new_field_parent = self.fields[siblings[0]]['parent']
            new_field_parent_reference_formulation = self.fields[new_field_parent]['reference_formulation']
            fields_to_be_added_siblings, converted_fields = self.get_info_from_siblings(siblings, True)
            if fields_to_be_added_siblings:
                fields_to_be_added = fields_to_be_added + fields_to_be_added_siblings
            new_field_parent_name = self.fields[new_field_parent]['name']
            # the parent is an iterable JSON field
            if 'JSONPath' in new_field_parent_reference_formulation:
                # if iterator, first apply iterator to parent
                #if self.fields[new_field_parent]['iterator']:
                #    expr = jp.parse(self.fields[new_field_parent]['iterator'])
                #    df[new_field_parent_name] = df[new_field_parent_name].apply(get_iterations_jsonpath, jsonpath=expr)
                #    df[new_field_parent_name + '.#'] = df[new_field_parent_name].apply(add_iteration_index)
                #    df = df.explode([new_field_parent_name, new_field_parent_name + '.#'])
                for sibling in siblings:
                    df = self.add_field_json(df, sibling)

                def dump_if_not_str(x):
                    if not isinstance(x, str):
                        x = json.dumps(x)
                    return x

                df[new_field_parent_name] = df[new_field_parent_name].apply(dump_if_not_str)
            # the parent is an iterable csv field
            if 'CSV' in new_field_parent_reference_formulation:
                df = self.add_siblings_csv(df, siblings, new_field_parent)
            if 'EXPRESSION' == new_field_parent_reference_formulation:
                for sibling in siblings:
                    df = self.add_field_expression(df, sibling, new_field_parent_name)
            return self.add_fields(df, fields_to_be_added)
        else:
            return df

    def add_field_json(self, df, field, nested_field=True):
        field_name = self.fields[field]['name']
        # if the field is an iterable, apply the iterator, else apply the expression
        if self.fields[field]['iterable']:
            field_jsonpath = jp.parse(self.fields[field]['iterator'])
        else:
            field_jsonpath = jp.parse(self.fields[field]['reference'])
        field_parent_name = '<it>'
        if nested_field:
            field_parent = self.fields[field]['parent']
            field_parent_name = self.fields[field_parent]['name']
        df[field_name] = df[field_parent_name].apply(get_iterations_jsonpath, jsonpath=field_jsonpath)
        df[field_name + '.#'] = df[field_name].apply(add_iteration_index)
        df = df.explode([field_name, field_name + '.#'])
        return df

    def add_field_csv(self, df, field):
        field_name = self.fields[field]['name']
        field_reference = self.fields[field]['reference']
        field_parent = self.fields[field]['parent']
        field_parent_name = self.fields[field_parent]['name']

        def read_csv_value(x, reference):
            df = pd.read_csv(StringIO(x), sep=',')
            return df[reference].tolist()

        df[field_name] = df[field_parent_name].apply(lambda x: read_csv_value(x, field_reference))
        return df

    def add_siblings_csv(self, df, siblings, parent):
        sibling_names = []
        for sibling in siblings:
            self.add_field_csv(df, sibling)
            sibling_names.append(self.fields[sibling]['name'])
        parent_name = self.fields[parent]['name']
        # split in lines and remove headers
        df[parent_name] = df[parent_name].apply(lambda x: x.splitlines()[1:])
        df[parent_name + '.#'] = df[parent_name].apply(add_iteration_index)
        df = df.explode([parent_name, parent_name + '.#', *sibling_names], ignore_index=True)
        for name in sibling_names:
            df[name + '.#'] = 0
        return df

    def add_field_expression(self, df, field, new_field_parent_name):
        field_reference_formulation = self.fields[field]['reference_formulation']
        if 'JSONPath' in field_reference_formulation:
            df = self.add_field_json(df, field)
        # CSV iterations + indexes will be made in when handling the child fields
        if 'CSV' in field_reference_formulation:
            df[self.fields[field]['name']] = df[new_field_parent_name]
        return df

    def make_view_from_json(self, source, iterator, logical_view):
        f = open(source)
        document = json.load(f)
        expr = jp.parse(iterator)
        data = [{'<it>': m.value} for m in expr.find(document)]
        df = pd.DataFrame(data)
        df['#'] = df.index
        view_fields = logical_view['fields']
        fields_to_be_added = []
        for field in view_fields:
            df = self.add_field_json(df, field, False)
            # field_name = self.fields[field]['name']
            # jsonpath = jp.parse(self.fields[field]['reference'])
            # df[field_name] = df['<it>'].apply(get_iterations_jsonpath, jsonpath=jsonpath)
            # df[field_name + '.#'] = df[field_name].apply(add_iteration_index)
            # df = df.explode([field_name, field_name + '.#'])
            if self.fields[field]['children']:
                fields_to_be_added.append(self.fields[field]['children'])
        df = self.add_fields(df, fields_to_be_added)
        df = df.drop('<it>', axis=1)
        return df

    def get_info_from_siblings(self, siblings, nested=False):
        fields_to_be_added = []
        converted_fields = {}
        if nested:
            parent = self.fields[siblings[0]]['parent']
            for sibling in siblings:
                self.fields[sibling]['name'] = self.fields[parent]['name'] + '.' + self.fields[sibling]['name']
        for sibling in siblings:
            if self.fields[sibling]['iterable']:
                converted_fields[self.fields[sibling]['iterator']] = self.fields[sibling]['name']
            else:
                converted_fields[self.fields[sibling]['reference']] = self.fields[sibling]['name']
            if self.fields[sibling]['children']:
                fields_to_be_added.append(self.fields[sibling]['children'])
        return fields_to_be_added, converted_fields

    def make_df_from_csv(self, source, converted_fields):
        types = defaultdict(lambda: str)
        df = pd.read_csv(source, sep=',', usecols=list(converted_fields.keys()), dtype=types)
        df.rename(columns=converted_fields, inplace=True)
        df['#'] = df.index
        for converted_field_name in converted_fields.values():
            # for csv: always single value so index is 0
            df[converted_field_name + '.#'] = 0
        return df

    def make_view_from_csv(self, source, logical_view):
        siblings = logical_view['fields']
        fields_to_be_added, converted_fields = self.get_info_from_siblings(siblings)
        df = self.make_df_from_csv(source, converted_fields)
        df = self.add_fields(df, list(fields_to_be_added))
        return df

    def execute(self) -> None:
        """Convert the mapping file and materialize the views

        """
        self.read_mapping()

        for logical_view in self.logical_views.values():
            if logical_view['id'] not in self.materialized_logical_views:
                self.materialize_logical_view(logical_view)

        for materialized_logical_view in self.materialized_logical_views:
            self.g.remove((materialized_logical_view, None, None))
            if self.old_rml:
                self.g.add((materialized_logical_view, RDF['type'], RML['LogicalSource']))
                self.g.add((materialized_logical_view, RML['referenceFormulation'], QL['CSV']))
                self.g.add(
                    (materialized_logical_view, RML['source'],
                     Literal(self.materialized_logical_views[materialized_logical_view])))
                ## no solution yet implemented for handling null values for CSV in old RML
            else:
                self.g.add((materialized_logical_view, RDF['type'], RML2['LogicalSource']))
                self.g.add((materialized_logical_view, RML2['referenceFormulation'], RML2['CSV']))
                source_node = BNode()
                self.g.add((materialized_logical_view, RML2['source'], source_node))
                self.g.add((source_node, RDF['type'], RML2['Source']))
                self.g.add((source_node, RDF['type'], RML2['RelativePathSource']))
                self.g.add((source_node, RML2['root'], RML2['MappingDirectory']))
                self.g.add(
                    (source_node, RML2['path'], Literal(self.materialized_logical_views[materialized_logical_view])))
                # acc to RML-IO spec "" is not automatically a null value for CSV
                self.g.add((source_node, RML2['null'], Literal("")))
        # remove view related triples
        for field in self.fields:
            self.g.remove((field, None, None))
        for join in self.joins:
            for join_condition in self.joins[join]['join_conditions']:
                self.g.remove((join_condition, None, None))
            self.g.remove((join, None, None))
        self.g.remove((None, RML2['field'], None))

        # write new mapping file
        converted_mapping = os.path.join(self.output_dir, 'mapping_without_views.ttl')
        if self.old_rml:
            converted_mapping = os.path.join(self.output_dir, 'mapping_without_views_old_rml.ttl')
        self.g.serialize(destination=converted_mapping, encoding='utf-8')
        print('done')


VERSION = '0.0.0'
EXIT_CODE_SUCCESS = 0
EXIT_CODE_UNKNOWN_COMMAND = -1
EXIT_CODE_NO_MAPPING = -2

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copyright by (c) '
                                                 'Els de Vleeschauwer '
                                                 '(2024), '
                                                 'available under the MIT '
                                                 'license',
                                     epilog='Please cite our paper if you '
                                            'make use of this tool')
    parser.add_argument('--version', action='version',
                        version=f'{parser.prog} {VERSION}')
    parser.add_argument('--mapping', dest='mapping',
                        help='The mapping file that needs to be converted ',
                        type=str)
    parser.add_argument('--output_dir', dest='output_dir', default='./',
                        help='Directory to which the output is saved, '
                             'default is "./"',
                        type=str)
    parser.add_argument('--old_rml', dest='old_rml', action='store_true',
                        help='Enables the use of old RML namespaces and vocabulary in the resulting mapping file'
                        )
    parser.add_argument('--optimize', dest='optimize', action='store_true',
                        help='Enables the optimization of the materialized logical view based on the triples maps'
                        )
    parser.add_argument('--no_ref_object_map', dest='no_ref_object_map', action='store_true',
                        help='Enables the replacement of referencing object maps by logical views'
                        )
    args = parser.parse_args()

    if not args.mapping:
        print(f'No mapping file provided. Provide mapping file after option "--mapping".', file=sys.stderr)
        sys.exit(EXIT_CODE_NO_MAPPING)
    else:
        convertor = ViewToCsvConvertor(args.mapping, args.output_dir, args.old_rml, args.optimize,
                                       args.no_ref_object_map)
        convertor.execute()
        sys.exit(EXIT_CODE_SUCCESS)
