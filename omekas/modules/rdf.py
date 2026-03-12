# RDFlib stuff
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, XSD, RDFS, SKOS

# list of useful namespaces
WDT = Namespace(
    "http://www.wikidata.org/prop/direct/"
)  # namespace for Wikidata property
WD = Namespace("http://www.wikidata.org/entity/")
SCHEMA = Namespace("http://schema.org/")
DCELEM = Namespace("http://purl.org/dc/elements/1.1/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
CIDOM_CRM = Namespace("http://cidoc-crm.org/cidoc-crm/7.1.3/")
BF = Namespace("")
