# ============================================================
# Topology completion for 1-loop propagator lists
# Input/Output format: [(mom_expr, mass), ...]
# Example: [(l+p1,0), (l,mt), (l-p2,0), (l-p2+p3,mt)]
# ============================================================

import sympy as sp

# ---------- Core helpers ----------
def shift_of(mom, l):
    """Return q in (l+q) from mom expression."""
    return sp.expand(mom - l)

def vec(q, basis, rules):
    """Coefficient vector of q in the chosen external basis (after applying rules)."""
    qq = sp.expand(q.subs(rules))
    poly = sp.Poly(qq, *basis)
    return [poly.coeff_monomial(b) for b in basis]

def rank_of(vecs):
    if not vecs:
        return 0
    return sp.Matrix(vecs).rank()

def missing_dir(current_vecs, d, prefer_order=None):
    """
    Pick a unit direction e_k that increases rank (greedy).
    prefer_order: list of indices [0..d-1] controlling priority.
    """
    cr = rank_of(current_vecs)
    order = prefer_order if prefer_order is not None else list(range(d))
    for k in order:
        e = [0]*d
        e[k] = 1
        if rank_of(current_vecs + [e]) > cr:
            return e
    # fallback
    e = [0]*d
    e[order[0] if order else 0] = 1
    return e

def canonicalize(topo, l, rules, ref_index=None):
    """
    Shift loop momentum so that the chosen reference propagator becomes exactly 'l'
    (i.e., its shift q0 becomes 0). This makes the procedure routing-stable.
    """
    shifts = [shift_of(mom, l) for mom, _ in topo]

    if ref_index is None:
        # Prefer an exact {l, mass} propagator if present; else take first.
        ref_index = 0
        for i, (mom, _) in enumerate(topo):
            if sp.expand(mom - l) == 0:
                ref_index = i
                break

    q0 = sp.expand(shifts[ref_index].subs(rules))
    l_new = l - q0
    topo_new = [(sp.expand(mom.subs({l: l_new})), m) for mom, m in topo]
    return topo_new

# ---------- Main function ----------
def extend_topology(
    topo_in, l, basis, rules=None,
    anchor="last",
    mass_policy="massless",
    max_add=10,
    ref_index=None,
    prefer_dir_order=None,   # e.g. [0,1,2,3] or [2,3,0,1]
    anchor_fallback="all",   # "all" tries all existing nonzero anchors before zero
    mt_symbol=None           # optional: tell the function what symbol is "mt"
):
    """
    Extend a topology by adding propagators until the shifts span the chosen basis.

    topo_in: list of (mom_expr, mass)
    l: loop momentum symbol
    basis: list of basis symbols [p1, p2, ...] you want full span of
    rules: dict of momentum conservation substitutions (optional)
    anchor: "last" or "zero"
    mass_policy:
        - "massless": new propagators get mass 0
        - "copyLast": new propagators get mt if any mt present else last mass
        - callable(topo)->mass
    mt_symbol: needed only if you use mass_policy="copyLast" and want "mt detection"
    """
    rules = rules or {}

    # 1) Canonicalize routing
    topo = canonicalize(topo_in, l, rules, ref_index=ref_index)

    # 2) Existing shifts and vectors
    shifts = [shift_of(mom, l) for mom, _ in topo]
    vecs = [vec(q, basis, rules) for q in shifts]
    r = rank_of(vecs)

    seen = set(sp.expand(q.subs(rules)) for q in shifts)
    d = len(basis)

    def pick_mass():
        if callable(mass_policy):
            return mass_policy(topo)
        if mass_policy == "massless":
            return 0
        if mass_policy == "copyLast":
            masses = [m for _, m in topo]
            if mt_symbol is not None and mt_symbol in masses:
                return mt_symbol
            return masses[-1]
        return 0

    def anchor_candidates():
        if anchor == "zero":
            return [sp.Integer(0)]
        # last nonzero shift first
        nonzero = [sp.expand(q.subs(rules)) for q in shifts if sp.expand(q.subs(rules)) != 0]
        nonzero = list(dict.fromkeys(nonzero))   # unique, keep order
        nonzero = list(reversed(nonzero))        # last first
        if anchor_fallback == "all":
            return nonzero + [sp.Integer(0)]
        return (nonzero[:1] if nonzero else [sp.Integer(0)])

    add = 0
    while r < d and add < max_add:
        e = missing_dir(vecs, d, prefer_order=prefer_dir_order)
        direction = sum(e[i] * basis[i] for i in range(d))

        placed = False
        for anc in anchor_candidates():
            q_new = sp.expand((anc + direction).subs(rules))
            if q_new not in seen:
                mom_new = sp.expand(l + q_new)
                topo.append((mom_new, pick_mass()))
                shifts.append(q_new)
                vecs.append(vec(q_new, basis, rules))
                seen.add(q_new)
                r = rank_of(vecs)
                add += 1
                placed = True
                break

        if not placed:
            # Rare: couldn't add anything new; rotate preference order and try again
            if prefer_dir_order is not None and len(prefer_dir_order) > 1:
                prefer_dir_order = prefer_dir_order[1:] + prefer_dir_order[:1]
            else:
                break

    return topo
