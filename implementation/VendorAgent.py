# coding=utf-8
from __future__ import print_function
from multiprocessing import Process, Queue
import socket

from rdflib import Namespace, Graph
from flask import Flask, request
import uuid

import constants.FIPAACLPerformatives as performatives
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.OntoNamespaces import ACL
from AgentUtil.Agent import Agent
import requests
from rdflib import RDF
from rdflib.namespace import FOAF
from AgentUtil.ACLMessages import build_message, get_message_properties


import logging
logging.basicConfig(level=logging.DEBUG)

import random, constants.OntologyConstants as OntologyConstants
from orderRequest import  OrderRequest
from pedidoRequest import  PedidoRequest
from rdflib.term import Literal


# Configuration stuff
hostname = socket.gethostname()
port = 9012

agn = Namespace(OntologyConstants.ONTOLOGY_URI)

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

ns = Namespace('ONTOLOGIA_ECSDI/')
direccions = ["Barcelona", "Valencia", "Madrid", "Zaragoza", "Sevilla", "Tarragona", "Girona", "Lleida", "Castelldefels", "Na macaret"]


@app.route('/comm', methods=['GET', 'POST'])
def comunicacion():
    """
    Entrypoint de comunicacion
    """

    message = request.args['content']
    graph_message = Graph()
    graph_message.parse(data=message)
    message_properties = get_message_properties(graph_message)

    not_understood_message = lambda: build_message(
        Graph(),
        performatives.NOT_UNDERSTOOD,
        sender=VendorAgent.uri,
        msgcnt=get_new_msg_count()
    ).serialize(format='xml')

    if message_properties is None:
        return not_understood_message()

    content = message_properties['content']
    action = graph_message.value(
        subject=content,
        predicate=RDF.type
    )

    if action == OntologyConstants.ACTION_SEND_DEV:
        s = ""
        # aqui devolucion
        ran = random.randint(0, 9)
        if ran > 6:
            return "devolución denegada por la tienda"
        return "devolución aceptada"

    if action == OntologyConstants.ACTION_CREATE_ORDER:
        return create_order(graph_message)

    else:
        return not_understood_message()


def create_order(graph_message):
    '''
    url = "http://" + hostname + ":" + "9011" + "/comm"

        print("creem messageDataGo Pedido")
        #uuid = identificador del pedido,
        messageDataGo = PedidoRequest(order.uuid, [order.product_id, '345'], "peso", random.randint(1, 9999),
                                      direccions[random.randint(0, 9)])

        print("Llegim graph orders")
        all_orders = Graph()
        all_orders.parse('./rdf/database_orders.rdf')
        print("Afegim order")
        add_order(all_orders, messageDataGo.uuid, messageDataGo.product_ids, messageDataGo.uuid,
                  messageDataGo.peso, messageDataGo.cp_code, messageDataGo.direction)
        print("Sobreescrivim base de dades")
        all_orders.serialize('./rdf/database_orders.rdf')

        print("creem messageDataGo graph")
        gra = messageDataGo.to_graph()
        #gra = order.to_graph()
        print("creem la request")
        print(gra.serialize(format='xml'))

        dataContent = build_message(gra, Literal(performatives.REQUEST),
                                    Literal(OntologyConstants.SEND_PEDIDO)).serialize(format='xml')


        print("fem request")
        resp = requests.post(url, data=dataContent)
        return "asdf"
    :param graph_message:
    :return:
    '''
    return 'lol'

def add_order(g, order_id, product_ids, uuid, peso, cp_code, direction):
    namespace = Namespace(OntologyConstants.ONTOLOGY_URI)
    order = namespace.__getattr__('#RequestOrder#' + str(order_id))
    g.add((order, RDF.type, Literal('ONTOLOGIA_ECSDI/order')))
    g.add((order, namespace.uuid, Literal(uuid)))
    g.add((order, namespace.cp_code, Literal(cp_code)))
    g.add((order, namespace.direction, Literal(direction)))
    g.add((order, namespace.weight_grams, Literal(peso)))
    for product_id in product_ids:
        g.add((order, namespace.product_id, Literal(product_id)))


def get_new_msg_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt

def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """
    VendorAgent.register_agent(DirectoryAgent)
    pass

if __name__ == '__main__':
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    app.run(host=hostname, port=port, debug=True)

    ab1.join()