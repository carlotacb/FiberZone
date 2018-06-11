# coding=utf-8
from imaplib import Literal
import requests
from flask import Flask, request, Response
from rdflib import Graph, Namespace, RDF
from multiprocessing import Process, Queue

import constants.FIPAACLPerformatives as FIPAACLPerformatives
import constants.OntologyConstants as OntologyConstants
from AgentUtil import ACLMessages
from orderRequest import OrderRequest
import socket
import time
from pedidoRequest import  PedidoRequest
from AgentUtil.Agent import Agent


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

agn = Namespace(OntologyConstants.ONTOLOGY_URI)

cola1 = Queue()


CLAgent = Agent('CLAgent',
                       agn.CLAgent,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)


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


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """

    CLAgent.register_agent(DirectoryAgent)

    pass

if __name__ == '__main__':
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    app.run(host=hostname, port=port, debug=True)