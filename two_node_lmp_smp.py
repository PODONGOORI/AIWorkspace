"""
Two-node power system: LMP (nodal) vs. SMP (system) comparison
==============================================================

A minimal, dependency-free model of a 2-bus power network used to illustrate
the difference between Locational Marginal Prices (지점별 한계가격, LMP) and the
single System Marginal Price (계통한계가격, SMP) used in Korea's CBP pool market.

Topology
--------

        f (MW)
   [Node 1] ----||---- [Node 2]      line limit: |f| <= Fmax
      |  Gen G1            |  Gen G2
      |  Load D1           |  Load D2

Each node has one generator and one load. The two nodes are joined by a single
lossless transmission line whose power flow f (from node 1 -> node 2) is
limited to [-Fmax, +Fmax].

Generator cost
--------------
Each generator i has a quadratic cost  C_i(g) = a_i*g + 0.5*b_i*g^2  on
0 <= g <= Pmax_i, so its marginal cost is  MC_i(g) = a_i + b_i*g.
Setting b_i = 0 gives a constant marginal cost (a flat merit-order block).

Pricing
-------
* SMP  : solve the *unconstrained* (copper-plate) economic dispatch, ignoring
         the line limit. The common marginal cost that balances the whole
         system is the single System Marginal Price. This is how Korea's pool
         currently prices energy (one number for the whole grid).
* LMP_i: solve the *constrained* DC optimal power flow with the line limit.
         The marginal cost of serving load at node i is that node's LMP. When
         the line congests, LMP_1 != LMP_2 and a congestion rent appears.

Run:  python3 two_node_lmp_smp.py
"""

from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Generator:
    name: str
    a: float        # linear cost coefficient ($/MWh)
    b: float        # quadratic cost coefficient ($/MWh per MW); 0 => flat MC
    pmax: float     # capacity (MW); pmin assumed 0

    def mc(self, g: float) -> float:
        """Marginal cost at output g."""
        return self.a + self.b * g


@dataclass
class Node:
    name: str
    gen: Generator
    load: float     # demand (MW)


@dataclass
class TwoNodeSystem:
    n1: Node
    n2: Node
    fmax: float     # transmission line thermal limit (MW), node1 -> node2


# --------------------------------------------------------------------------- #
# Solver helpers (1-D convex optimisation, no external libraries)
# --------------------------------------------------------------------------- #
def _gen_cost(gen: Generator, g: float) -> float:
    """Total cost C(g) = a*g + 0.5*b*g^2."""
    return gen.a * g + 0.5 * gen.b * g * g


def _solve_unconstrained(g1g, g2g, demand):
    """Copper-plate dispatch: min C1(g1)+C2(g2) s.t. g1+g2 = demand, caps.

    Returns (g1, g2, total_cost). The single balancing marginal price is found
    by bisection on lambda; outputs are read back as MC(g)=lambda clipped to
    capacity, with the tie split to exactly meet demand (handles flat MC).
    """
    def dispatch(lam):
        out = []
        for gen in (g1g, g2g):
            if gen.b > 0:
                g = (lam - gen.a) / gen.b
            else:                       # flat MC: off below price, full above
                g = gen.pmax if lam > gen.a else 0.0
            out.append(min(max(g, 0.0), gen.pmax))
        return out

    lo = min(g1g.a, g2g.a)
    hi = max(g1g.a, g2g.a) + max(g1g.b, g2g.b) * demand + 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if sum(dispatch(mid)) < demand:
            lo = mid
        else:
            hi = mid
    g1, g2 = dispatch(0.5 * (lo + hi))
    # Re-balance any flat-MC tie so generation exactly equals demand.
    slack = demand - (g1 + g2)
    if slack > 0:
        room1, room2 = g1g.pmax - g1, g2g.pmax - g2
        add1 = min(room1, slack) if g1g.a <= g2g.a else max(0.0, slack - room2)
        g1 += add1
        g2 += slack - add1
    return g1, g2, _gen_cost(g1g, g1) + _gen_cost(g2g, g2)


