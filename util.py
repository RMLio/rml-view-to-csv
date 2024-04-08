import jsonpath_ng as jp
import os
import json
import queries
import re

def get_fields_for_renaming(fields_to_be_renamed, fields):
    converted_fields = {}
    for field in fields_to_be_renamed:
        converted_fields[fields[field]['reference']] = fields[field]['name']
       # index only to be added to join if explicitely declared
       # converted_fields[fields[field]['reference']+ '.#'] = fields[field]['name'] + '.#'
    return converted_fields

def get_iterations_jsonpath(document, jsonpath):
    if isinstance(document, str):
        # this happens in case of switch of reference formulation
        document = json.loads(document)
    iterations = [m.value for m in jsonpath.find(document)]
    return iterations

def rename_parent_fields(dataframe, fieldnames_parent):
    for k, v in fieldnames_parent.items():
        # only duplicates get suffixes
        if k + '_parent' in dataframe:
            dataframe.rename(columns={k + '_parent': v}, inplace=True)
           # dataframe.rename(columns={k + '.#_parent': v + '.#'}, inplace=True)
        else:
            dataframe.rename(columns={k: v}, inplace=True)
           # dataframe.rename(columns={k + '.#': v + '.#'}, inplace=True)
    return dataframe

def resolve_path(path, is_dir=False):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    if is_dir and not os.path.exists(path):
        os.makedirs(path)
    return path

def get_all_references_per_view(graph, logical_view):
    references = []
    references_results = graph.query(queries.all_references_per_lv(logical_view))
    for row in references_results:
        references.append(row.Reference.value)
    templates_results = graph.query(queries.all_templates_per_lv(logical_view))
    for row in templates_results:
        extracted_references = re.findall('{(.+?)}', row.Template.value)
        for ref in extracted_references:
            references.append(ref)
    return references

def safe_removal_of_duplicates(graph, logical_view):
    results = graph.query(queries.all_blank_nodes_without_template_or_reference_per_lv(logical_view))
    return len(results) == 0




def add_iteration_index(value):
    if isinstance(value, list):
        return list(range(len(value)))
    else:
        return 0

