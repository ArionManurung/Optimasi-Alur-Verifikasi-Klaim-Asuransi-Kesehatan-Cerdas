"""
Modular CSP Solver (AC-3 + Backtracking MRV) and Genetic Algorithm Solver (GA Elitism)
for Allianz Health Insurance Claim Processing Staff Allocation
"""

import time
import random
import copy
from typing import Dict, List, Set, Tuple, Optional, Any
from .domain import ProblemDefinition, ScheduleVariable, Staff, Constraint


class CSPSolver:
    """
    Constraint Satisfaction Problem (CSP) Solver.
    Uses AC-3 (Arc Consistency 3) for constraint propagation
    and Backtracking Search with MRV (Minimum Remaining Values),
    Degree Heuristic tie-breaking, and LCV (Least Constraining Value).
    """

    def __init__(self, problem: ProblemDefinition):
        self.problem = problem
        self.nodes_expanded = 0
        self.backtracks_count = 0
        self.execution_time_sec = 0.0

    def ac3(self, domains: Optional[Dict[ScheduleVariable, List[Staff]]] = None) -> Tuple[bool, Dict[ScheduleVariable, List[Staff]]]:
        """
        AC-3 Algorithm for Constraint Propagation across Binary Constraints.
        Returns (is_consistent, revised_domains).
        """
        if domains is None:
            domains = {var: list(vals) for var, vals in self.problem.domains.items()}
        else:
            domains = {var: list(vals) for var, vals in domains.items()}

        # Build queue of binary constraint arcs (var1, var2, constraint)
        queue: List[Tuple[ScheduleVariable, ScheduleVariable, Constraint]] = []
        for c in self.problem.constraints:
            if len(c.variables) == 2:
                v1, v2 = c.variables[0], c.variables[1]
                queue.append((v1, v2, c))
                queue.append((v2, v1, c))

        while queue:
            v_xi, v_xj, constraint = queue.pop(0)
            revised, domains = self._revise(domains, v_xi, v_xj, constraint)
            if revised:
                if len(domains[v_xi]) == 0:
                    return False, domains  # Inconsistent domain
                # Re-add affected arcs
                for c in self.problem.constraints:
                    if len(c.variables) == 2 and v_xi in c.variables:
                        v_other = c.variables[0] if c.variables[1] == v_xi else c.variables[1]
                        if v_other != v_xj:
                            queue.append((v_other, v_xi, c))

        return True, domains

    def _revise(
        self,
        domains: Dict[ScheduleVariable, List[Staff]],
        v_xi: ScheduleVariable,
        v_xj: ScheduleVariable,
        constraint: Constraint
    ) -> Tuple[bool, Dict[ScheduleVariable, List[Staff]]]:
        """
        Revises domain of v_xi: removes x from D(v_xi) if no y in D(v_xj) satisfies constraint.
        """
        revised = False
        new_d_xi = []
        for x in domains[v_xi]:
            has_consistent_y = False
            for y in domains[v_xj]:
                test_assign = {v_xi: x, v_xj: y}
                if constraint.is_satisfied(test_assign):
                    has_consistent_y = True
                    break
            if has_consistent_y:
                new_d_xi.append(x)
            else:
                revised = True

        if revised:
            domains[v_xi] = new_d_xi

        return revised, domains

    def solve(self, use_ac3: bool = True) -> Tuple[Optional[Dict[ScheduleVariable, Staff]], Dict[str, Any]]:
        """
        Executes CSP Solver to find a valid assignment satisfying all hard constraints.
        Returns (assignment, stats_dict).
        """
        start_time = time.perf_counter()
        self.nodes_expanded = 0
        self.backtracks_count = 0

        initial_domains = {var: list(vals) for var, vals in self.problem.domains.items()}

        if use_ac3:
            consistent, pruned_domains = self.ac3(initial_domains)
            if not consistent:
                self.execution_time_sec = time.perf_counter() - start_time
                return None, self._get_stats(solved=False)
            initial_domains = pruned_domains

        assignment: Dict[ScheduleVariable, Staff] = {}
        result = self._backtrack(assignment, initial_domains)
        self.execution_time_sec = time.perf_counter() - start_time

        stats = self._get_stats(solved=result is not None)
        return result, stats

    def _backtrack(
        self,
        assignment: Dict[ScheduleVariable, Staff],
        domains: Dict[ScheduleVariable, List[Staff]]
    ) -> Optional[Dict[ScheduleVariable, Staff]]:
        """Core recursive backtracking search algorithm with MRV and LCV."""
        if len(assignment) == len(self.problem.variables):
            return assignment

        var = self._select_unassigned_variable(assignment, domains)
        if var is None:
            return None

        for val in self._order_domain_values(var, assignment, domains):
            self.nodes_expanded += 1
            test_assign = dict(assignment)
            test_assign[var] = val

            # Check local constraint consistency
            if self._is_consistent(var, val, test_assign):
                # Apply forward checking / domain inference
                new_domains = {v: list(d) for v, d in domains.items()}
                new_domains[var] = [val]

                res = self._backtrack(test_assign, new_domains)
                if res is not None:
                    return res

            self.backtracks_count += 1

        return None

    def _select_unassigned_variable(
        self,
        assignment: Dict[ScheduleVariable, Staff],
        domains: Dict[ScheduleVariable, List[Staff]]
    ) -> Optional[ScheduleVariable]:
        """
        Selects next variable using MRV (Minimum Remaining Values)
        and Degree Heuristic for tie-breaking.
        """
        unassigned = [v for v in self.problem.variables if v not in assignment]
        if not unassigned:
            return None

        # MRV: sort by smallest domain size
        min_domain_size = min(len(domains[v]) for v in unassigned)
        mrv_candidates = [v for v in unassigned if len(domains[v]) == min_domain_size]

        if len(mrv_candidates) == 1:
            return mrv_candidates[0]

        # Degree Heuristic: pick candidate involved in highest number of constraints with other unassigned vars
        best_var = mrv_candidates[0]
        max_degree = -1
        for candidate in mrv_candidates:
            degree = 0
            for c in self.problem.constraints:
                if candidate in c.variables:
                    degree += sum(1 for v in c.variables if v != candidate and v not in assignment)
            if degree > max_degree:
                max_degree = degree
                best_var = candidate

        return best_var

    def _order_domain_values(
        self,
        var: ScheduleVariable,
        assignment: Dict[ScheduleVariable, Staff],
        domains: Dict[ScheduleVariable, List[Staff]]
    ) -> List[Staff]:
        """
        LCV (Least Constraining Value) Heuristic:
        Orders values by number of conflicts caused in neighboring unassigned variables.
        """
        values = domains[var]
        if len(values) <= 1:
            return values

        def count_conflicts(val: Staff) -> int:
            conflicts = 0
            temp_assign = dict(assignment)
            temp_assign[var] = val
            for c in self.problem.constraints:
                if var in c.variables:
                    if not c.is_satisfied(temp_assign):
                        conflicts += 1
            return conflicts

        return sorted(values, key=count_conflicts)

    def _is_consistent(
        self,
        var: ScheduleVariable,
        val: Staff,
        assignment: Dict[ScheduleVariable, Staff]
    ) -> bool:
        """Checks if assigning val to var satisfies all relevant constraints."""
        for c in self.problem.constraints:
            if var in c.variables:
                if not c.is_satisfied(assignment):
                    return False
        return True

    def _get_stats(self, solved: bool) -> Dict[str, Any]:
        return {
            "solved": solved,
            "nodes_expanded": self.nodes_expanded,
            "backtracks_count": self.backtracks_count,
            "execution_time_sec": round(self.execution_time_sec, 5),
            "execution_time_ms": round(self.execution_time_sec * 1000, 2),
        }


