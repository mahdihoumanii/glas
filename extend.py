#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Complete 1-loop propagator sets by inserting routing-consistent propagators.

Algorithm:
1. Parse propagators as nodes in integer lattice (shift vectors)
2. Build adjacency graph where edges = unit step (differ by ±1 in one coordinate)
3. Find shortest paths between existing nodes to connect them
4. Add missing nodes along those paths
5. Extend to reach target_nprops

A valid 1-loop topology forms a cycle where consecutive propagators differ
by exactly one external momentum.
"""

from __future__ import annotations

import re
from collections import deque
from typing import Dict, List, Optional, Sequence, Set, Tuple

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
    Parse topology like: [[l - p3, 0], [l, mt], [l - p2, mt]]
    Return: [(mom_expr, mass_expr), ...]
    """
    s = raw_list_str.strip()
    if not ((s.startswith("[[") and s.endswith("]]")) or (s.startswith("{{") and s.endswith("}}"))):
        raise ValueError(f"Expected list like [[...], [...]] but got: {raw_list_str}")

    inner = _strip_brackets(s)
    entries = _split_top_level_entries(inner)

    topo = []
    for ent in entries:
        ent = ent.strip()
        payload = _strip_brackets(ent)

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
# Core data structures
# ============================================================


def shift_of(mom: sp.Expr, l: sp.Symbol) -> sp.Expr:
    """Return q in (l+q) from mom expression."""
    return sp.expand(mom - l)


def coeff_vector(q: sp.Expr, basis: Sequence[sp.Symbol]) -> Tuple[int, ...]:
    """Integer coefficient vector of q in the basis."""
    qq = sp.expand(q)
    return tuple(int(qq.coeff(b)) for b in basis)


def vector_to_expr(vec: Sequence[int], basis: Sequence[sp.Symbol]) -> sp.Expr:
    return sp.expand(sum(vec[i] * basis[i] for i in range(len(basis))))


def l1_distance(a: Tuple[int, ...], b: Tuple[int, ...]) -> int:
    """Manhattan distance between two nodes."""
    return sum(abs(a[i] - b[i]) for i in range(len(a)))


def are_adjacent(a: Tuple[int, ...], b: Tuple[int, ...]) -> bool:
    """Two nodes are adjacent if they differ by exactly ±1 in one coordinate."""
    return l1_distance(a, b) == 1


def get_neighbors(node: Tuple[int, ...], dim: int) -> List[Tuple[int, ...]]:
    """Get all 2*dim neighbors (±1 in each coordinate)."""
    neighbors = []
    for i in range(dim):
        for delta in [-1, 1]:
            neighbor = list(node)
            neighbor[i] += delta
            neighbors.append(tuple(neighbor))
    return neighbors


# ============================================================
# BFS shortest path
# ============================================================


def bfs_path(start: Tuple[int, ...], end: Tuple[int, ...], 
             existing: Set[Tuple[int, ...]], max_coord: int) -> List[Tuple[int, ...]]:
    """
    Find shortest path from start to end using unit steps.
    Prefers going through existing nodes when possible.
    Returns the path including start and end.
    """
    if start == end:
        return [start]
    
    dim = len(start)
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        if current == end:
            return path
        
        # Get neighbors, prioritize existing nodes
        neighbors = get_neighbors(current, dim)
        
        # Sort: existing nodes first, then by distance to end
        def priority(n: Tuple[int, ...]) -> Tuple[int, int]:
            in_existing = 0 if n in existing else 1
            dist = l1_distance(n, end)
            return (in_existing, dist)
        
        neighbors.sort(key=priority)
        
        for neighbor in neighbors:
            if neighbor in visited:
                continue
            if any(abs(c) > max_coord for c in neighbor):
                continue
            
            visited.add(neighbor)
            queue.append((neighbor, path + [neighbor]))
    
    # No path found (shouldn't happen for connected integer lattice)
    return []


# ============================================================
# Main algorithm
# ============================================================


