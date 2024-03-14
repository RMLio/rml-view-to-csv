views = """
prefix rml2: <http://w3id.org/rml/> 
SELECT DISTINCT *
WHERE {
    ?LogicalView a rml2:LogicalView .
    ?LogicalView rml2:onLogicalSource ?LogicalSource .
    ?LogicalView rml2:field ?Field .
    OPTIONAL {?LogicalView rml2:leftJoin|rml2:innerJoin ?Join .}
}"""

# get logical sources (can also be a logical view!)
sources = """
prefix rml2: <http://w3id.org/rml/> 
prefix rml: <http://semweb.mmlab.be/ns/rml#> 
SELECT DISTINCT *
WHERE {
    ?Parent rml2:onLogicalSource ?LogicalSource .
    OPTIONAL { ?LogicalSource rml2:source|rml:source  ?Source .}
    OPTIONAL { ?LogicalSource rml2:referenceFormulation|rml:referenceFormulation ?ReferenceFormulation .}
    OPTIONAL { ?LogicalSource rml2:iterator|rml:iterator ?Iterator } .
}"""

fields = """
prefix rml2: <http://w3id.org/rml/> 
SELECT DISTINCT *
WHERE {
    ?Parent rml2:field ?Field .
    ?Field rml2:fieldName ?Name .
    OPTIONAL {?Field rml2:constant ?Constant .}
    OPTIONAL {?Field rml2:reference ?Reference .}
    OPTIONAL {?Field rml2:template ?Template .}
    OPTIONAL {?Field rml2:field ?Child .}
    OPTIONAL {?Field rml2:referenceFormulation ?ReferenceFormulation .}
}"""

left_joins = """
prefix rml2: <http://w3id.org/rml/> 
SELECT DISTINCT *
WHERE {
    ?ChildLogicalView rml2:leftJoin ?Join .
    ?Join rml2:parentLogicalView ?ParentLogicalView .
    ?Join rml2:field ?Field .
    ?Join rml2:joinCondition ?JoinCondition .
    #TODO add more complex join conditions with parentMap, childMap
    ?JoinCondition rml2:parent ?Parent .
    ?JoinCondition rml2:child ?Child .
}"""

inner_joins = """
prefix rml2: <http://w3id.org/rml/> 
SELECT DISTINCT *
WHERE {
    ?ChildLogicalView rml2:innerJoin ?Join .
    ?Join rml2:parentLogicalView ?ParentLogicalView .
    ?Join rml2:field ?Field .
    ?Join rml2:joinCondition ?JoinCondition .
    #TODO add more complex join conditions with parentMap, childMap
    ?JoinCondition rml2:parent ?Parent .
    ?JoinCondition rml2:child ?Child .
}"""

# including also old rml
def all_references_per_lv(lv):
    return f"""
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    PREFIX rml2: <http://w3id.org/rml/>
    SELECT DISTINCT ?Reference WHERE {{
    {{
    ?TriplesMap rml:logicalSource|rml2:logicalSource  <{lv}> .   
    ?TriplesMap (<http://example.com>|!<http://example.com>)* ?o .
    ?o rml:reference|rr:child|rml2:reference|rml2:child ?Reference.
    }}
    UNION
    {{
    ?Join rml2:parentLogicalView <{lv}> .   
    ?Join (<http://example.com>|!<http://example.com>)* ?o .
    ?o rml:reference|rr:child|rml2:reference|rml2:parent ?Reference.
    }}
}}"""


# including also old rml
def all_templates_per_lv(lv):
    return f"""
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    PREFIX rml2: <http://w3id.org/rml/>
    SELECT DISTINCT ?Template WHERE {{
    {{
    ?TriplesMap rml:logicalSource|rml2:logicalSource <{lv}> .
    ?TriplesMap (<http://example.com>|!<http://example.com>)* ?o .
    ?o rr:template|rml2:template ?Template.
    }}
    UNION
    {{
    ?Join rml2:parentLogicalView <{lv}> .   
    ?Join (<http://example.com>|!<http://example.com>)* ?o .
    ?o rr:template|rml2:template ?Template.
    }}
    
    
}}"""

# including also old rml
def all_blank_nodes_without_template_or_reference_per_lv(lv):
    return f"""
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    PREFIX rml2: <http://w3id.org/rml/> 
    SELECT DISTINCT ?BlankNode WHERE {{
    ?TriplesMap rml2:logicalSource|rml:logicalSource <{lv}> .
    ?TriplesMap (<http://example.com>|!<http://example.com>)* ?BlankNode .
    {{
    {{?BlankNode rr:termType rr:BlankNode.}}
    UNION
    {{?BlankNode rml2:termType rml2:BlankNode.}}
    }}
    filter NOT EXISTS {{
       ?BlankNode (<http://example.com>|!<http://example.com>)* ?o .
       ?o rr:template|rml:reference ?o2.
       }}
    filter NOT EXISTS {{
       ?BlankNode (<http://example.com>|!<http://example.com>)* ?o .
       ?o rml2:template|rml2:reference ?o2.
       }}
    }}    
"""


# queries using in ref_object_map_to_view.py, old rml voc only, TODO add new rml voc
joins_in_TM = """
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT * WHERE {
    ?Tm rml:logicalSource ?ChildLogicalSource.
    ?Tm rr:subjectMap ?Sm.
    ?Sm rr:template ?ChildSubjectTemplate.
    ?Tm rr:predicateObjectMap ?Pom.
    ?Pom rr:predicateMap ?Pm.
    ?Pom rr:objectMap ?Om.
    ?Om rr:parentTriplesMap ?ParentTriplesMap.
    ?Om rr:joinCondition ?JoinCondition.
    ?JoinCondition rr:child ?Child.
    ?JoinCondition rr:parent ?Parent.
    ?ParentTriplesMap rr:subjectMap ?ParentSubjectMap.
    ?ParentSubjectMap rr:template ?ParentSubjectTemplate.
    ?ParentTriplesMap rml:logicalSource ?ParentLogicalSource.
    ?ChildLogicalSource rml:source ?ChildSource .
    ?ChildLogicalSource rml:referenceFormulation ?ChildReferenceFormulation .
    OPTIONAL { ?ChildLogicalSource rml:iterator ?Iterator } .
    ?ParentLogicalSource rml:source ?ParentSource .
    ?ParentLogicalSource rml:referenceFormulation ?ParentReferenceFormulation .
    OPTIONAL { ?ParentLogicalSource rml:iterator ?Iterator } .
}"""

logical_source_properties = """
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    PREFIX rml2: <http://w3id.org/rml/>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?LogicalSource ?Object WHERE {    
        ?s rml:logicalSource ?LogicalSource . 
        ?LogicalSource (<http://ex.com>|!<http://ex.com>)* ?Object .
        FILTER NOT EXISTS {
        ?Object ?p ?o2.
        }
    }
"""

def all_linked_references(term):
    return f"""
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    SELECT DISTINCT ?Reference WHERE {{
    <{term}> (<http://example.com>|!<http://example.com>)* ?o .
    ?o rml:reference ?Reference.
    }}"""

def all_linked_templates(term):
    return f"""
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX rml: <http://semweb.mmlab.be/ns/rml#>
    SELECT DISTINCT ?Template WHERE {{
    <{term}> (<http://example.com>|!<http://example.com>)* ?o .
    ?o rr:Template ?Template.
    }}"""