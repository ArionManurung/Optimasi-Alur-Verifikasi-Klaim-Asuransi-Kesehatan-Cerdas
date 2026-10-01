"""
Root level wrapper for Milestone 2 solver module.
Enables imports such as:
    from solver import CSPSolver, GASolver
"""

from src.tugas02_milestone2.solver import CSPSolver, GASolver
from src.tugas02_milestone2.domain import (
    Staff,
    Shift,
    ClaimStage,
    ScheduleVariable,
    Constraint,
    ProblemDefinition,
    generate_allianz_problem_small,
    generate_allianz_problem_large,
)

__all__ = [
    "CSPSolver",
    "GASolver",
    "Staff",
    "Shift",
    "ClaimStage",
    "ScheduleVariable",
    "Constraint",
    "ProblemDefinition",
    "generate_allianz_problem_small",
    "generate_allianz_problem_large",
]