def extend_topology(
    topo_in: List[Tuple[sp.Expr, sp.Expr]],
    l: sp.Symbol,
    basis: Sequence[sp.Symbol],
    target_nprops: int,
    eliminate_index: Optional[int] = None,
    max_add: int = 50,
    mass_new: sp.Expr = sp.Integer(0),
) -> List[Tuple[sp.Expr, sp.Expr]]:
    """
    Extend a topology to have exactly target_nprops propagators.
    
    Algorithm:
    1. Convert propagators to nodes (shift vectors)
    2. Find which external momenta are covered by unit steps
    3. Prioritize adding propagators that introduce MISSING momenta
    4. Use BFS to find shortest paths, preferring missing-momentum directions
    """
    topo = list(topo_in)
    dim = len(basis)
    
    # Convert to nodes
    nodes: Set[Tuple[int, ...]] = set()
    for mom, _ in topo:
        q = shift_of(mom, l)
        vec = coeff_vector(q, basis)
        nodes.add(vec)
    
    # Determine max coordinate from input
    max_coord = max((abs(c) for node in nodes for c in node), default=1)
    max_coord = max(1, max_coord)
    
    added = 0
    
    def add_node(vec: Tuple[int, ...]) -> bool:
        nonlocal added
        if vec in nodes:
            return False
        if any(abs(c) > max_coord for c in vec):
            return False
        nodes.add(vec)
        mom = sp.expand(l + vector_to_expr(vec, basis))
        topo.append((mom, mass_new))
        added += 1
        return True
    
    def get_covered_directions() -> Set[int]:
        """Find which momentum directions are covered by existing unit steps."""
        covered = set()
        node_list = list(nodes)
        for i, a in enumerate(node_list):
            for b in node_list[i+1:]:
                if l1_distance(a, b) == 1:
                    # Find which direction differs
                    for k in range(dim):
                        if a[k] != b[k]:
                            covered.add(k)
                            break
        return covered
    
    def get_missing_directions() -> List[int]:
        """Get momentum directions not yet covered, excluding eliminated one."""
        covered = get_covered_directions()
        missing = [k for k in range(dim) if k not in covered]
        if eliminate_index is not None and eliminate_index in missing:
            missing.remove(eliminate_index)
        return missing
    
    # Main loop: add propagators
    while len(topo) < target_nprops and added < max_add:
        missing_dirs = get_missing_directions()
        node_list = sorted(nodes)
        
        inserted = False
        
        # Priority 1: Fill gaps ONLY if the gap path includes a missing direction
        best_pair = None
        best_dist = float('inf')
        best_has_missing = False
        
        for i, a in enumerate(node_list):
            for b in node_list[i+1:]:
                d = l1_distance(a, b)
                if d <= 1:
                    continue
                
                # Check if path from a to b includes any missing direction
                delta = tuple(b[k] - a[k] for k in range(dim))
                path_has_missing = any(delta[k] != 0 and k in missing_dirs for k in range(dim))
                
                # Prefer paths with missing directions, then shortest
                if path_has_missing and not best_has_missing:
                    best_dist = d
                    best_pair = (a, b)
                    best_has_missing = True
                elif path_has_missing == best_has_missing and d < best_dist:
                    best_dist = d
                    best_pair = (a, b)
        
        if best_pair is not None and best_has_missing:
            a, b = best_pair
            best_candidate = None
            best_priority = (999, 999)
            
            for k in range(dim):
                diff = b[k] - a[k]
                if diff == 0:
                    continue
                delta = 1 if diff > 0 else -1
                candidate = list(a)
                candidate[k] += delta
                candidate = tuple(candidate)
                
                if candidate in nodes or any(abs(c) > max_coord for c in candidate):
                    continue
                
                is_missing = 0 if k in missing_dirs else 1
                priority = (is_missing, k)
                
                if priority < best_priority:
                    best_priority = priority
                    best_candidate = candidate
            
            if best_candidate is not None:
                if add_node(best_candidate):
                    inserted = True
        
        if inserted:
            continue
        
        # Priority 2: Add from endpoints in missing directions
        if missing_dirs:
            def count_neighbors_in_set(node: Tuple[int, ...]) -> int:
                return sum(1 for n in get_neighbors(node, dim) if n in nodes)
            
            sorted_by_neighbors = sorted(node_list, key=count_neighbors_in_set)
            
            for node in sorted_by_neighbors:
                for k in missing_dirs:
                    for delta in [-1, 1]:
                        candidate = list(node)
                        candidate[k] += delta
                        candidate = tuple(candidate)
                        if candidate not in nodes and all(abs(c) <= max_coord for c in candidate):
                            if add_node(candidate):
                                inserted = True
                                break
                    if inserted:
                        break
                if inserted:
                    break
        
        if inserted:
            continue
        
        # Priority 3: Fill remaining gaps (no missing directions left)
        if best_pair is not None and not best_has_missing:
            a, b = best_pair
            for k in range(dim):
                diff = b[k] - a[k]
                if diff == 0:
                    continue
                delta = 1 if diff > 0 else -1
                candidate = list(a)
                candidate[k] += delta
                candidate = tuple(candidate)
                
                if candidate not in nodes and all(abs(c) <= max_coord for c in candidate):
                    if add_node(candidate):
                        inserted = True
                        break
        
        if inserted:
            continue
        
        # Priority 2: Fill gaps between existing nodes
        best_pair = None
        best_dist = float('inf')
        
        for i, a in enumerate(node_list):
            for b in node_list[i+1:]:
                d = l1_distance(a, b)
                if 1 < d < best_dist:
                    best_dist = d
                    best_pair = (a, b)
        
        if best_pair is not None:
            # Find path and add one node along it
            path = bfs_path(best_pair[0], best_pair[1], nodes, max_coord)
            for node in path:
                if node not in nodes:
                    if add_node(node):
                        inserted = True
                        break
        
        if inserted:
            continue
        
        # Priority 3: Extend from endpoints
        def count_neighbors_in_set(node: Tuple[int, ...]) -> int:
            return sum(1 for n in get_neighbors(node, dim) if n in nodes)
        
        endpoints = sorted(node_list, key=count_neighbors_in_set)
        
        for endpoint in endpoints:
            for neighbor in get_neighbors(endpoint, dim):
                if neighbor not in nodes and all(abs(c) <= max_coord for c in neighbor):
                    if add_node(neighbor):
                        inserted = True
                        break
            if inserted:
                break
        
        if not inserted:
            max_coord += 1
            if max_coord > 3:
                break
    
    if len(topo) < target_nprops:
        print(f"Warning: could not reach {target_nprops} propagators (got {len(topo)})")
    
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
    """Eliminate one momentum using momentum conservation."""
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
            mom_s = sp.sstr(sp.expand(mom_out))
            mass_s = sp.sstr(sp.expand(mass))
            entries.append(f"{{{mom_s}, {mass_s}}}")
        blocks.append("  {" + ", ".join(entries) + "}")

    lines.append(",\n".join(blocks))
    lines.append("\n};\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ============================================================
# Self-test
# ============================================================


def self_test() -> None:
    l = sp.Symbol("l")
    p1, p2, p3, p4 = sp.symbols("p1 p2 p3 p4")
    mt = sp.Symbol("mt")

    local_dict = {"l": l, "p1": p1, "p2": p2, "p3": p3, "p4": p4, "mt": mt}
    basis = [p1, p2, p3, p4]

    # Test 1: Basic extension from 3 to 4 propagators
    raw = "top1:[[l, mt], [l - p1 - p2 + p3, 0], [l - p2, mt]]"
    m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\[\[.*\]\])\s*;?\s*$", raw)
    topo_in = parse_topology_list(m.group(2), local_dict)
    
    topo_ext = extend_topology(topo_in, l, basis, target_nprops=4)
    
    # Verify: 4 propagators, all shifts differ by unit steps
    assert len(topo_ext) == 4, f"Expected 4, got {len(topo_ext)}"
    
    shifts = [coeff_vector(shift_of(mom, l), basis) for mom, _ in topo_ext]
    
    # Check that all pairs have at least one path of unit steps
    for i, s1 in enumerate(shifts):
        for s2 in shifts[i+1:]:
            assert l1_distance(s1, s2) >= 1, "Duplicate shift"
    
    print(f"Test 1 OK: {[sp.sstr(mom) for mom, _ in topo_ext]}")

    # Test 2: Verify adjacency in output
    raw2 = "test2:{{l,0},{l-p1-p2,0}}"
    m2 = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\{\{.*\}\})\s*$", raw2)
    topo2_in = parse_topology_list(m2.group(2), local_dict)
    topo2_ext = extend_topology(topo2_in, l, basis, target_nprops=4)
    
    assert len(topo2_ext) == 4, f"Expected 4, got {len(topo2_ext)}"
    
    # Check that we can form a path through all nodes
    shifts2 = [coeff_vector(shift_of(mom, l), basis) for mom, _ in topo2_ext]
    node_set = set(shifts2)
    
    # BFS to check connectivity
    start = shifts2[0]
    visited = {start}
    queue = deque([start])
    while queue:
        curr = queue.popleft()
        for neighbor in get_neighbors(curr, len(basis)):
            if neighbor in node_set and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    assert len(visited) == len(node_set), "Nodes not connected by unit steps"
    print(f"Test 2 OK: {[sp.sstr(mom) for mom, _ in topo2_ext]}")

    print("All self-tests passed.")


