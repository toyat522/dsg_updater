import argparse
from dsg_updater.dsg_state_utils import robot_hold_obj, robot_unhold_obj
from heracles.query_interface import Neo4jWrapper
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", type=str, required=True)
    parser.add_argument("--object", type=str, required=True)
    args = parser.parse_args()

    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT"
    )

    query = f"""
        MATCH (r:Robot {{name: '{args.robot}'}})-[:HOLDS]->(o:Object {{nodeSymbol: '{args.object}'}})
        RETURN r, o
    """

    with Neo4jWrapper(
        dsgdb_conf.uri,
        (
            dsgdb_conf.username.get_secret_value(),
            dsgdb_conf.password.get_secret_value(),
        ),
        atomic_queries=True,
        print_profiles=False,
    ) as db:
        result = db.query(query)

        if result:
            print(f"\nRobot '{args.robot}' was holding '{args.object}'")
            robot_unhold_obj(db, args.robot, args.object)
            print(f"Released '{args.object}' from '{args.robot}'")
        else:
            print(f"\nRobot '{args.robot}' was not holding '{args.object}'")
            robot_hold_obj(db, args.robot, args.object)
            print(f"'{args.robot}' now holds '{args.object}'")


if __name__ == "__main__":
    main()
