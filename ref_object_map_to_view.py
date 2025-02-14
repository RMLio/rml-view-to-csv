import queries
from rdflib import Literal
from rdflib.namespace import RDF
from namespaces import *
import re


def extract_references_from_template(template):
    return [parent_subject_reference[1:-1] for parent_subject_reference in re.findall(r'\{.*?\}', template)]


def rename_same_logical_source(g):
    logical_source_properties_results = g.query(queries.logical_source_properties)
    logical_sources_dict = {}
    properties_dict = {}
    for row in logical_source_properties_results:
        logical_sources_dict[row.LogicalSource] = set()
    for row in logical_source_properties_results:
        logical_sources_dict[row.LogicalSource].add(row.Object)
    for k, v in logical_sources_dict.items():
        frozen_v = frozenset(v)
        if not frozen_v in properties_dict:
            properties_dict[frozen_v] = k
        else:
            for s, p, o in g.triples((None, RML['logicalSource'], k)):
                g.add((s, RML['logicalSource'], properties_dict[frozen_v]))
                g.remove((s, RML['logicalSource'], k))


def eliminate_self_joins(g):
    for s, p, o in g.triples((None, RR['parentTriplesMap'], None)):
        parentTriplesMap = o
        childObjectMap = s
        parentLogicalSource = g.value(parentTriplesMap, RML['logicalSource'])
        childPredicateObjectMap = g.value(predicate=RR['objectMap'], object=childObjectMap, any=False)
        childTriplesMap = g.value(predicate=RR['predicateObjectMap'], object=childPredicateObjectMap, any=False)
        childLogicalSource = g.value(childTriplesMap, RML['logicalSource'])
        if childLogicalSource == parentLogicalSource:
            joinConditions = g.objects(childObjectMap, RR['joinCondition'])
            parentSubjectMap = g.value(parentTriplesMap, RR['subjectMap'], any=False)
            safeSelfJoinElimination = True

            if parentSubjectMap and joinConditions:
                joinReferences = []
                for joinCondition in joinConditions:
                    parent = g.value(joinCondition, RR['parent']).value
                    child = g.value(joinCondition, RR['child']).value
                    if child == parent:
                        joinReferences.append(child);
                    else:
                        safeSelfJoinElimination = False

                if safeSelfJoinElimination:
                    safeTerms = has_safe_references(parentSubjectMap, joinReferences, g)
                    if not safeTerms:
                        childSubjectMap = g.value(parentTriplesMap, RR['subjectMap'], any=False)
                        if childSubjectMap:
                            safeTerms = has_safe_references(childSubjectMap, joinReferences, g)
                        else:
                            safeTerms = True

                    if safeTerms:
                        childPredicateMap = g.value(childPredicateObjectMap, RR['predicateMap'], any=False)
                        if childPredicateMap:
                            safeTerms = has_safe_references(childPredicateMap, joinReferences, g)
                    if not safeTerms:
                        safeSelfJoinElimination = False
            if safeSelfJoinElimination:
                termTypeAdded = False
                parentSubjectMapQuads = g.triples((parentSubjectMap, None, None))
                for parentSubjectMapQuad in parentSubjectMapQuads:
                    predicate = parentSubjectMapQuad[1]
                    if predicate == FNML['functionValue'] or predicate == RR['termType'] or \
                            predicate == RML['reference'] or predicate == RR['template'] or \
                            predicate == RR['constant']:
                        g.add((childObjectMap, predicate, parentSubjectMapQuad[2]))
                    if predicate == RR['termType']:
                        termTypeAdded = True
                g.remove((childObjectMap, RR['parentTriplesMap'], parentTriplesMap))
                if not termTypeAdded:
                    g.add((childObjectMap, RR['termType'], RR['IRI']))


def has_safe_references(term, join_references, g):
    is_safe = True
    term_references = get_all_linked_references(term, g)
    for parent_reference in term_references:
        if not parent_reference in join_references:
            is_safe = False
    return is_safe


def get_all_linked_references(term, g):
    references = set()
    linked_references_results = g.query(queries.all_linked_references(term))
    for row in linked_references_results:
        references.add(row.Reference.value)
    linked_templates_results = g.query(queries.all_linked_templates(term))
    for row in linked_templates_results:
        extracted_references = extract_references_from_template(row.Template)
        for reference in extracted_references:
            references.add(reference)
    return references


