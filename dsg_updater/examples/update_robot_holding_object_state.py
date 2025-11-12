from dsg_updater.update_generator import UpdateGenerator
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT"
    )
    updater = UpdateGenerator(dsgdb_conf)
    updater.update_dsg()


if __name__ == "__main__":
    main()
