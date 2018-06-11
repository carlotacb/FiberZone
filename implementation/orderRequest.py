from rdflib import Graph, Literal
from rdflib.namespace import Namespace, FOAF


class OrderRequest:

    def __init__(self, uuid, product_id):
        self.uuid = uuid
        self.product_id = product_id


    def to_graph(self):
        print("Creant graf")
        graph = Graph()
        namespace = Namespace('ONTOLOGIA_ECSDI/')
        order = namespace.__getattr__('#RequestOrder#' + str(self.uuid))
        graph.add((order, FOAF.uuid, Literal(self.uuid)))
        graph.add((order, FOAF.product_id, Literal(self.product_id)))
        print("graf creat")
        return graph

    @classmethod
    def from_graph(cls, graph):
        query = """SELECT ?x ?uuid ?product_id 
           WHERE {
                ?x ns1:Uuid ?uuid.
                ?x ns1:product_id ?product_id.
           }
        """
        qres = graph.query(query)
        search_res = []
        for f, uuid, product_id in qres:
            """search_res.append(Order(
                uuid.toPython(),
                product_id.toPython(),
               
            ))"""
            return OrderRequest(uuid.toPython(), product_id.toPython())
#return search_res