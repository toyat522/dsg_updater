from heracles.query_interface import Neo4jWrapper

from heracles_agents.dsg_interfaces import HeraclesDsgInterface
from dsg_updater.rule import Rule


class UpdateGenerator:
    def __init__(self, dsgdb_conf: HeraclesDsgInterface):
        self.rules: list[Rule] = []
        self.dsgdb_conf: HeraclesDsgInterface = dsgdb_conf

    def add_rule(self, cypher_string):
        self.rules.append()

    def update_dsg(self):
        for rule in self.rules:
            pass
