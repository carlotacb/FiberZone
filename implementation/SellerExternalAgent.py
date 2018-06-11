# -*- coding: utf-8 -*-
"""

Esqueleto de agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente

Asume que el agente de registro esta en el puerto 9000

"""
from __future__ import print_function
from multiprocessing import Process, Queue
import socket
from string import Template

from rdflib import Namespace, Graph, RDF
from rdflib.namespace import FOAF
import uuid
from flask import Flask, request, render_template
import sys
import constants.FIPAACLPerformatives as performatives
from AgentUtil.ACLMessages import build_message, send_message
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.OntoNamespaces import ACL
from AgentUtil.Agent import Agent
import requests

import logging
logging.basicConfig(level=logging.DEBUG)

import constants.OntologyConstants as OntologyConstants
from orderRequest import  OrderRequest
from rdflib.term import Literal


# Configuration stuff
hostname = socket.gethostname()
port = 9015

agn = Namespace(OntologyConstants.ONTOLOGY_URI)

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

ExternalSellerAgent = Agent('SellerExternalAgent',
                       agn.SellerExternalAgent,
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
app = Flask(__name__, template_folder='./templates')


def add_product_to_graph(g, product_id, product_name, product_description, weight_grams, brand, price, category, seller):
    g.add((agn[product_id], agn.product_name, Literal(product_name)))
    g.add((agn[product_id], agn.product_id, Literal(product_id)))
    g.add((agn[product_id], agn.product_description, Literal(product_description)))
    g.add((agn[product_id], agn.weight_grams, Literal(weight_grams)))
    g.add((agn[product_id], agn.brand, Literal(brand)))
    g.add((agn[product_id], agn.price_eurocents, Literal(price)))
    g.add((agn[product_id], agn.category, Literal(category)))
    g.add((agn[product_id], agn.seller, Literal(seller)))

@app.route("/", methods=['GET', 'POST'])
def welcome():
    if request.method == 'GET':
        return render_template('external_seller.html')

    message = Graph()

    product_id = uuid.uuid4()
    add_product_to_graph(
        message,
        product_id,
        request.form['product_name'],
        request.form['product_description'],
        int(request.form['weight_grams']),
        request.form['brand'],
        int(int(request.form['price_euros']) / 100),
        request.form['category'],
        request.form['seller']
    )

    message.add((agn[product_id], RDF.type, Literal(OntologyConstants.ACTION_ADD_EXT)))

    vendor_agent = ExternalSellerAgent.find_agent(DirectoryAgent, agn.VendorAgent)

    msg = build_message(
        message,
        perf=Literal(performatives.REQUEST),
        sender=ExternalSellerAgent.uri,
        receiver=vendor_agent.uri,
        msgcnt=get_new_msg_count(),
        content=agn[product_id]
    )

    print("hey lets print")
    send_message(msg, vendor_agent.address)
    print("hey already printed")
    return render_template('external_seller.html')

def get_new_msg_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    return


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """

    ExternalSellerAgent.register_agent(DirectoryAgent)

    pass


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port, debug=True)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')


