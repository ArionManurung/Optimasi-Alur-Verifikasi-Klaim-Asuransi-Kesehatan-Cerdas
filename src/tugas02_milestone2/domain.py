"""
Formal Domain Modeling for Allianz Health Insurance Claim Verification Scheduling
Constraint Satisfaction Problem (CSP) & Genetic Algorithm (GA) Optimization
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Any, Optional
import math


# Qualifications / Skill Certifications
QUAL_CHECK_POLIS = "Polis_Verification_Cert"
QUAL_MED_REVIEW = "Medical_Reviewer_Cert"
QUAL_FRAUD_AUDIT = "Fraud_Audit_Cert"
QUAL_APPROVAL = "Senior_Approval_Cert"

STAGE_QUALIFICATIONS = {
    "Cek_Polis": QUAL_CHECK_POLIS,
    "Verifikasi_RS": QUAL_MED_REVIEW,
    "Audit_Fraud": QUAL_FRAUD_AUDIT,
    "Persetujuan": QUAL_APPROVAL,
}


@dataclass(frozen=True)
class Shift:
    name: str  # Pagi, Siang, Malam
    hours: str = "08.00 - 16.00"


@dataclass(frozen=True)
class ClaimStage:
    name: str
    required_qualification: str



@dataclass(frozen=True)
class Staff:
    id: str
    name: str
    qualifications: Set[str]
    max_shifts_per_week: int = 5
    preferred_shift: Optional[str] = None  # e.g., 'Pagi', 'Siang', 'Malam'

    def has_qualification(self, qual: str) -> bool:
        return qual in self.qualifications


@dataclass(frozen=True)
class ScheduleVariable:
    stage: str      # Cek_Polis, Verifikasi_RS, Audit_Fraud, Persetujuan
    day: int        # 1..D
    shift: str      # Pagi, Siang, Malam

    @property
    def key(self) -> str:
        return f"{self.stage}_D{self.day}_{self.shift}"

    def __str__(self) -> str:
        return self.key


@dataclass
class Constraint:
    name: str
    variables: List[ScheduleVariable]
    is_hard: bool = True

    def is_satisfied(self, assignment: Dict[ScheduleVariable, Staff]) -> bool:
        """Evaluates whether assignment satisfies this constraint."""
        raise NotImplementedError


class QualificationConstraint(Constraint):
    """Hard Constraint: Staff assigned to stage must possess required qualification."""
    def __init__(self, var: ScheduleVariable):
        super().__init__(
            name=f"QualCheck_{var.key}",
            variables=[var],
            is_hard=True
        )
        self.var = var

    def is_satisfied(self, assignment: Dict[ScheduleVariable, Staff]) -> bool:
        if self.var not in assignment:
            return True  # Unassigned variable cannot violate constraint
        staff = assignment[self.var]
        required_qual = STAGE_QUALIFICATIONS.get(self.var.stage)
        if required_qual:
            return staff.has_qualification(required_qual)
        return True


class ShiftExclusivityConstraint(Constraint):
    """Hard Constraint: A staff member cannot work two different stages in the same (day, shift)."""
    def __init__(self, var1: ScheduleVariable, var2: ScheduleVariable):
        super().__init__(
            name=f"Exclusivity_{var1.key}_{var2.key}",
            variables=[var1, var2],
            is_hard=True
        )
        self.var1 = var1
        self.var2 = var2

    def is_satisfied(self, assignment: Dict[ScheduleVariable, Staff]) -> bool:
        if self.var1 not in assignment or self.var2 not in assignment:
            return True
        return assignment[self.var1].id != assignment[self.var2].id


class RestPeriodConstraint(Constraint):
    """Hard Constraint: Night shift on day D cannot be followed by Morning shift on day D+1."""
    def __init__(self, night_var: ScheduleVariable, morning_var: ScheduleVariable):
        super().__init__(
            name=f"RestPeriod_{night_var.key}_{morning_var.key}",
            variables=[night_var, morning_var],
            is_hard=True
        )
        self.night_var = night_var
        self.morning_var = morning_var

    def is_satisfied(self, assignment: Dict[ScheduleVariable, Staff]) -> bool:
        if self.night_var not in assignment or self.morning_var not in assignment:
            return True
        return assignment[self.night_var].id != assignment[self.morning_var].id


class MaxWorkloadConstraint(Constraint):
    """Hard Constraint: A staff member cannot exceed their maximum weekly shift limit."""
    def __init__(self, all_vars: List[ScheduleVariable], staff: Staff):
        super().__init__(
            name=f"MaxWorkload_{staff.id}",
            variables=all_vars,
            is_hard=True
        )
        self.staff = staff

    def is_satisfied(self, assignment: Dict[ScheduleVariable, Staff]) -> bool:
        assigned_count = sum(
            1 for v in self.variables
            if v in assignment and assignment[v].id == self.staff.id
        )
        return assigned_count <= self.staff.max_shifts_per_week


@dataclass
class ProblemDefinition:
    """Formal CSP / GA Problem Instance container."""
    variables: List[ScheduleVariable]
    domains: Dict[ScheduleVariable, List[Staff]]
    constraints: List[Constraint]
    all_staff: List[Staff]
    days: int
    shifts: List[str]
    stages: List[str]

    def validate_assignment(self, assignment: Dict[ScheduleVariable, Staff]) -> Tuple[bool, int, List[str]]:
        """
        Validates an assignment against all hard constraints.
        Returns: (is_valid, hard_violations_count, violation_details)
        """
        violations = []
        count = 0
        for c in self.constraints:
            if c.is_hard and not c.is_satisfied(assignment):
                count += 1
                violations.append(f"Violation [{c.name}]")
        return count == 0, count, violations

    def calculate_fitness(self, assignment: Dict[ScheduleVariable, Staff]) -> float:
        """
        Calculates fitness score for GA evaluation:
        Base score = 1000
        Penalty per hard constraint violation = 500
        Soft constraint bonuses for shift preference & workload fairness.
        """
        is_valid, hard_violations, _ = self.validate_assignment(assignment)
        score = 1000.0 - (hard_violations * 250.0)

        # Soft Constraint 1: Shift preference bonus (+10 per preferred shift match)
        pref_bonus = 0.0
        staff_shift_counts: Dict[str, int] = {s.id: 0 for s in self.all_staff}

        for var, staff in assignment.items():
            staff_shift_counts[staff.id] += 1
            if staff.preferred_shift and staff.preferred_shift == var.shift:
                pref_bonus += 10.0

        # Soft Constraint 2: Workload fairness (penalty for high variance in shift distribution)
        counts = list(staff_shift_counts.values())
        mean_cnt = sum(counts) / max(1, len(counts))
        variance = sum((c - mean_cnt) ** 2 for c in counts) / max(1, len(counts))
        fairness_penalty = variance * 5.0

        fitness = score + pref_bonus - fairness_penalty
        return max(0.0, fitness)


def generate_allianz_problem_small() -> ProblemDefinition:
    """
    Generates a Small-Scale Allianz Claim Scheduling Problem:
    - 3 Days (D1..D3)
    - 2 Shifts: Pagi, Siang
    - 4 Stages: Cek_Polis, Verifikasi_RS, Audit_Fraud, Persetujuan
    - Total Variables = 3 * 2 * 4 = 24 variables
    - Staff Pool = 8 verifiers with diverse qualifications
    """
    days = 3
    shifts = ["Pagi", "Siang"]
    stages = ["Cek_Polis", "Verifikasi_RS", "Audit_Fraud", "Persetujuan"]

    staff_pool = [
        Staff("E01", "Budi (Senior Fraud & Polis)", {QUAL_CHECK_POLIS, QUAL_FRAUD_AUDIT, QUAL_APPROVAL}, max_shifts_per_week=4, preferred_shift="Pagi"),
        Staff("E02", "Dr. Siti (Medical & RS)", {QUAL_MED_REVIEW, QUAL_CHECK_POLIS}, max_shifts_per_week=5, preferred_shift="Pagi"),
        Staff("E03", "Andi (Fraud Audit Spec)", {QUAL_FRAUD_AUDIT, QUAL_CHECK_POLIS}, max_shifts_per_week=4, preferred_shift="Siang"),
        Staff("E04", "Dr. Agus (Chief Medical)", {QUAL_MED_REVIEW, QUAL_APPROVAL, QUAL_CHECK_POLIS}, max_shifts_per_week=4, preferred_shift="Pagi"),
        Staff("E05", "Dewi (General Verifier)", {QUAL_CHECK_POLIS}, max_shifts_per_week=5, preferred_shift="Siang"),
        Staff("E06", "Eko (Senior Manager)", {QUAL_APPROVAL, QUAL_CHECK_POLIS, QUAL_FRAUD_AUDIT}, max_shifts_per_week=3, preferred_shift="Pagi"),
        Staff("E07", "Dr. Rina (RS Reviewer)", {QUAL_MED_REVIEW}, max_shifts_per_week=4, preferred_shift="Siang"),
        Staff("E08", "Fajar (Audit & Polis)", {QUAL_FRAUD_AUDIT, QUAL_CHECK_POLIS}, max_shifts_per_week=5, preferred_shift="Siang"),
    ]

    variables: List[ScheduleVariable] = []
    domains: Dict[ScheduleVariable, List[Staff]] = {}

    for d in range(1, days + 1):
        for s in shifts:
            for stg in stages:
                var = ScheduleVariable(stage=stg, day=d, shift=s)
                variables.append(var)
                # Domain pruning initially based on stage qualification
                req_qual = STAGE_QUALIFICATIONS[stg]
                eligible_staff = [st for st in staff_pool if st.has_qualification(req_qual)]
                domains[var] = eligible_staff

    constraints: List[Constraint] = []

    # 1. Qualification constraints
    for var in variables:
        constraints.append(QualificationConstraint(var))

    # 2. Shift exclusivity constraints for same day & shift across different stages
    by_day_shift: Dict[Tuple[int, str], List[ScheduleVariable]] = {}
    for var in variables:
        key = (var.day, var.shift)
        by_day_shift.setdefault(key, []).append(var)

    for (d, s), var_list in by_day_shift.items():
        for i in range(len(var_list)):
            for j in range(i + 1, len(var_list)):
                constraints.append(ShiftExclusivityConstraint(var_list[i], var_list[j]))

    # 3. Max workload constraints
    for st in staff_pool:
        constraints.append(MaxWorkloadConstraint(variables, st))

    return ProblemDefinition(
        variables=variables,
        domains=domains,
        constraints=constraints,
        all_staff=staff_pool,
        days=days,
        shifts=shifts,
        stages=stages
    )


def generate_allianz_problem_large() -> ProblemDefinition:
    """
    Generates a Large-Scale Allianz Claim Scheduling Problem:
    - 7 Days (D1..D7)
    - 3 Shifts: Pagi, Siang, Malam
    - 4 Stages: Cek_Polis, Verifikasi_RS, Audit_Fraud, Persetujuan
    - Total Variables = 7 * 3 * 4 = 84 variables
    - Staff Pool = 24 verifiers
    """
    days = 7
    shifts = ["Pagi", "Siang", "Malam"]
    stages = ["Cek_Polis", "Verifikasi_RS", "Audit_Fraud", "Persetujuan"]

    staff_pool: List[Staff] = []
    # Build 24 diverse staff members
    for i in range(1, 25):
        quals = {QUAL_CHECK_POLIS}
        if i % 2 == 0:
            quals.add(QUAL_MED_REVIEW)
        if i % 3 == 0:
            quals.add(QUAL_FRAUD_AUDIT)
        if i % 4 == 0:
            quals.add(QUAL_APPROVAL)
        
        pref = ["Pagi", "Siang", "Malam"][i % 3]
        max_s = 5 if i % 5 != 0 else 4
        staff_pool.append(Staff(f"E{i:02d}", f"Staff_{i:02d}", quals, max_shifts_per_week=max_s, preferred_shift=pref))

    variables: List[ScheduleVariable] = []
    domains: Dict[ScheduleVariable, List[Staff]] = {}

    for d in range(1, days + 1):
        for s in shifts:
            for stg in stages:
                var = ScheduleVariable(stage=stg, day=d, shift=s)
                variables.append(var)
                req_qual = STAGE_QUALIFICATIONS[stg]
                eligible_staff = [st for st in staff_pool if st.has_qualification(req_qual)]
                domains[var] = eligible_staff

    constraints: List[Constraint] = []

    # 1. Qualification constraints
    for var in variables:
        constraints.append(QualificationConstraint(var))

    # 2. Shift Exclusivity constraints
    by_day_shift: Dict[Tuple[int, str], List[ScheduleVariable]] = {}
    for var in variables:
        by_day_shift.setdefault((var.day, var.shift), []).append(var)

    for (d, s), var_list in by_day_shift.items():
        for i in range(len(var_list)):
            for j in range(i + 1, len(var_list)):
                constraints.append(ShiftExclusivityConstraint(var_list[i], var_list[j]))

    # 3. Rest Period Constraint (Malam day D to Pagi day D+1)
    for d in range(1, days):
        malam_vars = [v for v in variables if v.day == d and v.shift == "Malam"]
        pagi_vars = [v for v in variables if v.day == d + 1 and v.shift == "Pagi"]
        for mv in malam_vars:
            for pv in pagi_vars:
                constraints.append(RestPeriodConstraint(mv, pv))

    # 4. Max workload constraints
    for st in staff_pool:
        constraints.append(MaxWorkloadConstraint(variables, st))

    return ProblemDefinition(
        variables=variables,
        domains=domains,
        constraints=constraints,
        all_staff=staff_pool,
        days=days,
        shifts=shifts,
        stages=stages
    )
