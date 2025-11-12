from heracles_agents.dsg_interfaces import HeraclesDsgInterface
from heracles.query_interface import Neo4jWrapper
from dsg_updater.rule import Rule


class DSG_Updater:
    def __init__(self, dsgdb_conf: HeraclesDsgInterface):
        self.rules: list[Rule] = []
        self.dsgdb_conf: HeraclesDsgInterface = dsgdb_conf

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def update(self):
        with Neo4jWrapper(
            self.dsgdb_conf.uri,
            (
                self.dsgdb_conf.username.get_secret_value(),
                self.dsgdb_conf.password.get_secret_value(),
            ),
            atomic_queries=True,
            print_profiles=False,
        ) as db:
            for rule in self.rules:
                rule.apply(db)
