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
            "MATCH (r:Robot)-[:HOLDS]->(y:Object)-[:WITH*1..]->(z:Object) "
            "WHERE NOT (r)-[:HOLDS]->(z) "
            "RETURN r.name AS robot, z.nodeSymbol AS object"
        )

    def action(db: Neo4jWrapper, nodes):
        for node in nodes:
            robot = node["robot"]
            obj = node["object"]

            db.query(f"""
                MATCH (r:Robot {{name: '{robot}'}}), (z:Object {{nodeSymbol: '{obj}'}})
                MERGE (r)-[:HOLDS]->(z)
                RETURN z
            """)

    return Rule("transitive holding", condition, action)


def obj_stacking_rule():
    def condition(db: Neo4jWrapper):
        return db.query(
            "MATCH (x:Object)-[:WITH]->(y:Object) "
            "RETURN x.nodeSymbol AS sym_x"
        )

    def action(db: Neo4jWrapper, nodes):
        db.query(
            "MATCH (x:Object)-[:WITH]->(y:Object) "
            "SET y.center = point({x: x.bbox_center.x, y: x.bbox_center.y, "
            "    z: x.bbox_center.z + x.bbox_dim.z / 2.0 + y.bbox_dim.z / 2.0}), "
            "    y.bbox_center = point({x: x.bbox_center.x, y: x.bbox_center.y, "
            "    z: x.bbox_center.z + x.bbox_dim.z / 2.0 + y.bbox_dim.z / 2.0})"
        )

    return Rule("object stacking", condition, action)


def drop_on_unhold_rule():
    def condition(db: Neo4jWrapper):
        return db.query(
            "MATCH (r:Robot)-[:HOLDS]->(b:Object) "
            "WHERE EXISTS { (:Object)-[:WITH*1..]->(b) } "
            "AND NOT EXISTS { (r)-[:HOLDS]->(a:Object)-[:WITH*1..]->(b) } "
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


def proximity_class_rule(confused_classes: dict[frozenset, str]):
    """
    Args:
        confused_classes: maps frozenset({class_a, class_b}) -> resolved_class.
            When two objects of a confused pair have overlapping bounding boxes,
            both are reclassified to resolved_class.
    """
    all_classes = list({c for pair in confused_classes for c in pair})

    def condition(db: Neo4jWrapper):
        class_list = "[" + ", ".join(f"'{c}'" for c in all_classes) + "]"
        return db.query(
            f"MATCH (a:Object), (b:Object) "
            f"WHERE a.nodeSymbol < b.nodeSymbol "
            f"AND a.class IN {class_list} AND b.class IN {class_list} "
            f"AND abs(a.bbox_center.x - b.bbox_center.x) < (a.bbox_dim.x + b.bbox_dim.x) / 2 "
            f"AND abs(a.bbox_center.y - b.bbox_center.y) < (a.bbox_dim.y + b.bbox_dim.y) / 2 "
            f"AND abs(a.bbox_center.z - b.bbox_center.z) < (a.bbox_dim.z + b.bbox_dim.z) / 2 "
            f"RETURN a.nodeSymbol AS sym_a, a.class AS class_a, "
            f"b.nodeSymbol AS sym_b, b.class AS class_b"
        )

    def action(db: Neo4jWrapper, nodes):
        for node in nodes:
            sym_a, sym_b = node["sym_a"], node["sym_b"]
            class_a, class_b = node["class_a"], node["class_b"]
            pair = frozenset({class_a, class_b})
            resolved = confused_classes.get(pair)
            if resolved is None:
                continue

            if class_a == class_b:
                # Same class: merge b into a, then delete b.
                for rel in ("WITH", "HOLDS", "CONTAINS"):
                    db.query(
                        f"MATCH (x)-[:{rel}]->(b:Object {{nodeSymbol: '{sym_b}'}}) "
                        f"WHERE x.nodeSymbol <> '{sym_a}' "
                        f"MATCH (a:Object {{nodeSymbol: '{sym_a}'}}) MERGE (x)-[:{rel}]->(a)"
                    )
                db.query(
                    f"MATCH (b:Object {{nodeSymbol: '{sym_b}'}})-[:WITH]->(x) "
                    f"WHERE x.nodeSymbol <> '{sym_a}' "
                    f"MATCH (a:Object {{nodeSymbol: '{sym_a}'}}) MERGE (a)-[:WITH]->(x)"
                )
                db.query(f"MATCH (b:Object {{nodeSymbol: '{sym_b}'}}) DETACH DELETE b")
            else:
                db.query(f"MATCH (a:Object {{nodeSymbol: '{sym_a}'}}) SET a.class = '{resolved}'")
                db.query(f"MATCH (b:Object {{nodeSymbol: '{sym_b}'}}) SET b.class = '{resolved}'")

    return Rule("proximity class correction", condition, action)
