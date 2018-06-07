from imaplib import Literal
import requests
from flask import Flask, request, Response
from rdflib import Graph

import FIPAACLPerformatives
import OntologyConstants
from AgentUtil import ACLMessages
from orderRequest import OrderRequest
import socket



# Configuration stuff
hostname = socket.gethostname()
port = 9011



app = Flask(__name__)




@app.route('/comm', methods=['GET', 'POST'])
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    print("here CLAgent comunicacion")
    print(request.data)
    print(request.args)

    graph = Graph().parse(data=request.data)

 #   ontology = ACLMessages.get_message_ontology(graph)
 #   if ontology == OntologyConstants.SEND_BUY_ORDER:
    print( 'Its an plan request')
    print(graph)
    order = OrderRequest.from_graph(graph)
    print('Plan graph obtained, lets construct response message')
    return order.product_id
 #   else:
  #      print ('I dont understand')
  #      return ACLMessages.build_message(Graph(), Literal(FIPAACLPerformatives.NOT_UNDERSTOOD), Literal(""))


if __name__ == '__main__':
    app.run(host=hostname, port=port, debug=True)