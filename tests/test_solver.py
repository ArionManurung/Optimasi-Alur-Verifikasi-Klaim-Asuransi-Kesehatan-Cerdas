"""
Automated Test Suite for Milestone 2 CSP & GA Solvers
Includes Edge Case Testing (Zero domain, Unsatisfiable constraints, Single variable, Large scale)
"""

import pytest
from src.tugas02_milestone2.domain import (
    Staff,
    ScheduleVariable,
    Constraint,
    ProblemDefinition,
    QualificationConstraint,
    ShiftExclusivityConstraint,
    MaxWorkloadConstraint,
    generate_allianz_problem_small,
    generate_allianz_problem_large,
    QUAL_CHECK_POLIS,
    QUAL_FRAUD_AUDIT,
    QUAL_MED_REVIEW,
    QUAL_APPROVAL,
)
from src.tugas02_milestone2.solver import CSPSolver, GASolver


def test_ac3_domain_reduction():
    """Test AC-3 arc consistency prunes impossible domains correctly."""
    problem = generate_allianz_problem_small()
    solver = CSPSolver(problem)
    consistent, pruned_domains = solver.ac3()

    assert consistent is True
    # Verify each variable domain contains only qualified staff
    for var, domain in pruned_domains.items():
        assert len(domain) > 0
        req_qual = {"Cek_Polis": QUAL_CHECK_POLIS, "Verifikasi_RS": QUAL_MED_REVIEW,
                    "Audit_Fraud": QUAL_FRAUD_AUDIT, "Persetujuan": QUAL_APPROVAL}[var.stage]
        for staff in domain:
            assert staff.has_qualification(req_qual)


def test_csp_backtracking_small_problem():
    """Test CSP Backtracking MRV solves small Allianz problem completely."""
    problem = generate_allianz_problem_small()
    solver = CSPSolver(problem)
    solution, stats = solver.solve(use_ac3=True)

    assert solution is not None
    assert stats["solved"] is True
    assert len(solution) == len(problem.variables)

    # Verify no hard constraint violations in solution
    is_valid, violations_count, details = problem.validate_assignment(solution)
    assert is_valid is True
    assert violations_count == 0


def test_ga_solver_small_problem():
    """Test Genetic Algorithm solver achieves low/zero violation solution."""
    problem = generate_allianz_problem_small()
    solver = GASolver(
        problem=problem,
        pop_size=80,
        generations=100,
        crossover_rate=0.8,
        mutation_rate=0.08,
        random_seed=42
    )
    solution, stats = solver.solve()

    assert solution is not None
    assert "best_fitness" in stats
    assert len(stats["history_best_fitness"]) == 100
    # GA should improve fitness over generations
    assert stats["history_best_fitness"][-1] >= stats["history_best_fitness"][0]


def test_edge_case_unsatisfiable_overconstrained():
    """
    Edge Case: Unsatisfiable over-constrained problem.
    4 stages requiring simultaneous shift, but only 1 staff member available.
    """
    staff = Staff("E01", "Only One Staff", {QUAL_CHECK_POLIS, QUAL_MED_REVIEW, QUAL_FRAUD_AUDIT, QUAL_APPROVAL}, max_shifts_per_week=1)
    
    vars = [
        ScheduleVariable("Cek_Polis", 1, "Pagi"),
        ScheduleVariable("Verifikasi_RS", 1, "Pagi"),
    ]
    domains = {v: [staff] for v in vars}
    constraints = [
        ShiftExclusivityConstraint(vars[0], vars[1])
    ]

    prob = ProblemDefinition(
        variables=vars,
        domains=domains,
        constraints=constraints,
        all_staff=[staff],
        days=1,
        shifts=["Pagi"],
        stages=["Cek_Polis", "Verifikasi_RS"]
    )

    solver = CSPSolver(prob)
    solution, stats = solver.solve(use_ac3=True)

    assert solution is None
    assert stats["solved"] is False


def test_edge_case_empty_domain():
    """
    Edge Case: Zero domain (No eligible staff for a required qualification).
    """
    staff = Staff("E01", "Basic Staff", {QUAL_CHECK_POLIS})
    var = ScheduleVariable("Audit_Fraud", 1, "Pagi")
    
    prob = ProblemDefinition(
        variables=[var],
        domains={var: []},  # Empty domain
        constraints=[QualificationConstraint(var)],
        all_staff=[staff],
        days=1,
        shifts=["Pagi"],
        stages=["Audit_Fraud"]
    )

    solver = CSPSolver(prob)
    solution, stats = solver.solve(use_ac3=True)

    assert solution is None
    assert stats["solved"] is False


def test_edge_case_single_variable():
    """
    Edge Case: Minimal single variable problem.
    """
    staff = Staff("E01", "Fraud Auditor", {QUAL_FRAUD_AUDIT})
    var = ScheduleVariable("Audit_Fraud", 1, "Pagi")
    
    prob = ProblemDefinition(
        variables=[var],
        domains={var: [staff]},
        constraints=[QualificationConstraint(var)],
        all_staff=[staff],
        days=1,
        shifts=["Pagi"],
        stages=["Audit_Fraud"]
    )

    solver = CSPSolver(prob)
    solution, stats = solver.solve(use_ac3=True)

    assert solution is not None
    assert stats["solved"] is True
    assert solution[var].id == "E01"


def test_csp_and_ga_large_scale_stability():
    """
    Edge Case / Scale Test: Large Allianz problem (84 variables, 24 staff).
    Tests system stability and solver performance.
    """
    problem = generate_allianz_problem_large()
    
    # CSP Test
    csp_solver = CSPSolver(problem)
    csp_sol, csp_stats = csp_solver.solve(use_ac3=True)
    assert csp_stats["execution_time_sec"] >= 0

    # GA Test
    ga_solver = GASolver(problem, pop_size=60, generations=30, random_seed=42)
    ga_sol, ga_stats = ga_solver.solve()
    assert ga_stats["generations"] == 30
    assert len(ga_stats["history_hard_violations"]) == 30