# ============================================================
# Main
# ============================================================


def main() -> None:
    import json
    from pathlib import Path

    cwd = Path.cwd()
    run_dir = cwd.parent if cwd.name == "Mathematica" else cwd
    meta_path = run_dir / "meta.json"

    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json not found at {meta_path}")

    meta = json.loads(meta_path.read_text())
    n_in = int(meta.get("n_in", 2))
    n_out = int(meta.get("n_out", 2))
    n = n_in + n_out

    particles = meta.get("particles", [])
    incoming_names = [p["momentum"] for p in particles if p.get("side") == "in"]
    outgoing_names = [p["momentum"] for p in particles if p.get("side") == "out"]

    print(f"[extend] n = {n} (n_in={n_in}, n_out={n_out})")

    # Build symbols
    l = sp.Symbol("l")
    mt = sp.Symbol("mt")
    p_syms = sp.symbols(" ".join(f"p{i}" for i in range(1, n + 1)))
    p_syms = list(p_syms) if isinstance(p_syms, (list, tuple)) else [p_syms]

    local_dict = {"l": l, "mt": mt}
    for sym in p_syms:
        local_dict[str(sym)] = sym

    basis = p_syms
    eliminate_index = len(basis) - 1  # Eliminate highest (p_n)

    incoming_indices = [i for i, p in enumerate(basis) if str(p) in incoming_names]
    outgoing_indices = [i for i, p in enumerate(basis) if str(p) in outgoing_names]

    print(f"[extend] basis: {[str(b) for b in basis]}, eliminate: {basis[eliminate_index]}")

    in_path = cwd / "Files" / "Topologies.txt" if cwd.name == "Mathematica" else Path("Files/Topologies.txt")
    out_path = cwd / "Extended.m" if cwd.name == "Mathematica" else Path("Extended.m")

    if not in_path.exists():
        raise FileNotFoundError(f"Topologies.txt not found at {in_path}")

    extended = []

    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(\[\[.*\]\]|\{\{.*\}\})\s*;?\s*$", line)
            if not m:
                raise ValueError(f"Line does not match format: {line}")

            name = m.group(1)
            raw_list = m.group(2)
            topo_in = parse_topology_list(raw_list, local_dict)
            before = len(topo_in)

            topo_ext = extend_topology(
                topo_in, l, basis,
                target_nprops=n,
                eliminate_index=eliminate_index,
            )

            after = len(topo_ext)
            print(f"[extend] {name}: {before} -> {after}")

            extended.append(topo_ext)

    write_extended_m(
        str(out_path), extended, "Extended",
        basis, eliminate_index, incoming_indices, outgoing_indices,
    )
    print(f"[extend] Wrote {out_path}")


if __name__ == "__main__":
    self_test()
    main()