def _solve_constrained(g1g, g2g, d1, d2, fmax):
    """DC-OPF with line limit. Returns (g1, g2, flow, total_cost).

    Lossless 2-bus network: f = g1 - D1 and g2 = (D1+D2) - g1, so the problem is
    a 1-D convex minimisation over g1 on a feasible interval bounded by the
    generator caps and the line limit |g1 - D1| <= Fmax.
    """
    demand = d1 + d2
    lo = max(0.0, demand - g2g.pmax, d1 - fmax)
    hi = min(g1g.pmax, demand, d1 + fmax)
    if lo > hi + 1e-9:
        raise ValueError("Infeasible: cannot serve load within line/cap limits.")

    # d/dg1 [C1(g1) + C2(demand - g1)] = MC1(g1) - MC2(demand - g1); increasing.
    def dcost(g1):
        return g1g.mc(g1) - g2g.mc(demand - g1)

    if dcost(lo) >= 0:
        g1 = lo
    elif dcost(hi) <= 0:
        g1 = hi
    else:
        a, b = lo, hi
        for _ in range(200):
            m = 0.5 * (a + b)
            if dcost(m) < 0:
                a = m
            else:
                b = m
        g1 = 0.5 * (a + b)

    g2 = demand - g1
    return g1, g2, g1 - d1, _gen_cost(g1g, g1) + _gen_cost(g2g, g2)


# Perturbation step for finite-difference marginal prices (MW).
_EPS = 1e-4


def unconstrained_dispatch(sys: TwoNodeSystem):
    """Copper-plate dispatch -> (g1, g2, SMP).

    SMP = d(total cost)/d(total demand), the single system-wide marginal price.
    """
    g1g, g2g = sys.n1.gen, sys.n2.gen
    demand = sys.n1.load + sys.n2.load
    g1, g2, cost = _solve_unconstrained(g1g, g2g, demand)
    _, _, cost_up = _solve_unconstrained(g1g, g2g, demand + _EPS)
    smp = (cost_up - cost) / _EPS
    return g1, g2, smp


