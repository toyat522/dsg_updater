from heracles.query_interface import Neo4jWrapper


class Rule:
    def __init__(self, name: str, condition, action):
        self.name = name
        self.condition = condition
        self.action = action

    # Maybe these input strings should be in a more restrictive language
    # which maps into a cypher query.
    #
    # By having a more restricted language, we can these rules can be more easily
    # resolved.
    def set_condition(query: str):
        pass

    def set_action(query: str):
        pass

    def apply(self, db):
        affected = self.condition(db)
        if affected:
            self.action(db, affected)

    def __str__(self):
        return f"Rule '{self.name}'"


def obj_holding_rule():
    def condition(db: Neo4jWrapper):
        return db.query("MATCH (r:Robot)-[:HOLDS]->(o:Object) "
                        "RETURN r.name AS robot, o.nodeSymbol AS object")

    def action(db: Neo4jWrapper, nodes):
        for node in nodes:
            robot = node["robot"]
            obj = node["object"]

            db.query(f"""
                MATCH (r:Robot {{name: '{robot}'}})-[:HOLDS]->(o:Object {{nodeSymbol: '{obj}'}})
                SET o.center = r.position
                SET o.bbox_center = r.position
                RETURN o
            """)

    return Rule("holding obj", condition, action)


def transitive_holding_rule():
    def condition(db: Neo4jWrapper):
        return db.query(
            "MATCH (r:Robot)-[:HOLDS]->(y:Object)-[:HOLDS*1..]->(z:Object) "
            "WHERE NOT (r)-[:HOLDS]->(z) "
            "RETURN r.name AS robot, r.position AS position, z.nodeSymbol AS object"
        )

    def action(db: Neo4jWrapper, nodes):
        for node in nodes:
            robot = node["robot"]
            obj = node["object"]

            db.query(f"""
                MATCH (r:Robot {{name: '{robot}'}}), (z:Object {{nodeSymbol: '{obj}'}})
                MERGE (r)-[:HOLDS]->(z)
                SET z.center = r.position
                SET z.bbox_center = r.position
                RETURN z
            """)

    return Rule("transitive holding", condition, action)


def drop_on_unhold_rule():
    def condition(db: Neo4jWrapper):
        # A Robot->b HOLDS edge is stale-transitive when:
        # 1. Some Object transitively holds b (so b is "inside" something, not directly gripped)
        # 2. But Robot no longer holds any Object that transitively reaches b
        return db.query(
            "MATCH (r:Robot)-[:HOLDS]->(b:Object) "
            "WHERE EXISTS { (:Object)-[:HOLDS*1..]->(b) } "
            "AND NOT EXISTS { (r)-[:HOLDS]->(a:Object)-[:HOLDS*1..]->(b) } "
            "RETURN r.name AS robot, b.nodeSymbol AS held"
        )

    def action(db: Neo4jWrapper, nodes):
        for node in nodes:
            robot = node["robot"]
            held = node["held"]

            db.query(f"""
                MATCH (r:Robot {{name: '{robot}'}})-[rel:HOLDS]->(b:Object {{nodeSymbol: '{held}'}})
                DELETE rel
            """)

    return Rule("drop on unhold", condition, action)
