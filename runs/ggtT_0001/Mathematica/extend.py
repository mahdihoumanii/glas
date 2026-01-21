#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Complete 1-loop propagator sets by inserting routing-consistent propagators.

Key guarantees:
- Internal representation uses full external-leg basis [p1..pn].
- Allowed steps are ONLY unit steps +/- p_i.
- No momentum-conservation elimination during the algorithm.
- Added shifts are inserted only along shortest unit-step paths between existing shifts.
- Output may optionally eliminate one momentum using explicit incoming/outgoing sets.
"""

from __future__ import annotations

import re
from collections import deque
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

# ============================================================
# Parsing helpers
# ============================================================


def _split_top_level_entries(s: str) -> List[str]:
    """Split a string like "[a,b],[c,d]" into ["[a,b]", "[c,d]"]"""
    entries = []
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if ch in "[{":
            if depth == 0:
                start = i
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0 and start is not None:
                entries.append(s[start : i + 1].strip())
                start = None
    return entries


def _strip_brackets(s: str) -> str:
    s = s.strip()
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
        return s[1:-1]
    return s


def parse_topology_list(raw_list_str: str, local_dict: Dict[str, sp.Symbol]) -> List[Tuple[sp.Expr, sp.Expr]]:
    """
    raw_list_str like: [[l - p3, 0], [l, mt], [l - p2, mt]]
    Return: [(mom_expr, mass_expr), ...] as SymPy
    Accepts [] or {} brackets.
    """
    s = raw_list_str.strip()
    if not ((s.startswith("[[") and s.endswith("]]")) or (s.startswith("{{") and s.endswith("}}"))):
        raise ValueError(f"Expected list like [[...], [...]] or {{...}} but got: {raw_list_str}")

    inner = _strip_brackets(s)
    entries = _split_top_level_entries(inner)

    topo = []
    for ent in entries:
        ent = ent.strip()
        payload = _strip_brackets(ent)

        # split on the first comma at top level
        depth = 0
        split_idx = None
        for i, ch in enumerate(payload):
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                split_idx = i
                break
        if split_idx is None:
            raise ValueError(f"Entry does not contain a comma: {ent}")

        mom_s = payload[:split_idx].strip()
        mass_s = payload[split_idx + 1 :].strip()
        mom = parse_expr(mom_s, local_dict=local_dict, transformations=TRANSFORMS)
        mass = parse_expr(mass_s, local_dict=local_dict, transformations=TRANSFORMS)
        topo.append((sp.expand(mom), sp.expand(mass)))

    return topo


# ============================================================
# Topology completion
# ============================================================


def shift_of(mom: sp.Expr, l: sp.Symbol) -> sp.Expr:
    """Return q in (l+q) from mom expression."""
    return sp.expand(mom - l)


def coeff_vector(q: sp.Expr, basis: Sequence[sp.Symbol]) -> List[int]:
    """Integer coefficient vector of q in the chosen basis."""
    qq = sp.expand(q)
    return [int(qq.coeff(b)) for b in basis]


def vector_to_expr(vec: Sequence[int], basis: Sequence[sp.Symbol]) -> sp.Expr:
    return sp.expand(sum(vec[i] * basis[i] for i in range(len(basis))))


def vec_key(vec: Sequence[int]) -> Tuple[int, ...]:
    return tuple(int(v) for v in vec)


def rank_of(vecs: List[List[int]]) -> int:
    if not vecs:
        return 0
    return sp.Matrix(vecs).rank()


def l1_dist(a: Sequence[int], b: Sequence[int]) -> int:
    return sum(abs(b[i] - a[i]) for i in range(len(a)))


def choose_step_index(
    a: Sequence[int],
    delta: Sequence[int],
    seen: Iterable[Tuple[int, ...]],
    missing_indices: Sequence[int],
    allowed_max_abs: int,
    incoming_indices: Sequence[int],
    outgoing_indices: Sequence[int],
) -> Optional[int]:
    """
    Choose a step index k for shortest-path progress with routing priority:
    1) missing basis directions first
    2) steps that land on an existing node (if possible)
    3) incoming legs with negative step
    4) outgoing legs with positive step
    5) fallback basis order
    """
    candidates = [i for i, d in enumerate(delta) if d != 0]
    if not candidates:
        return None

    def within_bounds(i: int) -> bool:
        step = 1 if delta[i] > 0 else -1
        return abs(a[i] + step) <= allowed_max_abs

    candidates = [i for i in candidates if within_bounds(i)]
    if not candidates:
        return None

    missing_first = [i for i in candidates if i in missing_indices]
    if missing_first:
        candidates = missing_first

    def is_existing_step(i: int) -> bool:
        step = 1 if delta[i] > 0 else -1
        a_next = list(a)
        a_next[i] += step
        return tuple(a_next) in seen

    existing = [i for i in candidates if is_existing_step(i)]
    if existing:
        candidates = existing

    incoming_neg = [i for i in candidates if i in incoming_indices and delta[i] < 0]
    if incoming_neg:
        return min(incoming_neg)

    outgoing_pos = [i for i in candidates if i in outgoing_indices and delta[i] > 0]
    if outgoing_pos:
        return min(outgoing_pos)

    return min(candidates)


def extend_topology(
    topo_in: List[Tuple[sp.Expr, sp.Expr]],
    l: sp.Symbol,
    basis: Sequence[sp.Symbol],
    target_nprops: Optional[int],
    eliminate_index: Optional[int],
    incoming_indices: Sequence[int],
    outgoing_indices: Sequence[int],
    rank_needed: Optional[int] = None,
    max_add: int = 50,
    mass_new: sp.Expr = sp.Integer(0),
) -> List[Tuple[sp.Expr, sp.Expr]]:
    """
    Extend a topology by inserting missing unit-step propagators.

    Algorithm:
    - Represent each shift q as integer vector over full basis.
    - Iteratively choose the pair (a,b) in S with maximal L1 distance.
    - Walk along a shortest path from a to b; if a step hits an existing node,
      advance to it; otherwise insert that node (one insertion per iteration).
    - Rank check uses a projection that drops eliminate_index.

    This prevents unphysical shifts because only unit steps are allowed and
    new nodes are inserted only on shortest paths between existing nodes.
    """
    topo = list(topo_in)
    shifts = [shift_of(mom, l) for mom, _ in topo]
    vecs = [coeff_vector(q, basis) for q in shifts]
    seen = {vec_key(v) for v in vecs}
    max_abs_input = max((abs(c) for v in vecs for c in v), default=1)
    allowed_max_abs = max(1, max_abs_input)

    def drop_component(v: List[int], idx: Optional[int]) -> List[int]:
        if idx is None:
            return v[:]
        return [c for i, c in enumerate(v) if i != idx]

    def current_rank() -> int:
        proj = [drop_component(list(v), eliminate_index) for v in seen]
        return rank_of(proj)

    if rank_needed is None:
        rank_needed = max(0, len(basis) - 1 if eliminate_index is not None else len(basis))

    added = 0

    def need_more() -> bool:
        need_props = target_nprops is not None and len(topo) < target_nprops
        need_rank = current_rank() < rank_needed
        return need_props or need_rank

    # Deterministic ordering for pair selection
    def sorted_vecs() -> List[List[int]]:
        return [list(v) for v in sorted(seen)]

    def has_existing_step(a_vec: List[int], b_vec: List[int]) -> bool:
        delta_vec = [b_vec[i] - a_vec[i] for i in range(len(basis))]
        for i, d in enumerate(delta_vec):
            if d == 0:
                continue
            step = 1 if d > 0 else -1
            a_next = a_vec[:]
            a_next[i] += step
            if vec_key(a_next) in seen:
                return True
        return False

    def insert_node(vec: List[int]) -> None:
        nonlocal added
        key = vec_key(vec)
        if key in seen:
            return
        if any(abs(c) > allowed_max_abs for c in vec):
            return
        seen.add(key)
        mom_new = sp.expand(l + vector_to_expr(vec, basis))
        topo.append((mom_new, mass_new))
        added += 1

    def compute_missing_indices() -> List[int]:
        indices = set()
        vec_list = [list(v) for v in seen]
        for i in range(len(vec_list)):
            for j in range(i + 1, len(vec_list)):
                diff = [vec_list[i][k] - vec_list[j][k] for k in range(len(basis))]
                for k, d in enumerate(diff):
                    if d != 0:
                        indices.add(k)
        missing = [i for i in range(len(basis)) if i not in indices]
        return missing

    def insert_shortest_path(a_vec: List[int], b_vec: List[int]) -> bool:
        """Insert missing nodes along shortest path from a to b, one at a time."""
        a = a_vec[:]
        b = b_vec[:]
        if not has_existing_step(a, b) and has_existing_step(b, a):
            a, b = b, a
        while l1_dist(a, b) > 1:
            delta = [b[i] - a[i] for i in range(len(basis))]
            missing_indices = compute_missing_indices()
            k = choose_step_index(
                a,
                delta,
                seen,
                missing_indices,
                allowed_max_abs,
                incoming_indices,
                outgoing_indices,
            )
            if k is None:
                return False
            step = 1 if delta[k] > 0 else -1
            a_next = a[:]
            a_next[k] += step
            if vec_key(a_next) in seen:
                a = a_next
                continue
            insert_node(a_next)
            return True
        return False

    # Phase A: path completion until unit-step connected (no pair with dist>1)
    while need_more() and added < max_add:
        vec_list = sorted_vecs()
        max_dist = -1
        pair = None
        for i in range(len(vec_list)):
            for j in range(i + 1, len(vec_list)):
                d = l1_dist(vec_list[i], vec_list[j])
                if d > max_dist:
                    max_dist = d
                    pair = (vec_list[i], vec_list[j])

        if pair is None or max_dist <= 1:
            break

        if not insert_shortest_path(pair[0], pair[1]):
            break

    # Phase B: pad to target_nprops with deterministic chain completion
    def append_path(chain: List[List[int]], start: List[int], target: List[int]) -> bool:
        a = start[:]
        while a != target:
            delta = [target[i] - a[i] for i in range(len(basis))]
            missing_indices = compute_missing_indices()
            k = choose_step_index(
                a,
                delta,
                seen,
                missing_indices,
                allowed_max_abs,
                incoming_indices,
                outgoing_indices,
            )
            if k is None:
                return False
            step = 1 if delta[k] > 0 else -1
            a_next = a[:]
            a_next[k] += step
            if vec_key(a_next) not in seen:
                insert_node(a_next)
            chain.append(a_next)
            a = a_next
        return True

    def build_chain_all() -> List[List[int]]:
        vec_list = sorted_vecs()
        if not vec_list:
            return []
        zero = [0] * len(basis)
        start = zero if vec_key(zero) in seen else min(vec_list, key=lambda v: (sum(abs(x) for x in v), v))
        chain = [start]
        current = start
        unvisited = {vec_key(v): list(v) for v in vec_list if v != start}
        while unvisited:
            target = min(unvisited.values(), key=lambda v: (l1_dist(current, v), v))
            if not append_path(chain, current, target):
                break
            current = target
            unvisited.pop(vec_key(target))
        return chain

    def missing_indices_from_chain(chain: List[List[int]]) -> List[int]:
        covered = set()
        for i in range(len(chain) - 1):
            diff = [chain[i + 1][k] - chain[i][k] for k in range(len(basis))]
            for k, d in enumerate(diff):
                if d != 0:
                    covered.add(k)
        return [i for i in range(len(basis)) if i not in covered]

    while target_nprops is not None and len(topo) < target_nprops and added < max_add:
        chain = build_chain_all()
        if not chain:
            break

        end_left = chain[0]
        end_right = chain[-1]
        if sum(abs(x) for x in end_left) > sum(abs(x) for x in end_right):
            v_max = end_left
            at_left = True
        else:
            v_max = end_right
            at_left = False

        missing = missing_indices_from_chain(chain)
        appended = False
        for idx in missing + [i for i in range(len(basis)) if i not in missing]:
            candidate = v_max[:]
            candidate[idx] -= 1
            if vec_key(candidate) in seen or any(abs(c) > allowed_max_abs for c in candidate):
                continue
            insert_node(candidate)
            if at_left:
                chain.insert(0, candidate)
            else:
                chain.append(candidate)
            appended = True
            break
        if not appended:
            break

    if target_nprops is not None and len(topo) < target_nprops:
        print("Warning: could not reach target_nprops within max_add")

    return topo


# ============================================================
# Output
# ============================================================


def apply_elimination(
    expr: sp.Expr,
    basis: Sequence[sp.Symbol],
    eliminate_index: Optional[int],
    incoming_indices: Sequence[int],
    outgoing_indices: Sequence[int],
) -> sp.Expr:
    """
    Optionally eliminate one momentum at output time using:
      sum(incoming) = sum(outgoing)
    """
    if eliminate_index is None:
        return expr

    p_elim = basis[eliminate_index]
    incoming = [basis[i] for i in incoming_indices]
    outgoing = [basis[i] for i in outgoing_indices]

    if eliminate_index in outgoing_indices:
        sub = {p_elim: sum(incoming) - (sum(outgoing) - p_elim)}
    elif eliminate_index in incoming_indices:
        sub = {p_elim: sum(outgoing) - (sum(incoming) - p_elim)}
    else:
        return expr

    return sp.expand(expr.subs(sub))


def sympy_to_mathematica_expr(expr: sp.Expr) -> str:
    """Mathematica-friendly string for linear expressions."""
    return sp.sstr(sp.expand(expr))


def write_extended_m(
    out_path: str,
    extended_list: List[List[Tuple[sp.Expr, sp.Expr]]],
    var_name: str,
    basis: Sequence[sp.Symbol],
    eliminate_index: Optional[int],
    incoming_indices: Sequence[int],
    outgoing_indices: Sequence[int],
) -> None:
    lines = []
    lines.append("(* Auto-generated by extend.py *)\n")
    lines.append(f"{var_name} = {{\n")

    blocks = []
    for topo in extended_list:
        entries = []
        for mom, mass in topo:
            mom_out = apply_elimination(mom, basis, eliminate_index, incoming_indices, outgoing_indices)
            mom_s = sympy_to_mathematica_expr(mom_out)
            mass_s = sympy_to_mathematica_expr(mass)
            entries.append(f"{{{mom_s}, {mass_s}}}")
        blocks.append("  {" + ", ".join(entries) + "}")

    lines.append(",\n".join(blocks))
    lines.append("\n};\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ============================================================
# Main + self-test
# ============================================================


def self_test() -> None:
    l = sp.Symbol("l")
    p1, p2, p3, p4 = sp.symbols("p1 p2 p3 p4")
    mt = sp.Symbol("mt")

    local_dict = {"l": l, "p1": p1, "p2": p2, "p3": p3, "p4": p4, "mt": mt}
    basis = [p1, p2, p3, p4]

    incoming_indices = [0, 1]
    outgoing_indices = [2, 3]

    raw = "top1:[[l, mt], [l - p1 - p2 + p3, 0], [l - p2, mt]]"
    m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\[\[.*\]\])\s*;?\s*$", raw)
    topo_in = parse_topology_list(m.group(2), local_dict)

    topo_ext = extend_topology(
        topo_in,
        l,
        basis,
        target_nprops=4,
        eliminate_index=None,
        incoming_indices=incoming_indices,
        outgoing_indices=outgoing_indices,
        rank_needed=3,
        max_add=10,
        mass_new=sp.Integer(0),
    )

    added = topo_ext[len(topo_in) :]
    required = sp.expand(l - p1 - p2)
    assert any(sp.expand(mom) == required for mom, _ in added), "Missing l - p1 - p2"

    print("Self-test added propagators:")
    for mom, mass in added:
        print("  ", mom, ",", mass)

    # Padding tests to ensure we reach 4 propagators
    raw_a = "tA:{{l,0},{l-p2,0},{l-p3,mt}}"
    m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\{\{.*\}\})\s*$", raw_a)
    topo_a = parse_topology_list(m.group(2), local_dict)
    topo_a_ext = extend_topology(
        topo_a,
        l,
        basis,
        target_nprops=4,
        eliminate_index=None,
        incoming_indices=incoming_indices,
        outgoing_indices=outgoing_indices,
        rank_needed=3,
        max_add=10,
        mass_new=sp.Integer(0),
    )
    assert len(topo_a_ext) == 4, "Expected 4 propagators for tA"

    raw_b = "tB:{{l,mt},{l-p1-p2,mt},{l-p2,0}}"
    m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\{\{.*\}\})\s*$", raw_b)
    topo_b = parse_topology_list(m.group(2), local_dict)
    topo_b_ext = extend_topology(
        topo_b,
        l,
        basis,
        target_nprops=4,
        eliminate_index=None,
        incoming_indices=incoming_indices,
        outgoing_indices=outgoing_indices,
        rank_needed=3,
        max_add=10,
        mass_new=sp.Integer(0),
    )
    assert len(topo_b_ext) == 4, "Expected 4 propagators for tB"

    raw_c = "tC:{{l,0},{l-p2,0},{l-p1-p2,0}}"
    m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\{\{.*\}\})\s*$", raw_c)
    topo_c = parse_topology_list(m.group(2), local_dict)
    topo_c_ext = extend_topology(
        topo_c,
        l,
        basis,
        target_nprops=4,
        eliminate_index=None,
        incoming_indices=incoming_indices,
        outgoing_indices=outgoing_indices,
        rank_needed=3,
        max_add=10,
        mass_new=sp.Integer(0),
    )
    for mom, _ in topo_c_ext:
        v = coeff_vector(shift_of(mom, l), basis)
        assert all(abs(c) <= 1 for c in v), "Found |coeff| > 1 in tC"
    required_c = sp.expand(l - p1 - p2 - p3)
    assert any(sp.expand(mom) == required_c for mom, _ in topo_c_ext), "Missing l - p1 - p2 - p3 in tC"


def main() -> None:
    # Symbols used in input
    l = sp.Symbol("l")
    p1, p2, p3, p4, p5 = sp.symbols("p1 p2 p3 p4 p5")
    mt = sp.Symbol("mt")

    local_dict = {
        "l": l, "p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5, "mt": mt
    }

    # Full external basis (no elimination during algorithm)
    basis = [p1, p2, p3, p4, p5]

    # Incoming/outgoing leg indices (edit to match your process)
    incoming_indices = [0, 1]
    outgoing_indices = [2, 3, 4]

    # Choose which momentum to eliminate ONLY at output (e.g., last leg)
    eliminate_index = len(basis) - 1

    in_path = "Files/Topologies.txt"
    out_path = "Extended.m"

    extended = []

    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\[\[.*\]\]|\{\{.*\}\})\s*;?\s*$", line)
            if not m:
                raise ValueError(f"Line does not match expected format:\n{line}")

            raw_list = m.group(2)
            topo_in = parse_topology_list(raw_list, local_dict)

            topo_ext = extend_topology(
                topo_in,
                l,
                basis,
                target_nprops=4,
                eliminate_index=eliminate_index,
                incoming_indices=incoming_indices,
                outgoing_indices=outgoing_indices,
                rank_needed=len(basis) - 1,
                max_add=20,
                mass_new=sp.Integer(0),
            )

            extended.append(topo_ext)

    write_extended_m(
        out_path,
        extended,
        var_name="Extended",
        basis=basis,
        eliminate_index=eliminate_index,
        incoming_indices=incoming_indices,
        outgoing_indices=outgoing_indices,
    )
    print(f"Wrote {out_path} with {len(extended)} extended topologies.")


if __name__ == "__main__":
    self_test()
    main()
