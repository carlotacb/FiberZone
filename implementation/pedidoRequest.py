from rdflib import Graph, Literal
from rdflib.namespace import Namespace, FOAF


class PedidoRequest:

    def __init__(self, uuid, product_id, peso, cp_code, direction):
        self.uuid = uuid
        self.product_id = product_id
        self.peso = peso
        self.cp_code = cp_code
        self.direction = direction

    def to_graph(self):
        print("Creant graf")
        graph = Graph()
        namespace = Namespace('ONTOLOGIA_ECSDI/')
        order = namespace.__getattr__('#RequestPedido#' + str(self.uuid))
        graph.add((order, FOAF.Uuid, Literal(self.uuid)))
        graph.add((order, FOAF.product_id, Literal(self.product_id)))
        graph.add((order, FOAF.peso, Literal(self.peso)))
        graph.add((order, FOAF.cp_code, Literal(self.cp_code)))
        graph.add((order, FOAF.direction, Literal(self.direction)))

        print("graf creat")
        return graph

    @classmethod
    def from_graph(cls, graph):
        query = """SELECT ?x ?uuid ?product_id ?peso ?cp_code ?direction
           WHERE {
                ?x ns1:Uuid ?uuid.
                ?x ns1:product_id ?product_id.
                ?x ns1:peso ?peso.
                ?x ns1:cp_code ?cp_code.
                ?x ns1:direction ?direction.
           }
        """
        qres = graph.query(query)
        search_res = []
        for f, uuid, product_id, peso, cp_code, direction in qres:
            """search_res.append(Order(
                uuid.toPython(),
                product_id.toPython(),
                peso.toPython(),
                cp_code.toPython(),
                direction.toPython(),

            ))"""
            return PedidoRequest(uuid.toPython(), product_id.toPython(), peso.toPython(), cp_code.toPython(), direction.toPython())
# return search_res