def constrained_dispatch(sys: TwoNodeSystem):
    """DC-OPF with the line limit -> dispatch, flow, LMPs, congestion info.

    Each LMP_i is the true marginal cost of serving one more MW of load at node
    i, computed as d(total cost)/d(D_i) by finite difference. This stays correct
    even when a node's generator is at a bound (e.g. an uncongested line lets the
    other node's generator set the price at both buses).
    """
    g1g, g2g = sys.n1.gen, sys.n2.gen
    d1, d2 = sys.n1.load, sys.n2.load

    g1, g2, flow, cost = _solve_constrained(g1g, g2g, d1, d2, sys.fmax)
    _, _, _, cost_d1 = _solve_constrained(g1g, g2g, d1 + _EPS, d2, sys.fmax)
    _, _, _, cost_d2 = _solve_constrained(g1g, g2g, d1, d2 + _EPS, sys.fmax)
    lmp1 = (cost_d1 - cost) / _EPS
    lmp2 = (cost_d2 - cost) / _EPS

    congested = abs(abs(flow) - sys.fmax) < 1e-6
    return {
        "g1": g1, "g2": g2, "flow": flow,
        "lmp1": lmp1, "lmp2": lmp2,
        "congested": congested,
        # Congestion rent collected by the market operator = flow * price spread.
        "congestion_rent": flow * (lmp2 - lmp1),
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def report(title, sys: TwoNodeSystem):
    g1u, g2u, smp = unconstrained_dispatch(sys)
    c = constrained_dispatch(sys)

    print("=" * 68)
    print(title)
    print("=" * 68)
    print(f"  Node 1: gen MC = {sys.n1.gen.a:g} + {sys.n1.gen.b:g}*g  "
          f"(Pmax {sys.n1.gen.pmax:g} MW),  load {sys.n1.load:g} MW")
    print(f"  Node 2: gen MC = {sys.n2.gen.a:g} + {sys.n2.gen.b:g}*g  "
          f"(Pmax {sys.n2.gen.pmax:g} MW),  load {sys.n2.load:g} MW")
    print(f"  Line limit Fmax = {sys.fmax:g} MW (node1 -> node2)")
    print(f"  Total demand    = {sys.n1.load + sys.n2.load:g} MW")
    print("-" * 68)
    print("  Unconstrained dispatch (copper plate) -> SMP")
    print(f"    g1 = {g1u:7.2f} MW   g2 = {g2u:7.2f} MW")
    print(f"    SMP = {smp:.2f} $/MWh   (single system-wide price)")
    print("-" * 68)
    print("  Constrained DC-OPF (line limit enforced) -> LMP")
    print(f"    g1 = {c['g1']:7.2f} MW   g2 = {c['g2']:7.2f} MW   "
          f"flow = {c['flow']:7.2f} MW")
    print(f"    LMP_node1 = {c['lmp1']:.2f} $/MWh")
    print(f"    LMP_node2 = {c['lmp2']:.2f} $/MWh")
    print(f"    Line congested? {'YES' if c['congested'] else 'no'}")
    if c["congested"]:
        print(f"    LMP spread (node2 - node1) = {c['lmp2'] - c['lmp1']:.2f} $/MWh")
        print(f"    Congestion rent            = {c['congestion_rent']:.2f} $/h")
    print("-" * 68)
    print("  LMP vs SMP")
    print(f"    SMP        = {smp:.2f} $/MWh   (what every node pays today)")
    print(f"    LMP_node1  = {c['lmp1']:.2f} $/MWh   "
          f"(diff vs SMP: {c['lmp1'] - smp:+.2f})")
    print(f"    LMP_node2  = {c['lmp2']:.2f} $/MWh   "
          f"(diff vs SMP: {c['lmp2'] - smp:+.2f})")
    if not c["congested"]:
        print("    => Line uncongested: LMP_1 = LMP_2 = SMP. Locational and")
        print("       system prices coincide.")
    else:
        cheap = "node1" if c["lmp1"] < c["lmp2"] else "node2"
        exp = "node2" if cheap == "node1" else "node1"
        print(f"    => Congestion splits the price: {cheap} (export/cheap side)")
        print(f"       is below SMP, {exp} (import/scarce side) is above. The")
        print("       uniform SMP masks this locational scarcity signal.")
    print()


# --------------------------------------------------------------------------- #
# Scenarios
# --------------------------------------------------------------------------- #
def main():
    # Node 1 hosts a cheap, large generator; node 2 a costly one.
    g1_cheap = Generator(name="G1 (cheap baseload)", a=20.0, b=0.0, pmax=200.0)
    g2_exp = Generator(name="G2 (peaker)",          a=50.0, b=0.0, pmax=150.0)

    # Scenario A: roomy line -> no congestion. LMP = SMP everywhere.
    sysA = TwoNodeSystem(
        n1=Node("Bus1", g1_cheap, load=50.0),
        n2=Node("Bus2", g2_exp,   load=100.0),
        fmax=120.0,
    )
    report("Scenario A  -  Uncongested line (Fmax = 120 MW)", sysA)

    # Scenario B: same system, tight line -> congestion. LMPs diverge.
    sysB = TwoNodeSystem(
        n1=Node("Bus1", g1_cheap, load=50.0),
        n2=Node("Bus2", g2_exp,   load=100.0),
        fmax=60.0,
    )
    report("Scenario B  -  Congested line (Fmax = 60 MW), flat MC", sysB)

    # Scenario C: quadratic (smooth) cost curves + congestion. Now SMP lies
    # strictly *between* the two LMPs - both generators are marginal.
    g1_q = Generator(name="G1 (quadratic)", a=15.0, b=0.10, pmax=200.0)
    g2_q = Generator(name="G2 (quadratic)", a=25.0, b=0.20, pmax=200.0)
    sysC = TwoNodeSystem(
        n1=Node("Bus1", g1_q, load=80.0),
        n2=Node("Bus2", g2_q, load=120.0),
        fmax=30.0,
    )
    report("Scenario C  -  Congested line + quadratic costs (SMP between LMPs)",
           sysC)


if __name__ == "__main__":
    main()
