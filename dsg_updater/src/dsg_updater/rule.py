from heracles.query_interface import Neo4jWrapper


class Rule:
    def __init__(self, name: str, condition, action):
        self.name = name
        self.condition = condition
        self.action = action

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
                SET o.center = point({{x: r.x, y: r.y, z: r.z}})
                RETURN o
            """)

    return Rule("holding obj", condition, action)
