# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

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
from flask import Flask, request
import sys
import constants.FIPAACLPerformatives as performatives
from AgentUtil.ACLMessages import build_message, get_message_properties
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.OntoNamespaces import ACL
from AgentUtil.Agent import Agent
import requests

import logging
logging.basicConfig(level=logging.DEBUG)

import random, constants.OntologyConstants as OntologyConstants
from orderRequest import  OrderRequest
from rdflib.term import Literal


# Configuration stuff
hostname = socket.gethostname()
port = 9010

agn = Namespace(OntologyConstants.ONTOLOGY_URI)

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

BuyerAgent = Agent('BuyerAgent',
                       agn.BuyerAgent,
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


@app.route("/")
def welcome():
    return "BuyerAgent"

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    global dsgraph
    global mss_cnt

    message = request.args['content']
    graph_message = Graph()
    graph_message.parse(data=message)
    message_properties = get_message_properties(graph_message)

    not_understood_message = lambda : build_message(
            Graph(),
            performatives.NOT_UNDERSTOOD,
            sender=BuyerAgent.uri,
            msgcnt=get_new_msg_count()
        ).serialize(format='xml')

    if message_properties is None:
        return not_understood_message()

    content = message_properties['content']
    action = graph_message.value(
        subject=content,
        predicate=RDF.type
    )

    if action != OntologyConstants.ACTION_SEARCH_PRODUCTS:
        not_understood_message()

    query_graph = graph_message.objects(content, OntologyConstants.QUERY)
    query_dict = {}
    for query in query_graph:
        if graph_message.value(subject=query, predicate=RDF.type) == OntologyConstants.QUERY_BRAND:
            query_dict['brand'] = graph_message.value(
                subject=query,
                predicate=OntologyConstants.QUERY_BRAND
            )
        if graph_message.value(subject=query, predicate=RDF.type) == OntologyConstants.QUERY_SEARCH_TEXT:
            query_dict['search_text'] = graph_message.value(
                subject=query,
                predicate=OntologyConstants.QUERY_SEARCH_TEXT
            )
        if graph_message.value(subject=query, predicate=RDF.type) == OntologyConstants.QUERY_MIN_PRICE:
            query_dict['min_price'] = graph_message.value(
                subject=query,
                predicate=OntologyConstants.QUERY_MIN_PRICE
            )
        if graph_message.value(subject=query, predicate=RDF.type) == OntologyConstants.QUERY_MAX_PRICE:
            query_dict['max_price'] = graph_message.value(
                subject=query,
                predicate=OntologyConstants.QUERY_MAX_PRICE
            )

    return search_graph_products(**query_dict).serialize(format='xml')


def search_graph_products(brand='(.*)', search_text='(.*)', min_price=0, max_price=sys.float_info.max):
    all_products = Graph()
    all_products.parse('./rdf/database_products.rdf')

    sparql_query = Template('''
        SELECT DISTINCT ?product ?id ?name ?description ?weight_grams ?category ?price_eurocents ?brand
        WHERE {
            ?product rdf:type ?type_prod .
            ?product ns:product_id ?id .
            ?product ns:product_name ?name .
            ?product ns:product_description ?description .
            ?product ns:weight_grams ?weight_grams .
            ?product ns:category ?category .
            ?product ns:price_eurocents ?price_eurocents .
            ?product ns:brand ?brand .
            FILTER (
                ?price_eurocents > $min_price && 
                ?price_eurocents < $max_price &&
                (regex(str(?name), '$search_text', 'i') || regex(str(?description), '$search_text', 'i') ) &&
                regex(str(?brand), '$brand', 'i')
            )
        }
    ''').substitute(dict(
            min_price=min_price,
            max_price=max_price,
            brand=brand,
            search_text=search_text
        )
    )

    return all_products.query(
        sparql_query,
        initNs=dict(
            foaf=FOAF,
            rdf=RDF,
            ns=agn,
        )
    )

def get_new_msg_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


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

    url ="http://" + hostname + ":" + "9012"+"/comm"

    #    flights_url = disIP.flights_IP + str(Constants.PORT_AFlights) + "/comm"

    messageDataGo = OrderRequest(random.randint(1, 2000), idProd)
    gra = messageDataGo.to_graph()

    dataContent = build_message(gra, Literal(performatives.REQUEST), Literal(OntologyConstants.SEND_BUY_ORDER)).serialize(
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