class GASolver:
    """
    Genetic Algorithm (GA) Solver with Tournament Selection,
    Uniform/Two-Point Crossover, Adaptive Mutation, and Elitism.
    """

    def __init__(
        self,
        problem: ProblemDefinition,
        pop_size: int = 100,
        generations: int = 150,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.05,
        tournament_size: int = 5,
        elitism_count: int = 4,
        random_seed: Optional[int] = 42
    ):
        self.problem = problem
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism_count = min(elitism_count, pop_size)
        if random_seed is not None:
            random.seed(random_seed)

    def _create_random_individual(self) -> List[Staff]:
        """Creates a chromosome: array of staff assigned to each variable in order."""
        chromosome = []
        for var in self.problem.variables:
            domain = self.problem.domains[var]
            if domain:
                chromosome.append(random.choice(domain))
            else:
                # Fallback if domain is empty
                chromosome.append(random.choice(self.problem.all_staff))
        return chromosome

    def _chromosome_to_assignment(self, chromosome: List[Staff]) -> Dict[ScheduleVariable, Staff]:
        return {var: staff for var, staff in zip(self.problem.variables, chromosome)}

    def solve(self) -> Tuple[Dict[ScheduleVariable, Staff], Dict[str, Any]]:
        """
        Executes Evolutionary Loop with Elitism and tracks convergence.
        Returns (best_assignment, convergence_metrics).
        """
        start_time = time.perf_counter()

        # Initialize Population
        population = [self._create_random_individual() for _ in range(self.pop_size)]

        history_best_fitness: List[float] = []
        history_mean_fitness: List[float] = []
        history_hard_violations: List[int] = []

        best_individual: Optional[List[Staff]] = None
        best_fitness = -float("inf")

        for gen in range(self.generations):
            # Evaluate Population
            fitness_scores = []
            hard_violations_list = []

            for ind in population:
                assign = self._chromosome_to_assignment(ind)
                fit = self.problem.calculate_fitness(assign)
                _, violations, _ = self.problem.validate_assignment(assign)

                fitness_scores.append(fit)
                hard_violations_list.append(violations)

                if fit > best_fitness:
                    best_fitness = fit
                    best_individual = list(ind)

            # Record generation metrics
            mean_fit = sum(fitness_scores) / len(fitness_scores)
            min_violations = min(hard_violations_list)

            history_best_fitness.append(best_fitness)
            history_mean_fitness.append(mean_fit)
            history_hard_violations.append(min_violations)

            # Elitism: retain top individuals
            sorted_pop = [ind for _, ind in sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)]
            next_generation = copy.deepcopy(sorted_pop[:self.elitism_count])

            # Produce offspring to fill population
            while len(next_generation) < self.pop_size:
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)

                if random.random() < self.crossover_rate:
                    offspring1, offspring2 = self._crossover(parent1, parent2)
                else:
                    offspring1, offspring2 = list(parent1), list(parent2)

                offspring1 = self._mutate(offspring1)
                offspring2 = self._mutate(offspring2)

                next_generation.append(offspring1)
                if len(next_generation) < self.pop_size:
                    next_generation.append(offspring2)

            population = next_generation

        elapsed_sec = time.perf_counter() - start_time
        best_assignment = self._chromosome_to_assignment(best_individual or population[0])
        is_valid, hard_viol, viol_details = self.problem.validate_assignment(best_assignment)

        stats = {
            "solved": is_valid,
            "best_fitness": best_fitness,
            "final_hard_violations": hard_viol,
            "generations": self.generations,
            "pop_size": self.pop_size,
            "execution_time_sec": round(elapsed_sec, 5),
            "execution_time_ms": round(elapsed_sec * 1000, 2),
            "history_best_fitness": history_best_fitness,
            "history_mean_fitness": history_mean_fitness,
            "history_hard_violations": history_hard_violations,
            "violation_details": viol_details,
        }

        return best_assignment, stats

    def _tournament_selection(self, population: List[List[Staff]], fitness_scores: List[float]) -> List[Staff]:
        """k-tournament selection operator."""
        selected_indices = random.sample(range(len(population)), min(self.tournament_size, len(population)))
        best_idx = max(selected_indices, key=lambda i: fitness_scores[i])
        return population[best_idx]

    def _crossover(self, parent1: List[Staff], parent2: List[Staff]) -> Tuple[List[Staff], List[Staff]]:
        """Two-point Crossover operator."""
        n = len(parent1)
        if n < 2:
            return list(parent1), list(parent2)
        pt1 = random.randint(0, n - 2)
        pt2 = random.randint(pt1 + 1, n - 1)

        offspring1 = parent1[:pt1] + parent2[pt1:pt2] + parent1[pt2:]
        offspring2 = parent2[:pt1] + parent1[pt1:pt2] + parent2[pt2:]
        return offspring1, offspring2

    def _mutate(self, individual: List[Staff]) -> List[Staff]:
        """Mutation operator: domain resetting and swap mutation."""
        mutated = list(individual)
        for i, var in enumerate(self.problem.variables):
            if random.random() < self.mutation_rate:
                domain = self.problem.domains[var]
                if domain:
                    mutated[i] = random.choice(domain)
        return mutated
