#!/usr/bin/env python3
"""
Belief-space position tracking using HOLDS edges and in-memory history.

Rules:
1. pickup_tracking: on the first HOLDS cycle, records pick-up event and
                    captures the object's position as its origin.
2. most_probable: deterministic position update: track robot while held.
3. belief: choice rules enumerating all possible object states.
"""

import time

from dsg_updater.asp_rule import ActionTemplate, AspRule, q, snapshot_to_facts
from heracles_agents.dsg_interfaces import HeraclesDsgInterface
from heracles.query_interface import Neo4jWrapper


# fires once on first HOLDS cycle to record the pick-up and capture origin position
PICKUP_TRACKING_PROGRAM = """\
has_pickup(O) :- picked_up(_, O).
add_picked_up(O, R)         :- base_holds(R, O), not has_pickup(O).
remember_origin(O, X, Y, Z) :- base_holds(_, O), center(O, X, Y, Z), not has_pickup(O).

#show add_picked_up/2.
#show remember_origin/4.
"""

# Update object position to match robot while HOLDS edge exists
MOST_PROBABLE_PROGRAM = """\
update_position(O, R) :- base_holds(R, O), robot(R), object(O).

#show update_position/2.
"""

# Choice rules produce one world per combination of held/placed/at_origin
BELIEF_PROGRAM = """\
% helpers to avoid anonymous variables (the underscores) in negative literals (e.g. not held(O))
held(O)           :- held_by(O, _).    % derived from the choice rule; could be true or false
ever_picked_up(O) :- picked_up(_, O).  % has this object ever been picked up?
currently_held(O) :- base_holds(_, O). % there is an active HOLDS edge in the DB

% while HOLDS edge exists: robot may or may not actually have the object
{held_by(O, R)}       :- base_holds(R, O).
at_origin(O, X, Y, Z) :- currently_held(O), not held(O), origin(O, X, Y, Z).

% after HOLDS removed: object may have been placed or dropped
{placed_at(O)}        :- ever_picked_up(O), not currently_held(O).
at_origin(O, X, Y, Z) :- ever_picked_up(O), not currently_held(O), not placed_at(O), origin(O, X, Y, Z).

#show held_by/2.
#show placed_at/1.
#show at_origin/4.
"""


UPDATE_POSITION_TEMPLATE = ActionTemplate(
    arg_names=["O", "R"],
    cypher=(
        "MATCH (o:Object {nodeSymbol: '$O'}), (r:Robot {name: '$R'}) "
        "SET o.center = r.position, o.bbox_center = r.position"
    ),
)


COMBINED_PROGRAM = PICKUP_TRACKING_PROGRAM + MOST_PROBABLE_PROGRAM


# Converts add_picked_up and remember_origin atoms to in-memory fact strings
PERSIST = {
    "add_picked_up": lambda a: (
        f"picked_up({q(a.arguments[1].string)},{q(a.arguments[0].string)})."
    ),
    "remember_origin": lambda a: (
        f'origin({q(a.arguments[0].string)},'
        f'"{a.arguments[1].string}",'
        f'"{a.arguments[2].string}",'
        f'"{a.arguments[3].string}").'
    ),
}


def pickup_tracking_rule(memory: set[str]) -> AspRule:
    return AspRule(
        "pickup tracking",
        PICKUP_TRACKING_PROGRAM,
        persist=PERSIST,
        memory=memory,
    )


def most_probable_rule(memory: set[str]) -> AspRule:
    return AspRule(
        "most probable position",
        MOST_PROBABLE_PROGRAM,
        templates={"update_position": UPDATE_POSITION_TEMPLATE},
        memory=memory,
    )


def combined_rule(memory: set[str]) -> AspRule:
    return AspRule(
        "pickup tracking and most probable",
        COMBINED_PROGRAM,
        templates={"update_position": UPDATE_POSITION_TEMPLATE},
        persist=PERSIST,
        memory=memory,
    )


def belief_rule(memory: set[str]) -> AspRule:
    return AspRule("belief space", BELIEF_PROGRAM, memory=memory)


def main():
    dsgdb_conf = HeraclesDsgInterface(
        dsg_interface_type="heracles",
        uri="neo4j://$ADT4_HERACLES_IP:$ADT4_HERACLES_PORT",
    )

    memory: set[str] = set()
    rule = combined_rule(memory)
    belief = belief_rule(memory)

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
            facts = snapshot_to_facts(db)
            atoms = rule.solve(facts)
            rule.apply(atoms, db)
            models = belief.enumerate_models(facts)

        print(f"[{rule.name}] {len(atoms)} action atom(s):")
        for a in sorted(str(a) for a in atoms):
            print(f"  {a}")

        print(f"[{belief.name}] {len(models)} possible world(s)")
        for i, m in enumerate(models):
            print(f"  World {i + 1}: {sorted(str(a) for a in m)}")

        time.sleep(1)


if __name__ == "__main__":
    main()
