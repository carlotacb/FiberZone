# coding=utf-8
from imaplib import Literal
import requests
from flask import Flask, request, Response
from rdflib import Namespace, Graph, RDF
from rdflib.namespace import FOAF
from rdflib.term import Literal

import constants.FIPAACLPerformatives as FIPAACLPerformatives
import constants.OntologyConstants as OntologyConstants
from AgentUtil import ACLMessages
from orderRequest import OrderRequest
import socket
import time
from pedidoRequest import  PedidoRequest


# Configuration stuff
hostname = socket.gethostname()
port = 9011
Lote = [] #cada 5 se vacia el lote y se envia

precioBase = 10
precioFinal = 0
app = Flask(__name__)
mensajeFecha = "Recibirás el pedido en 2 dias a partir de:"
precioExtra1 = 0
precioExtra2 = 0

FOAF = Namespace('http://xmlns.com/foaf/0.1/')
agn = Namespace(OntologyConstants.ONTOLOGY_URI)


def update_state(uuid, state):
    print('id:', uuid, 'state:', state)
    all_orders = Graph()
    all_orders.parse('./rdf/database_orders.rdf')
    query_update = """DELETE { ?order ns1:state 'pending' }
    INSERT { ?order ns1:state '""" + state + """' }
    WHERE
    {
        ?order ns1:uuid '""" + uuid + """'
    }"""
    print(query_update)
    newOrder = all_orders.query(query_update,  initNs=dict(
            foaf=FOAF,
            rdf=RDF,
            ns1=agn,
        ))
    print(newOrder.serialize(format='xml'))
    return


update_state('7951dc00-ef96-4387-957d-cbc371af7230', 'updated')


@app.route('/comm', methods=['GET', 'POST'])
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    print("here CLAgent comunicacion")
    global precioBase
    global precioFinal
    global mensajeFecha
    global precioExtra1,precioExtra2
    ahora = mensajeFecha
    ahora += " "
    ahora += time.strftime("%c")

    graph = Graph().parse(data=request.data)
    pedido = PedidoRequest.from_graph(graph)

    #coger identificador y leer de la BD
    identificador = pedido.uuid
    print("Llegim graph orders")
    all_orders = Graph()
    all_orders.parse('./rdf/database_orders.rdf')
    query = """SELECT ?x ?uuid ?product_id ?peso ?cp_code ?direction
       WHERE {
            ?x ns1:Uuid ?uuid.
            ?x ns1:product_id ?product_id.
            ?x ns1:peso ?peso.
            ?x ns1:cp_code ?cp_code.
            ?x ns1:direction ?direction.
            FILTER( str(?uuid) = '""" + identificador + """' )
       }
    """
    newOrder = all_orders.query(query)
    print(newOrder.serialize(format='xml'))


    print( 'Its a plan request')
    order = OrderRequest.from_graph(graph)
    print('Plan graph obtained, lets construct response message')
   # print(order)
    #if order.peso > 10:
    peso = 11
    #oferta transportista 1
    url ="http://" + hostname + ":" + "9013"+"/calc"
    dataContent = {"peso":peso}
    resp = requests.post(url, data=dataContent)
    precioExtra1 += int(resp.text)
    print("precioExtra = ",precioExtra1)

    #oferta transportista 2
    url ="http://" + hostname + ":" + "9014"+"/calc"
    dataContent2 = {"size":len(Lote)}
    resp = requests.post(url, data=dataContent2)
    precioExtra2 += int(resp.text)
    print("precioExtra = ", precioExtra2)

    Lote.append(order.product_id)
    LoteFinal = Lote[:]
    if len(Lote) == 5 :
        #realizar envio
        #vaciar lote
        precioFinal = min(precioExtra2,precioExtra1)
        precioBase = 10
      #  LoteFinal[:] = Lote[:]
        Lote[:] = []
        LoteFinal.append(ahora)
        LoteFinal.append(precioFinal)
        precioExtra1 = precioExtra2 = 0
        print(ahora)
        print(LoteFinal)
        return str(LoteFinal)

    return len(Lote).__str__()
    return order.product_id


if __name__ == '__main__':
    app.run(host=hostname, port=port, debug=True)