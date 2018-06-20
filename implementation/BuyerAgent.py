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
from flask import Flask, request
import sys
import constants.FIPAACLPerformatives as performatives
from AgentUtil.ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.OntoNamespaces import ACL
from AgentUtil.Agent import Agent
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
import constants.OntologyConstants as OntologyConstants
from orderRequest import OrderRequest
from rdflib.term import Literal
import logging

logging.basicConfig(level=logging.DEBUG)

# Configuration stuff
hostname = '0.0.0.0'
port = 9010


import os
directory_hostname = os.environ['DIRECTORY_HOST'] or hostname

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
                       'http://%s:9000/Register' % directory_hostname,
                       'http://%s:9000/Stop' % directory_hostname)

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

    not_understood_message = lambda: build_message(
        Graph(),
        performatives.NOT_UNDERSTOOD,
        sender=BuyerAgent.uri,
        msgcnt=get_new_msg_count()
    ).serialize(format='xml')

    if message_properties is None:
        return not_understood_message()

    content = message_properties['content']
    action = str(graph_message.value(
        subject=content,
        predicate=RDF.type
    ))

    if action != OntologyConstants.ACTION_SEARCH_PRODUCTS:
        return not_understood_message()

    query_dict = {}
    if graph_message.value(subject=content, predicate=OntologyConstants.QUERY_BRAND):
        print('mega gay is ', graph_message.value(subject=content, predicate=OntologyConstants.QUERY_BRAND))

    if graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_BRAND]):
        query_dict['brand'] = graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_BRAND])

    if graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_SEARCH_TEXT]):
        query_dict['search_text'] = graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_SEARCH_TEXT])

    if graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_MIN_PRICE]):
        query_dict['min_price'] = graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_MIN_PRICE])

    if graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_MAX_PRICE]):
        query_dict['max_price'] = graph_message.value(subject=content, predicate=agn[OntologyConstants.QUERY_MAX_PRICE])

    return search_graph_products(**query_dict).serialize(format='xml')


def search_graph_products(brand='(.*)', search_text='(.*)', min_price=0, max_price=sys.float_info.max):
    all_products = Graph()
    all_products.parse('./rdf/database_products.rdf')

    sparql_query = Template('''
        SELECT DISTINCT ?product ?id ?name ?description ?image ?weight_grams ?category ?price_eurocents ?brand
        WHERE {
            ?product rdf:type ?type_prod .
            ?product ns:product_id ?id .
            ?product ns:product_name ?name .
            ?product ns:product_description ?description .
            ?product ns:weight_grams ?weight_grams .
            ?product ns:category ?category .
            ?product ns:price_eurocents ?price_eurocents .
            ?product ns:image ?image .
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

    result_query = all_products.query(
        sparql_query,
        initNs=dict(
            foaf=FOAF,
            rdf=RDF,
            ns=agn,
        )
    )

    result_graph = Graph()
    for x in result_query:
        subject = x.product
        result_graph.add((subject, RDF.type, agn.product))
        result_graph.add((subject, agn.product_id, x.id))
        result_graph.add((subject, agn.product_name, x.name))
        result_graph.add((subject, agn.product_description, x.description))
        result_graph.add((subject, agn.category, x.category))
        result_graph.add((subject, agn.price_eurocents, x.price_eurocents))
        result_graph.add((subject, agn.brand, x.brand))
        result_graph.add((subject, agn.image, x.image))

    return result_graph


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


# el grafo G tiene que contener toda la informacion
# necesaria para realizar el pedido
# por ejemplo, idPedido, idProducto, idPersona ...
@app.route("/order/<idProds>")
def newOrder(idProds):
    """
    Creates a new order with the idProd
    :return:
    """

    product_ids = idProds.split(',')
    order_id = uuid.uuid4()
    order = agn['order_' + str(order_id)]
    graph_message = Graph()
    graph_message.add((order, RDF.type, Literal(OntologyConstants.ACTION_CREATE_ORDER)))
    graph_message.add((order, agn.order_id, Literal(order_id)))
    for product_id in product_ids:
        graph_message.add((order, agn.product_id, Literal(product_id)))

    vendor_agent = BuyerAgent.find_agent(DirectoryAgent, agn.VendorAgent)

    message = build_message(
        graph_message,
        perf=Literal(performatives.REQUEST),
        sender=BuyerAgent.uri,
        receiver=vendor_agent.uri,
        msgcnt=get_new_msg_count(),
        content=order
    )

    try:
        send_message(message, vendor_agent.address)
    except Exception as e:
        print('owned error', str(e))

    return 'Pedido creado'

    # gr = send_message( build_message(gmess, perf=ACL.request, sender=InfoAgent.uri, receiver=DirectoryAgent.uri, content=reg_obj, msgcnt=mss_cnt),
    # DirectoryAgent.address)
    resp = requests.post(url, data=dataContent)


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
    BuyerAgent.register_agent(DirectoryAgent)
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
