# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Esqueleto de agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente

Asume que el agente de registro esta en el puerto 9000

@author: javier
"""
from __future__ import print_function
from multiprocessing import Process, Queue
import socket

from rdflib import Namespace, Graph
from flask import Flask, request

import FIPAACLPerformatives
from AgentUtil.ACLMessages import build_message
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.OntoNamespaces import ACL
from AgentUtil.Agent import Agent
import requests

import logging
logging.basicConfig(level=logging.DEBUG)

import os
import bottlenose
from bs4 import BeautifulSoup

import random, OntologyConstants
from orderRequest import  OrderRequest
from rdflib.term import Literal

amazon = bottlenose.Amazon(
    os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'], os.environ['AWS_ASSOCIATE_TAG'], Region='ES',
    Parser=lambda text: BeautifulSoup(text, 'xml')
)

__author__ = 'javier'


# Configuration stuff
hostname = socket.gethostname()
port = 9010

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentePersonal = Agent('AgenteSimple',
                       agn.AgenteSimple,
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

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    global dsgraph
    global mss_cnt
    pass


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"



@app.route("/search")
def search():
    """
    Endpoint that returns search of query.
    :return: amazon_items
    """

    query = request.args['query']

    response = None
    try:
        response = amazon.ItemSearch(Keywords=query, SearchIndex="All")
        print(response)
    except Exception as e: print(e)

    return response.prettify()

#el grafo G tiene que contener toda la informacion
#necesaria para realizar el pedido
# por ejemplo, idPedido, idProducto, idPersona ...
@app.route("/order/<idProd>")
def newOrder(idProd):
    """
    Creates a new order with the idProd
    :return:
    """
    print("Im in order func")

    url ="http://127.0.0.1:" + "5000"+"/comm"

    #    flights_url = disIP.flights_IP + str(Constants.PORT_AFlights) + "/comm"

    messageDataGo = OrderRequest(random.randint(1, 2000), idProd)
    gra = messageDataGo.to_graph()

    dataContent = build_message(gra, Literal(FIPAACLPerformatives.REQUEST), Literal(OntologyConstants.SEND_BUY_ORDER)).serialize(
        format='xml')
    print("before send request ")
#gr = send_message( build_message(gmess, perf=ACL.request, sender=InfoAgent.uri, receiver=DirectoryAgent.uri, content=reg_obj, msgcnt=mss_cnt),
#DirectoryAgent.address)
    resp = requests.post(url, data=dataContent)

    print("im here, resp:")
    print(resp)
    print(resp.text)
    return resp.text



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
    pass


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')


