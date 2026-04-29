import clingo
import logging
from string import Template

from heracles.query_interface import Neo4jWrapper

logger = logging.getLogger(__name__)


class ActionTemplate:
    def __init__(self, arg_names: list[str], cypher: str):
        self.arg_names = arg_names
        self.template = Template(cypher)

    def render(self, atom_args: list[str]) -> str:
        if len(atom_args) != len(self.arg_names):
            raise ValueError(
                f"Template expects {len(self.arg_names)} args ",
                f"({self.arg_names}), got {len(atom_args)}"
            )
        return self.template.substitute(dict(zip(self.arg_names, atom_args)))


# Helper function to wrap a Python string as a quoted ASP string literal
def q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# Query database and return ASP facts about the state
def snapshot_to_facts(db: Neo4jWrapper) -> str:
    lines: list[str] = []

    # Robots
    for r in db.query(
        "MATCH (r:Robot) RETURN r.name AS name"
    ) or []:
        lines.append(f"robot({q(r['name'])}).")

    # Objects
    for o in db.query(
        "MATCH (o:Object) RETURN o.nodeSymbol AS sym, o.class AS class"
    ) or []:
        lines.append(f"object({q(o['sym'])}).")
        lines.append(f"class({q(o['sym'])}, {q(o.get('class') or 'unknown')}).")

    # HOLDS edges
    for h in db.query(
        "MATCH (r:Robot)-[:HOLDS]->(o:Object) "
        "RETURN r.name AS robot, o.nodeSymbol AS obj"
    ) or []:
        lines.append(f"base_holds({q(h['robot'])}, {q(h['obj'])}).")

    # WITH edges
    for w in db.query(
        "MATCH (a:Object)-[:WITH]->(b:Object) "
        "RETURN a.nodeSymbol AS a, b.nodeSymbol AS b"
    ) or []:
        lines.append(f"with({q(w['a'])}, {q(w['b'])}).")

    return "\n".join(lines)


class AspRule:
    def __init__(
        self,
        name: str,
        asp_program: str,
        templates: dict[str, ActionTemplate] | None = None,
    ):
        self.name = name
        self.asp_program = asp_program
        self.templates = templates or {}

    def solve(self, db: Neo4jWrapper) -> list[clingo.Symbol]:
        # Snapshot database state into ASP facts
        facts = snapshot_to_facts(db)

        # Create clingo program with known facts about the world
        ctl = clingo.Control(["--warn=none"])
        ctl.add("base", [], facts + "\n" + self.asp_program)
        ctl.ground([("base", [])])

        # Solve clingo program
        atoms: list[clingo.Symbol] = []
        result = ctl.solve(on_model=lambda m: atoms.extend(m.symbols(shown=True)))

        if result.unsatisfiable:
            logger.warning(f"AspRule '{self.name}' is unsatisfiable")
            return []

        return atoms

    # Solve ASP program, translate atoms to Cypher via templates, execute
    def apply(self, db: Neo4jWrapper) -> list[clingo.Symbol]:
        atoms = self.solve(db)
        for atom in atoms:
            template = self.templates.get(atom.name)
            if template is None:
                logger.warning(
                    f"AspRule '{self.name}': no template for predicate "
                    f"'{atom.name}/{len(atom.arguments)}': skipping {atom}"
                )
                continue
            args = [(a.string) for a in atom.arguments]
            cypher = template.render(args)
            db.query(cypher)
        return atoms

    def __str__(self) -> str:
        return f"AspRule '{self.name}'"
