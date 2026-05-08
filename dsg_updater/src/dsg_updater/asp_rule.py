import clingo
import logging
from collections.abc import Callable
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


# wrap a python string as a quoted ASP string literal
def q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# query the database and return ground ASP facts for the current state
def snapshot_to_facts(db: Neo4jWrapper) -> str:
    lines: list[str] = []

    for r in db.query("MATCH (r:Robot) RETURN r.name AS name") or []:
        lines.append(f"robot({q(r['name'])}).")

    for o in db.query(
        "MATCH (o:Object) RETURN o.nodeSymbol AS sym, o.class AS class"
    ) or []:
        lines.append(f"object({q(o['sym'])}).")
        lines.append(f"class({q(o['sym'])}, {q(o.get('class') or 'unknown')}).")

    for o in db.query(
        "MATCH (o:Object) WHERE o.center IS NOT NULL "
        "RETURN o.nodeSymbol AS sym, "
        "       o.center.x AS x, o.center.y AS y, o.center.z AS z"
    ) or []:
        x, y, z = f"{o['x']:.6f}", f"{o['y']:.6f}", f"{o['z']:.6f}"
        lines.append(f'center({q(o["sym"])}, "{x}", "{y}", "{z}").')

    for h in db.query(
        "MATCH (r:Robot)-[:HOLDS]->(o:Object) "
        "RETURN r.name AS robot, o.nodeSymbol AS obj"
    ) or []:
        lines.append(f"base_holds({q(h['robot'])}, {q(h['obj'])}).")

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
        # Persist maps atom names to functions that produce in-memory facts
        persist: dict[str, Callable[[clingo.Symbol], str]] | None = None,
        # Facts accumulated here are included in every solve
        memory: set[str] | None = None,
    ):
        self.name = name
        self.asp_program = asp_program
        self.templates = templates or {}
        self.persist = persist or {}
        self.memory = memory

    def get_all_facts(self, facts: str) -> str:
        if self.memory:
            return facts + "\n" + "\n".join(self.memory)
        return facts

    def solve(self, facts: str) -> list[clingo.Symbol]:
        # Get all facts from memory
        full = self.get_all_facts(facts)
        ctl = clingo.Control(["--warn=none"])
        ctl.add("base", [], full + "\n" + self.asp_program)
        ctl.ground([("base", [])])

        atoms: list[clingo.Symbol] = []
        result = ctl.solve(on_model=lambda m: atoms.extend(m.symbols(shown=True)))

        if result.unsatisfiable:
            logger.warning(f"AspRule '{self.name}' is unsatisfiable")
            return []

        return atoms

    def apply(self, atoms: list[clingo.Symbol], db: Neo4jWrapper) -> None:
        for atom in atoms:
            # Accumulate fact into memory if this atom has a persist function
            if atom.name in self.persist and self.memory is not None:
                self.memory.add(self.persist[atom.name](atom))
            template = self.templates.get(atom.name)
            if template is None:
                if atom.name not in self.persist:
                    logger.warning(
                        f"AspRule '{self.name}': no template for predicate "
                        f"'{atom.name}/{len(atom.arguments)}': skipping {atom}"
                    )
                continue
            args = [a.string for a in atom.arguments]
            db.query(template.render(args))

    # return all stable models; used for belief-space enumeration
    def enumerate_models(self, facts: str) -> list[list[clingo.Symbol]]:
        # Get all facts from memory
        full = self.get_all_facts(facts)
        ctl = clingo.Control(["--warn=none", "0"])
        ctl.add("base", [], full + "\n" + self.asp_program)
        ctl.ground([("base", [])])
        models: list[list[clingo.Symbol]] = []
        with ctl.solve(yield_=True) as handle:  # type: ignore[union-attr]
            for model in handle:
                models.append(model.symbols(shown=True))
        return models

    def __str__(self) -> str:
        return f"AspRule '{self.name}'"
