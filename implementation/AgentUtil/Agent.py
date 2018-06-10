"""
.. module:: Agent

Agent
******

:Description: Agent
  Clase para guardar los atributos de un agente

"""

__author__ = 'bejar'

from rdflib.namespace import FOAF, RDF
from AgentUtil.OntoNamespaces import ACL, DSO
from AgentUtil.ACLMessages import build_message, send_message
from rdflib import Graph, Literal, Namespace
from constants.OntologyConstants import ONTOLOGY_URI
from AgentUtil.Logging import config_logger

logger = config_logger(level=1)

ns = Namespace(ONTOLOGY_URI)
mss_cnt = 0


class Agent():
    def __init__(self, name, uri, address, stop):
        self.name = name
        self.uri = uri
        self.address = address
        self.stop = stop

    def register_agent(self, DirectoryAgent):
        """
        Envia un mensaje de registro al servicio de registro
        usando una performativa Request y una accion Register del
        servicio de directorio

        :param gmess:
        :return:
        """

        logger.info('Nos registramos')

        global mss_cnt

        gmess = Graph()

        # Construimos el mensaje de registro
        gmess.bind('foaf', FOAF)
        gmess.bind('dso', DSO)
        reg_obj = ns[self.name + '-Register']
        gmess.add((reg_obj, RDF.type, DSO.Register))
        gmess.add((reg_obj, DSO.Uri, self.uri))
        gmess.add((reg_obj, FOAF.Name, Literal(self.name)))
        gmess.add((reg_obj, DSO.Address, Literal(self.address)))
        gmess.add((reg_obj, DSO.AgentType, DSO.HotelsAgent))

        # Lo metemos en un envoltorio FIPA-ACL y lo enviamos
        gr = send_message(
            build_message(gmess, perf=ACL.request,
                          sender=self.uri,
                          receiver=DirectoryAgent.uri,
                          content=reg_obj,
                          msgcnt=mss_cnt),
            DirectoryAgent.address)
        mss_cnt += 1
        return gr


    def search_agent(self, DirectoryAgent, AgentToSearch):
        return 'lol'
