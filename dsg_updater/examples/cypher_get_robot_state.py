import argparse
from heracles.query_interface import Neo4jWrapper
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, required=True)
    args = parser.parse_args()

    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT"
    )

    query = f"""
    MATCH (r:Robot {{name: '{args.name}'}})
    RETURN r.x AS x, r.y AS y, r.z AS z, r.qw AS qw, r.qx AS qx, r.qy AS qy, r.qz AS qz
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

        if not result:
            print(f"\nNo robot named '{args.name}' found in the database.")
            return

        state = result[0]
        print(f"\nRobot '{args.name}' state:")
        print(f"    Position: ({state['x']}, {state['y']}, {state['z']})")
        print(f"    Orientation: ({state['qw']}, {state['qx']}, "
              f"{state['qy']}, {state['qz']})")


if __name__ == "__main__":
    main()
