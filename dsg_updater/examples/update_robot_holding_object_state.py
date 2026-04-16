#!/usr/bin/env python3
import time
from dsg_updater.dsg_updater import DSG_Updater
from dsg_updater.rule import drop_on_unhold_rule, obj_holding_rule, obj_stacking_rule, proximity_class_rule, transitive_holding_rule
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT"
    )
    updater = DSG_Updater(dsgdb_conf)
    confused_classes = {
        frozenset({"decor"}): "decor",
        frozenset({"storage", "decor"}): "decor",
        frozenset({"trash", "decor"}): "decor",
    }
    updater.add_rule(obj_holding_rule())
    updater.add_rule(obj_stacking_rule())
    #updater.add_rule(transitive_holding_rule())
    #updater.add_rule(drop_on_unhold_rule())
    updater.add_rule(proximity_class_rule(confused_classes))
    while True:
        updater.update()
        time.sleep(1)


if __name__ == "__main__":
    main()
