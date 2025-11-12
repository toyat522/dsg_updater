import argparse
from dsg_updater.dsg_state_utils import get_obj_center
from heracles.query_interface import Neo4jWrapper
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--object", type=str, required=True)
    args = parser.parse_args()

    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT"
    )

    with Neo4jWrapper(
        dsgdb_conf.uri,
        (
            dsgdb_conf.username.get_secret_value(),
            dsgdb_conf.password.get_secret_value(),
        ),
        atomic_queries=True,
        print_profiles=False,
    ) as db:
        x, y, z = get_obj_center(db, args.object)
        print(f"\nObject '{args.object}' at (x: {x}, y: {y}, z: {z})")


if __name__ == "__main__":
    main()
