#!/usr/bin/env python3
import time

from dsg_updater.asp_rule import ActionTemplate, AspRule
from heracles_agents.dsg_interfaces import HeraclesDsgInterface
from heracles.query_interface import Neo4jWrapper


OBJ_HOLDING_PROGRAM = """\
% obj_holding_rule
% An object held by a robot should track the robot's position.
holds(R, O) :- base_holds(R, O).

update_position(O, R) :- holds(R, O), robot(R), object(O).

#show update_position/2.
"""

OBJ_STACKING_PROGRAM = """\
% obj_stacking_rule
% The position of a stacked object is derived from its base object's bbox.
update_stack_position(Y, X) :- with(X, Y), object(X), object(Y).

#show update_stack_position/2.
"""

COMBINED_PROGRAM = """\
% ---- action atoms ----
holds(R, O) :- base_holds(R, O).

update_position(O, R)       :- holds(R, O), robot(R), object(O).
update_stack_position(Y, X) :- with(X, Y), object(X), object(Y).

% ---- integrity constraints ----
:- base_holds(R, _), not robot(R).
:- with(X, X).

#show update_position/2.
#show update_stack_position/2.
"""


UPDATE_POSITION_TEMPLATE = ActionTemplate(
    arg_names=["O", "R"],
    cypher=(
        "MATCH (o:Object {nodeSymbol: '$O'}), (r:Robot {name: '$R'}) "
        "SET o.center = r.position, o.bbox_center = r.position"
    ),
)

UPDATE_STACK_POSITION_TEMPLATE = ActionTemplate(
    arg_names=["Y", "X"],
    cypher=(
        "MATCH (parent:Object {nodeSymbol: '$X'}), "
        "      (child:Object {nodeSymbol: '$Y'}) "
        "SET child.center = point({"
        "  x: parent.bbox_center.x, "
        "  y: parent.bbox_center.y, "
        "  z: parent.bbox_center.z + parent.bbox_dim.z/2 + child.bbox_dim.z/2"
        "}), "
        "child.bbox_center = child.center"
    ),
)


def obj_holding_rule() -> AspRule:
    return AspRule(
        "holding obj",
        OBJ_HOLDING_PROGRAM,
        templates={
            "update_position": UPDATE_POSITION_TEMPLATE,
        },
    )


def obj_stacking_rule() -> AspRule:
    return AspRule(
        "object stacking",
        OBJ_STACKING_PROGRAM,
        templates={
            "update_stack_position": UPDATE_STACK_POSITION_TEMPLATE,
        },
    )


def combined_rule() -> AspRule:
    return AspRule(
        "holding and stacking",
        COMBINED_PROGRAM,
        templates={
            "update_position": UPDATE_POSITION_TEMPLATE,
            "update_stack_position": UPDATE_STACK_POSITION_TEMPLATE,
        },
    )


def main():
    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT",
    )

    rule = combined_rule()

    while True:
        with Neo4jWrapper(
            dsgdb_conf.uri,
            (
                dsgdb_conf.username.get_secret_value(),
                dsgdb_conf.password.get_secret_value(),
            ),
            atomic_queries=True,
            print_profiles=False,
        ) as db:
            atoms = rule.apply(db)

        print(f"[{rule.name}] {len(atoms)} action atom(s):")
        for a in sorted(str(a) for a in atoms):
            print(f"  {a}")

        time.sleep(1)


if __name__ == "__main__":
    main()
