import argparse
from heracles.query_interface import Neo4jWrapper
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", type=str, required=True)
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--y", type=float, required=True)
    parser.add_argument("--z", type=float, default=0.0)
    parser.add_argument("--qw", type=float, default=1.0)
    parser.add_argument("--qx", type=float, default=0.0)
    parser.add_argument("--qy", type=float, default=0.0)
    parser.add_argument("--qz", type=float, default=0.0)
    args = parser.parse_args()

    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT"
    )

    query = f"""
        MERGE (r:Robot {{name: '{args.robot}'}})
        SET r.position = point({{x: {args.x}, y: {args.y}, z: {args.z}}}),
            r.qw = {args.qw},
            r.qx = {args.qx},
            r.qy = {args.qy},
            r.qz = {args.qz}
        RETURN r
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
        print(f"\nUpdated robot pose: {result}")


if __name__ == "__main__":
    main()
