from heracles.query_interface import Neo4jWrapper
from typing import Optional


def get_robot_pose(db: Neo4jWrapper, robot_name: str) -> Optional[tuple]:
    result = db.query(f"""
        MATCH (r:Robot {{name: '{robot_name}'}})
        RETURN r.position.x AS x, r.position.y AS y, r.position.z AS z,
        r.qw AS qw, r.qx AS qx, r.qy AS qy, r.qz AS qz
    """)

    if not result:
        return None

    return (result[0]["x"], result[0]["y"], result[0]["z"],
            result[0]["qx"], result[0]["qy"], result[0]["qz"], result[0]["qw"])


def get_held_objects(db: Neo4jWrapper, robot_name: str):
    robot_exists = db.query(f"MATCH (r:Robot {{name: '{robot_name}'}}) "
                            "RETURN r.name AS name")

    assert robot_exists, f"robot '{robot_name}' does not exist"

    return db.query(f"""
        MATCH (r:Robot {{name: '{robot_name}'}})-[:HOLDS]->(o:Object)
        RETURN o.nodeSymbol AS nodeSymbol
    """)


def robot_hold_obj(db: Neo4jWrapper, robot_name: str, obj_symbol: str) -> bool:
    robot_exists = db.query(f"MATCH (r:Robot {{name: '{robot_name}'}}) "
                            "RETURN r.name AS name")
    obj_exists = db.query(f"MATCH (o:Object {{nodeSymbol: '{obj_symbol}'}}) "
                          "RETURN o.nodeSymbol AS nodeSymbol")

    if not robot_exists or not obj_exists:
        return False

    db.query(f"""
        MATCH (r:Robot {{name: '{robot_name}'}}), (o:Object {{nodeSymbol: '{obj_symbol}'}})
        MERGE (r)-[:HOLDS]->(o)
        RETURN r, o
    """)
    return True


def robot_unhold_obj(db: Neo4jWrapper, robot_name: str, obj_symbol: str) -> bool:
    robot_exists = db.query(f"MATCH (r:Robot {{name: '{robot_name}'}}) "
                            "RETURN r.name AS name")
    obj_exists = db.query(f"MATCH (o:Object {{nodeSymbol: '{obj_symbol}'}}) "
                          "RETURN o.nodeSymbol AS nodeSymbol")

    if not robot_exists or not obj_exists:
        return False

    db.query(f"""
        MATCH (r:Robot {{name: '{robot_name}'}})-[rel:HOLDS]->(o:Object {{nodeSymbol: '{obj_symbol}'}})
        DELETE rel
        RETURN r, o
    """)
    return True


def get_obj_center(db: Neo4jWrapper, obj_symbol: str) -> Optional[tuple]:
    obj_exists = db.query(f"MATCH (o:Object {{nodeSymbol: '{obj_symbol}'}}) "
                          "RETURN o.nodeSymbol AS nodeSymbol")

    if not obj_exists:
        return None

    result = db.query(f"MATCH (o: Object {{nodeSymbol: '{obj_symbol}'}}) "
                      "RETURN o.center as center""")[0]["center"]

    return result.x, result.y, result.z


def set_obj_center(db: Neo4jWrapper, obj_symbol: str, x: float, y: float, z: float) -> bool:
    obj_exists = db.query(f"MATCH (o:Object {{nodeSymbol: '{obj_symbol}'}}) "
                          "RETURN o.nodeSymbol AS nodeSymbol")

    if not obj_exists:
        return False

    db.query(f"MATCH (o:Object {{nodeSymbol: '{obj_symbol}'}})"
             f"SET o.center = point({{x: {x}, y: {y}, z: {z}}}) RETURN o")

    return True
