from rdflib.compare import to_isomorphic
from rdflib import Graph
import sys

def compare(graph_file, expected_graph_file):
    g1 = Graph().parse(graph_file)
    g2 = Graph().parse(expected_graph_file)
    iso1 = to_isomorphic(g1)
    iso2 = to_isomorphic(g2)
    return iso1 == iso2

print(compare(sys.argv[1], sys.argv[2]))


