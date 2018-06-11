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
port = 9016

agn = Namespace(OntologyConstants.ONTOLOGY_URI)

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

ExternalUserAgent = Agent('ExternalUserAgent',
                       agn.ExternalUserAgent,
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


@app.route("/", methods=['GET', 'POST'])
def welcome():
    if request.method == 'GET':
        return render_template('search.html')

    message = Graph()
    msg_count = get_new_msg_count()
    search = agn['search_query_' + str(msg_count)]

    if request.form['brand']:
        message.add((search, agn[OntologyConstants.QUERY_BRAND], Literal(request.form['brand'])))

    if request.form['min_price']:
        message.add((search, agn[OntologyConstants.QUERY_MIN_PRICE], Literal(int(request.form['min_price']) * 100)))

    if request.form['max_price']:
        message.add((search, agn[OntologyConstants.QUERY_MAX_PRICE], Literal(int(request.form['max_price']) * 100)))

    if request.form['search_text']:
        message.add((search, agn[OntologyConstants.QUERY_SEARCH_TEXT], Literal(request.form['search_text'])))

    message.add((search, RDF.type, Literal(OntologyConstants.ACTION_SEARCH_PRODUCTS)))

    print('lol fuck')
    BuyerAgent = ExternalUserAgent.find_agent(DirectoryAgent, agn.BuyerAgent)
    print('you have agent or what')

    msg = build_message(
        message,
        perf=Literal(performatives.REQUEST),
        sender=ExternalUserAgent.uri,
        receiver=BuyerAgent.uri,
        msgcnt=msg_count,
        content=search
    )

    print("hey lets print")
    response = send_message(msg, BuyerAgent.address)

    products = []
    for item in response.subjects(RDF.type, agn.product):
        product = dict(
            product_name=str(response.value(subject=item, predicate=agn.product_name)),
            product_id=str(response.value(subject=item, predicate=agn.product_id)),
            brand=str(response.value(subject=item, predicate=agn.brand)),
            product_description=str(response.value(subject=item, predicate=agn.product_description)),
            price_euros=int(response.value(subject=item, predicate=agn.price_eurocents))/100,
            category=str(response.value(subject=item, predicate=agn.category)),
            image=str(response.value(subject=item, predicate=agn.image)),
        )
        products.append(product)

    print('products', products)

    return render_template('search_result.html', products=products)

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

    ExternalUserAgent.register_agent(DirectoryAgent)

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


