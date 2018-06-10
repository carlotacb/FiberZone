# coding=utf-8
from __future__ import print_function
from multiprocessing import Process, Queue
import socket

from rdflib import Namespace, Graph
from flask import Flask, request

import constants.FIPAACLPerformatives as FIPAACLPerformatives
from AgentUtil.ACLMessages import build_message
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.OntoNamespaces import ACL
from AgentUtil.Agent import Agent
import requests

import logging
logging.basicConfig(level=logging.DEBUG)

import random, constants.OntologyConstants as OntologyConstants
from orderRequest import  OrderRequest
from pedidoRequest import  PedidoRequest
from rdflib.term import Literal

# Configuration stuff
hostname = socket.gethostname()
port = 9012

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

VendorAgent = Agent('VendorAgent',
                       agn.VendorAgent,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)


# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__)

import logging
logging.basicConfig(level=logging.INFO)
direccions = ["Barcelona", "Valencia", "Madrid", "Zaragoza", "Sevilla", "Tarragona", "Girona", "Lleida", "Castell de fels", "Na macaret"]

@app.route('/comm', methods=['GET', 'POST'])
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    print("here VendorAgent comunicacion")
    graph = Graph().parse(data=request.data)
    print("obtenim order request")
    order = OrderRequest.from_graph(graph)

    url = "http://" + hostname + ":" + "9011" + "/comm"

    print("creem messageDataGo Pedido")
    messageDataGo = PedidoRequest(order.uuid, order.product_id, "peso", random.randint(1, 9999),
                                  direccions[random.randint(0, 9)])
    print("creem messageDataGo graph")
    gra = messageDataGo.to_graph()
    #gra = order.to_graph()
    print("creem la request")
    print(gra.serialize(format='xml'))

    #dataContent = build_message(gra, Literal(FIPAACLPerformatives.REQUEST),
                                #Literal(OntologyConstants.SEND_BUY_ORDER)).serialize(format='xml')
    dataContent = build_message(gra, Literal(FIPAACLPerformatives.REQUEST), Literal(OntologyConstants.SEND_PEDIDO)).serialize(format='xml')

    print("fem request")
    resp = requests.post(url, data=dataContent)
    return "asdf"


if __name__ == '__main__':
    app.run(host=hostname, port=port, debug=True)