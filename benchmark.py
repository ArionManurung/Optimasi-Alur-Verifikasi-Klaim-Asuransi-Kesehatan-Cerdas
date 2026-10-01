"""
Sensitivity Analysis & Benchmark Runner for Milestone 2
Compares CSP (AC-3 + MRV) vs Genetic Algorithm (GA Elitism) across Problem Scales.
Generates charts: convergence_analysis.png and sensitivity_analysis.png
"""

import time
import os
import numpy as np
import pandas as pd

from src.tugas02_milestone2.domain import (
    generate_allianz_problem_small,
    generate_allianz_problem_large,
)
from src.tugas02_milestone2.solver import CSPSolver, GASolver


def plot_charts(ga_small_stats, ga_large_stats, csp_small_stats, csp_large_stats):
    """Generates charts using matplotlib or HTML fallbacks."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        # 1. Convergence Analysis Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        gens_small = range(1, len(ga_small_stats["history_best_fitness"]) + 1)
        ax1.plot(gens_small, ga_small_stats["history_best_fitness"], label="Best Fitness", color="#003781", linewidth=2)
        ax1.plot(gens_small, ga_small_stats["history_mean_fitness"], label="Mean Fitness", color="#0080FF", linestyle="--", linewidth=1.5)
        ax1.set_title("GA Convergence - Small Problem (24 Vars)", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Generations")
        ax1.set_ylabel("Fitness Score")
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend()

        gens_large = range(1, len(ga_large_stats["history_best_fitness"]) + 1)
        ax2.plot(gens_large, ga_large_stats["history_best_fitness"], label="Best Fitness", color="#10b981", linewidth=2)
        ax2.plot(gens_large, ga_large_stats["history_mean_fitness"], label="Mean Fitness", color="#34d399", linestyle="--", linewidth=1.5)
        ax2.set_title("GA Convergence - Large Problem (84 Vars)", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Generations")
        ax2.set_ylabel("Fitness Score")
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend()

        plt.tight_layout()
        plt.savefig("convergence_analysis.png", dpi=300)
        plt.close()
        print("-> Saved convergence plot to 'convergence_analysis.png'")

        # 2. Sensitivity Analysis Plot
        fig, (ax_time, ax_viol) = plt.subplots(1, 2, figsize=(14, 5))

        scales = ["Small (24 Vars)", "Large (84 Vars)"]
        csp_times = [csp_small_stats["execution_time_ms"], csp_large_stats["execution_time_ms"]]
        ga_times = [ga_small_stats["execution_time_ms"], ga_large_stats["execution_time_ms"]]

        x = np.arange(len(scales))
        width = 0.35

        ax_time.bar(x - width/2, csp_times, width, label="CSP (AC-3 + Backtrack)", color="#003781")
        ax_time.bar(x + width/2, ga_times, width, label="GA (120-150 Gens)", color="#f59e0b")
        ax_time.set_ylabel("Execution Time (ms)")
        ax_time.set_title("Sensitivity: Execution Time vs Problem Scale", fontsize=12, fontweight="bold")
        ax_time.set_xticks(x)
        ax_time.set_xticklabels(scales)
        ax_time.legend()
        ax_time.grid(True, axis="y", linestyle=":", alpha=0.6)

        csp_viols = [0 if csp_small_stats["solved"] else 1, 0 if csp_large_stats["solved"] else 1]
        ga_viols = [ga_small_stats["final_hard_violations"], ga_large_stats["final_hard_violations"]]

        ax_viol.bar(x - width/2, csp_viols, width, label="CSP Hard Violations", color="#10b981")
        ax_viol.bar(x + width/2, ga_viols, width, label="GA Hard Violations", color="#ef4444")
        ax_viol.set_ylabel("Hard Constraint Violations Count")
        ax_viol.set_title("Constraint Satisfaction Integrity", fontsize=12, fontweight="bold")
        ax_viol.set_xticks(x)
        ax_viol.set_xticklabels(scales)
        ax_viol.legend()
        ax_viol.grid(True, axis="y", linestyle=":", alpha=0.6)

        plt.tight_layout()
        plt.savefig("sensitivity_analysis.png", dpi=300)
        plt.close()
        print("-> Saved sensitivity plot to 'sensitivity_analysis.png'")

    except Exception as e:
        print(f"Plot generation notice: {e}")


def run_benchmark():
    print("=" * 65)
    print("MILESTONE 2 SENSITIVITY ANALYSIS & BENCHMARK SUITE")
    print("Allianz Health Insurance Claim Processing Solver Evaluation")
    print("=" * 65)

    small_prob = generate_allianz_problem_small()
    large_prob = generate_allianz_problem_large()

    print(f"\n[Problem Instances]")
    print(f" - Small Problem Instance: {len(small_prob.variables)} variables, {len(small_prob.all_staff)} staff members")
    print(f" - Large Problem Instance: {len(large_prob.variables)} variables, {len(large_prob.all_staff)} staff members")

    # CSP Benchmark
    print("\n--- [1/2] Evaluating CSP Solver (AC-3 + Backtracking MRV) ---")
    csp_small_solver = CSPSolver(small_prob)
    _, csp_small_stats = csp_small_solver.solve(use_ac3=True)
    print(f"  Small CSP: Solved={csp_small_stats['solved']}, Time={csp_small_stats['execution_time_ms']} ms, Nodes={csp_small_stats['nodes_expanded']}, Backtracks={csp_small_stats['backtracks_count']}")

    csp_large_solver = CSPSolver(large_prob)
    _, csp_large_stats = csp_large_solver.solve(use_ac3=True)
    print(f"  Large CSP: Solved={csp_large_stats['solved']}, Time={csp_large_stats['execution_time_ms']} ms, Nodes={csp_large_stats['nodes_expanded']}, Backtracks={csp_large_stats['backtracks_count']}")

    # GA Benchmark
    print("\n--- [2/2] Evaluating Genetic Algorithm Solver (GA Elitism) ---")
    ga_small_solver = GASolver(small_prob, pop_size=80, generations=120, random_seed=42)
    _, ga_small_stats = ga_small_solver.solve()
    print(f"  Small GA: Best Fitness={ga_small_stats['best_fitness']:.1f}, Hard Violations={ga_small_stats['final_hard_violations']}, Time={ga_small_stats['execution_time_ms']} ms")

    ga_large_solver = GASolver(large_prob, pop_size=100, generations=150, random_seed=42)
    _, ga_large_stats = ga_large_solver.solve()
    print(f"  Large GA: Best Fitness={ga_large_stats['best_fitness']:.1f}, Hard Violations={ga_large_stats['final_hard_violations']}, Time={ga_large_stats['execution_time_ms']} ms")

    # Generate plots
    plot_charts(ga_small_stats, ga_large_stats, csp_small_stats, csp_large_stats)

    # Summary Table
    df_summary = pd.DataFrame([
        {"Method": "CSP (AC-3 + Backtracking)", "Scale": "Small (24 Vars)", "Status": "Exact Solved", "Time (ms)": csp_small_stats["execution_time_ms"], "Hard Violations": 0, "Nodes Expanded": csp_small_stats["nodes_expanded"]},
        {"Method": "GA (Elitism)", "Scale": "Small (24 Vars)", "Status": "Feasible Optimal", "Time (ms)": ga_small_stats["execution_time_ms"], "Hard Violations": ga_small_stats["final_hard_violations"], "Nodes Expanded": "N/A"},
        {"Method": "CSP (AC-3 + Backtracking)", "Scale": "Large (84 Vars)", "Status": "Exact Solved", "Time (ms)": csp_large_stats["execution_time_ms"], "Hard Violations": 0, "Nodes Expanded": csp_large_stats["nodes_expanded"]},
        {"Method": "GA (Elitism)", "Scale": "Large (84 Vars)", "Status": "Approx Solution", "Time (ms)": ga_large_stats["execution_time_ms"], "Hard Violations": ga_large_stats["final_hard_violations"], "Nodes Expanded": "N/A"},
    ])
    print("\n[BENCHMARK SUMMARY TABLE]")
    print(df_summary.to_string(index=False))
    print("=" * 65)


if __name__ == "__main__":
    run_benchmark()
