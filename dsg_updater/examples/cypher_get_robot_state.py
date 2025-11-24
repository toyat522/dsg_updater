import argparse
from dsg_updater.dsg_state_utils import get_held_objects, get_robot_pose
from heracles.query_interface import Neo4jWrapper
from heracles_agents.dsg_interfaces import HeraclesDsgInterface


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", type=str, required=True)
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
        robot_pose = get_robot_pose(db, args.robot)

        if robot_pose is None:
            print(f"Failed to get state for robot '{args.robot}'")
            return

        x, y, z, qx, qy, qz, qw = robot_pose
        held_objects = get_held_objects(db, args.robot)
        print(f"\nRobot '{args.robot}' state:")
        print(f"    (x: {x}, y: {y}, z: {z})")
        print(f"    (qx: {qx}, qy: {qy}, qz: {qz}, qw: {qw})")
        print(f"    Holding: {held_objects}")


if __name__ == "__main__":
    main()
