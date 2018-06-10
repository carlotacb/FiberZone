# coding=utf-8
from imaplib import Literal
import requests
from flask import Flask, request, Response
from rdflib import Graph

import constants.FIPAACLPerformatives as FIPAACLPerformatives
import random, constants.OntologyConstants as OntologyConstants
from AgentUtil import ACLMessages
from AgentUtil.ACLMessages import build_message
from orderRequest import OrderRequest
from pedidoRequest import PedidoRequest
import socket
import time

import logging
logging.basicConfig(level=logging.DEBUG)


# Configuration stuff
hostname = socket.gethostname()
port = 9012
app = Flask(__name__)
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
    print("creem la request")
    #dataContent = build_message(gra, Literal(FIPAACLPerformatives.REQUEST), Literal(OntologyConstants.SEND_PEDIDO)).serialize(format='xml')

    print("fem request")
    #resp = requests.post(url, data=dataContent)
    return "asdf"


if __name__ == '__main__':
    app.run(host=hostname, port=port, debug=True)