def ref_object_map_to_view(g):
    rename_same_logical_source(g)
    g.serialize(destination='./renamed.ttl', encoding='utf-8')
    eliminate_self_joins(g)
    g.serialize(destination='./no-self-join.ttl', encoding='utf-8')
    joins_in_TM = g.query(queries.joins_in_TM)
    len(joins_in_TM)  # without this it seems as if the result are processed before they are complete
    counter = 0
    for row in joins_in_TM:
        # child source
        tm_id = EX['tm_' + str(counter)]
        child_view_id = EX['child_view_' + str(counter)]
        g.add((tm_id, RDF['type'], RR['TriplesMap']))
        g.add((tm_id, RML['logicalSource'], child_view_id))
        g.add((child_view_id, RDF['type'], RML2['LogicalView']))
        g.add((child_view_id, RML2['viewOn'], row.ChildLogicalSource))
        child_sm_id = EX['child_sm_' + str(counter)]
        g.add((tm_id, RR['subjectMap'], child_sm_id))
        g.add((child_sm_id, RR['template'], row.ChildSubjectTemplate))
        child_pom_id = EX['child_pom_' + str(counter)]
        g.add((tm_id, RR['predicateObjectMap'], child_pom_id))
        g.add((child_pom_id, RR['predicateMap'], row.Pm))
        child_om_id = EX['child_om_' + str(counter)]
        g.add((child_pom_id, RR['objectMap'], child_om_id))
        new_template = row.ParentSubjectTemplate.value.replace('}', '_from_parent}')
        g.add((child_om_id, RR['template'], Literal(new_template)))
        g.add((row.Om, RR['termType'], RR['IRI']))

        g.remove((row.Tm, None, row.Pom))
        g.remove((row.Pom, None, None))

        parent_view_id = EX['parent_view_' + str(counter)]
        g.add((parent_view_id, RDF['type'], RML2['LogicalView']))
        g.add((parent_view_id, RML2['viewOn'], row.ParentLogicalSource))

        # join
        join_id = EX[child_view_id + '_' + parent_view_id + '_join']
        g.add((child_view_id, RML2['leftJoin'], join_id))
        g.add((join_id, RDF['type'], RML2['Join']))
        g.add((join_id, RML2['parentLogicalView'], parent_view_id))
        jc_id = EX['jc_' + row.Parent.value + '_' + row.Child.value]
        g.add((join_id, RML2['joinCondition'], jc_id))
        g.add((jc_id, RML2['parent'], row.Parent))
        g.add((jc_id, RML2['child'], row.Child))

        field_id = EX['field_' + row.Child]
        g.add((child_view_id, RML2['field'], field_id))
        g.add((field_id, RML2['reference'], row.Child))
        g.add((field_id, RML2['fieldName'], row.Child))

        field_id = EX['field_' + row.Parent]
        g.add((parent_view_id, RML2['field'], field_id))
        g.add((field_id, RML2['reference'], row.Parent))
        g.add((field_id, RML2['fieldName'], row.Parent))

        parent_references = extract_references_from_template(row.ParentSubjectTemplate)
        for parent_reference in parent_references:
            field_id = EX['field_' + parent_reference]
            g.add((parent_view_id, RML2['field'], field_id))
            g.add((field_id, RML2['reference'], Literal(parent_reference)))
            g.add((field_id, RML2['fieldName'], Literal(parent_reference)))

            field_id2 = EX['join_field_' + parent_reference]
            g.add((join_id, RML2['field'], field_id2))
            g.add((field_id2, RML2['reference'], Literal(parent_reference)))
            g.add((field_id2, RML2['fieldName'], Literal(parent_reference + '_from_parent')))

        child_references = extract_references_from_template(row.ChildSubjectTemplate)
        for child_reference in child_references:
            field_id = EX['field_' + child_reference]
            g.add((child_view_id, RML2['field'], field_id))
            g.add((field_id, RML2['reference'], Literal(child_reference)))
            g.add((field_id, RML2['fieldName'], Literal(child_reference)))

        counter += 1
