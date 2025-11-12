import time
from dsg_updater.dsg_updater import DSG_Updater
from dsg_updater.rule import obj_holding_rule
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT"
    )
    updater = DSG_Updater(dsgdb_conf)
    updater.add_rule(obj_holding_rule())
    while True:
        updater.update()
        time.sleep(1)


if __name__ == "__main__":
    main()
