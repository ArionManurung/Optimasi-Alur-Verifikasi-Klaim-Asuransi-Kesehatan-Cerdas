import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import heapq
import time

from src.tugas02_milestone2.domain import (
    generate_allianz_problem_small,
    generate_allianz_problem_large,
    STAGE_QUALIFICATIONS,
)
from src.tugas02_milestone2.solver import CSPSolver, GASolver

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Allianz Claim AI Copilot - Milestone 1 & 2",
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Styling
st.markdown("""
<style>
    .stApp { font-family: 'Segoe UI', Roboto, sans-serif; }
    .kpi-card {
        background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .kpi-title { font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; opacity: 0.8;}
    .kpi-value { font-size: 1.6rem; font-weight: 700; }
    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MILESTONE 1: GRAPH & UCS ENGINE
# ---------------------------------------------------------
GRAPH_ALLIANZ = {
    'Pengajuan': {'Cek_Polis': 5, 'Verifikasi_RS': 15},
    'Cek_Polis': {'Pengajuan': 5, 'Audit_Fraud': 10},
    'Verifikasi_RS': {'Pengajuan': 15, 'Audit_Fraud': 5, 'Persetujuan': 20},
    'Audit_Fraud': {'Cek_Polis': 10, 'Verifikasi_RS': 5, 'Persetujuan': 10},
    'Persetujuan': {'Verifikasi_RS': 20, 'Audit_Fraud': 10, 'Pencairan': 5},
    'Pencairan': {'Persetujuan': 5}
}

def ucs_claim_verification(start, goal, graph):
    pq = [(0, [start])]
    visited = set()
    while pq:
        cost, path = heapq.heappop(pq)
        node = path[-1]
        if node == goal:
            return cost, path
        if node not in visited:
            visited.add(node)
            for neighbor, weight in graph[node].items():
                if neighbor not in visited:
                    heapq.heappush(pq, (cost + weight, path + [neighbor]))
    return float("inf"), []

# ---------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#003781; font-weight:800; margin-bottom:0;'>🟦 Allianz <span style='font-size:1.0rem; color:#64748b;'>AI Copilot</span></h2>", unsafe_allow_html=True)
    st.caption("Sistem Optimasi Verifikasi Klaim & Penjadwalan Staf")
    st.markdown("---")
    
    menu = st.radio(
        "Navigasi Proyek",
        [
            "🏠 Dashboard Utama",
            "🧩 Milestone 1: UCS Claim Path",
            "⚙️ Milestone 2: CSP & GA Solver",
            "📊 Analisis Sensitivitas & Performa",
        ],
        index=2
    )
    
    st.markdown("---")
    st.info("💡 **Milestone 2 (W04):** Engine optimasi batasan bisnis menggunakan **CSP (AC-3 + Backtracking MRV)** dan **Algoritma Genetika (GA Elitism)**.")

# ---------------------------------------------------------
# 4. DASHBOARD UTAMA
# ---------------------------------------------------------
if menu == "🏠 Dashboard Utama":
    st.title("🏠 Dashboard Utama - Allianz Claim AI Copilot")
    st.markdown("Selamat datang di platform optimasi operasional verifikasi klaim asuransi kesehatan Allianz.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="kpi-card"><div class="kpi-title">Modul 1 Pathfinder</div><div class="kpi-value">UCS Engine</div><div style="color:#10b981; font-size:0.8rem; font-weight:600;">⚡ 30 Menit Route</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="kpi-card"><div class="kpi-title">Modul 2 Constraint Solver</div><div class="kpi-value">CSP / GA</div><div style="color:#0080FF; font-size:0.8rem; font-weight:600;">🎯 AC-3 + Elitism</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="kpi-card"><div class="kpi-title">Integritas Batasan</div><div class="kpi-value">100% Legal</div><div style="color:#10b981; font-size:0.8rem; font-weight:600;">0 Violations</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="kpi-card"><div class="kpi-title">Skala Dukungan</div><div class="kpi-value">84 Shifts</div><div style="color:#64748b; font-size:0.8rem; font-weight:600;">Up to 24 Staff</div></div>', unsafe_allow_html=True)

    st.markdown("### Architecture Pipeline Overview")
    st.markdown("""
    1. **Milestone 1**: Pencarian jalur verifikasi klaim tercepat menggunakan *Uniform Cost Search* (UCS).
    2. **Milestone 2**: Optimasi alokasi verifikator klaim terikat batasan regulasi (Labor Law, Medical Certification, Shift Exclusivity) menggunakan **CSP (AC-3 & MRV)** & **GA Evolutionary Loop**.
    """)

# ---------------------------------------------------------
# 5. MILESTONE 1 VIEW
# ---------------------------------------------------------
elif menu == "🧩 Milestone 1: UCS Claim Path":
    st.title("🧩 Milestone 1: Optimasi Alur Verifikasi Klaim (UCS)")
    st.markdown("Pencarian alur verifikasi klaim dengan estimasi waktu terendah menggunakan Uniform Cost Search.")
    
    start_node = st.selectbox("Tahap Awal", list(GRAPH_ALLIANZ.keys()), index=0)
    goal_node = st.selectbox("Tahap Akhir", list(GRAPH_ALLIANZ.keys()), index=5)
    
    if st.button("Hitung Jalur Optimal (UCS)"):
        waktu, jalur = ucs_claim_verification(start_node, goal_node, GRAPH_ALLIANZ)
        st.success(f"**Jalur Optimal**: {' ➔ '.join(jalur)}")
        st.metric("Total Waktu Proses", f"{waktu} Menit")

# ---------------------------------------------------------
# 6. MILESTONE 2: CSP & GA SOLVER VIEW
# ---------------------------------------------------------
elif menu == "⚙️ Milestone 2: CSP & GA Solver":
    st.title("⚙️ Milestone 2: Modul Pemecahan Batasan Keputusan Bisnis")
    st.markdown("Mesin inferensi batasan (*Constraint Solver*) untuk alokasi shift verifikator klaim terikat regulasi bisnis.")
    
    col_config, col_main = st.columns([1, 2.5])
    
    with col_config:
        st.subheader("🛠️ Parameter Solver")
        
        algorithm = st.radio(
            "Pilih Algoritma",
            ["CSP (AC-3 + Backtracking MRV)", "Algoritma Genetika (GA Elitism)"],
            index=0
        )
        
        scale = st.selectbox(
            "Skala Masalah",
            ["Small Scale (3 Hari, 24 Slot Shift)", "Large Scale (7 Hari, 84 Slot Shift)"]
        )
        
        if "Genetic Algorithm" in algorithm:
            st.markdown("**Konfigurasi GA**")
            pop_size = st.slider("Ukuran Populasi", 20, 200, 80, 10)
            generations = st.slider("Jumlah Generasi", 10, 300, 100, 10)
            crossover_rate = st.slider("Crossover Rate", 0.5, 1.0, 0.85, 0.05)
            mutation_rate = st.slider("Mutation Rate", 0.01, 0.30, 0.05, 0.01)
        else:
            use_ac3 = st.checkbox("Aktifkan Propagasi Batasan AC-3", value=True)
            
        btn_solve = st.button("🚀 Jalankan Optimasi Solver", use_container_width=True)

    with col_main:
        if btn_solve:
            problem = generate_allianz_problem_small() if "Small" in scale else generate_allianz_problem_large()
            
            st.subheader("📋 Hasil Penjadwalan & Verifikasi Batasan")
            
            with st.spinner("Menjalankan mesin inferensi solver..."):
                start_t = time.perf_counter()
                
                if "CSP" in algorithm:
                    solver = CSPSolver(problem)
                    solution, stats = solver.solve(use_ac3=use_ac3)
                else:
                    solver = GASolver(
                        problem=problem,
                        pop_size=pop_size,
                        generations=generations,
                        crossover_rate=crossover_rate,
                        mutation_rate=mutation_rate,
                        random_seed=42
                    )
                    solution, stats = solver.solve()
                
                exec_time = (time.perf_counter() - start_t) * 1000

            if solution is not None:
                is_valid, viol_count, viol_details = problem.validate_assignment(solution)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Status Solusi", "LEGAL / OPTIMAL" if is_valid else "PELANGGARAN DETEKSI")
                m2.metric("Waktu Eksekusi", f"{exec_time:.2f} ms")
                m3.metric("Jumlah Pelanggaran Hard", f"{viol_count}")
                
                # Format Schedule Table
                records = []
                for var, staff in solution.items():
                    records.append({
                        "Hari": f"Hari {var.day}",
                        "Shift": var.shift,
                        "Tahap Klaim": var.stage,
                        "Staf Terpilih": f"{staff.name} ({staff.id})",
                        "Kualifikasi Sesuai": "✅" if staff.has_qualification(STAGE_QUALIFICATIONS[var.stage]) else "❌"
                    })
                
                df_sched = pd.DataFrame(records)
                st.dataframe(df_sched, use_container_width=True, height=350)
                
                # Visual Heatmap of Shifts
                st.subheader("📊 Visualisasi Matrix Alokasi Shift Staf")
                pivot_df = df_sched.pivot(index=["Hari", "Shift"], columns="Tahap Klaim", values="Staf Terpilih")
                st.table(pivot_df)

                if "Genetic Algorithm" in algorithm and "history_best_fitness" in stats:
                    st.subheader("📈 Grafik Konvergensi Fitness GA")
                    df_fit = pd.DataFrame({
                        "Generasi": range(1, len(stats["history_best_fitness"]) + 1),
                        "Best Fitness": stats["history_best_fitness"],
                        "Mean Fitness": stats["history_mean_fitness"]
                    })
                    fig_fit = px.line(df_fit, x="Generasi", y=["Best Fitness", "Mean Fitness"], title="Progres Konvergensi GA per Generasi")
                    st.plotly_chart(fig_fit, use_container_width=True)
            else:
                st.error("❌ Solver gagal menemukan solusi yang memenuhi seluruh batasan (Unsatisfiable Problem).")

# ---------------------------------------------------------
# 7. ANALISIS SENSITIVITAS VIEW
# ---------------------------------------------------------
elif menu == "📊 Analisis Sensitivitas & Performa":
    st.title("📊 Laporan Analisis Sensitivitas & Performa Solver")
    st.markdown("Perbandingan performa komputasi antara **CSP (AC-3 + Backtracking MRV)** dan **Algoritma Genetika (GA)**.")
    
    if st.button("🔥 Jalankan Suite Benchmark Sensitivitas"):
        with st.spinner("Menjalankan pengujian performa skala kecil & besar..."):
            small_p = generate_allianz_problem_small()
            large_p = generate_allianz_problem_large()
            
            # CSP
            c_s = CSPSolver(small_p); _, csp_s_stats = c_s.solve(use_ac3=True)
            c_l = CSPSolver(large_p); _, csp_l_stats = c_l.solve(use_ac3=True)
            
            # GA
            g_s = GASolver(small_p, pop_size=80, generations=100, random_seed=42); _, ga_s_stats = g_s.solve()
            g_l = GASolver(large_p, pop_size=100, generations=120, random_seed=42); _, ga_l_stats = g_l.solve()
            
            df_bench = pd.DataFrame([
                {"Metode": "CSP (AC-3 + MRV)", "Skala": "Small (24 Vars)", "Waktu Eksekusi (ms)": csp_s_stats["execution_time_ms"], "Hard Violations": 0, "Akurasi Solusi": "100% Exact"},
                {"Metode": "GA (Elitism)", "Skala": "Small (24 Vars)", "Waktu Eksekusi (ms)": ga_s_stats["execution_time_ms"], "Hard Violations": ga_s_stats["final_hard_violations"], "Akurasi Solusi": "Feasible Optimal"},
                {"Metode": "CSP (AC-3 + MRV)", "Skala": "Large (84 Vars)", "Waktu Eksekusi (ms)": csp_l_stats["execution_time_ms"], "Hard Violations": 0, "Akurasi Solusi": "100% Exact"},
                {"Metode": "GA (Elitism)", "Skala": "Large (84 Vars)", "Waktu Eksekusi (ms)": ga_l_stats["execution_time_ms"], "Hard Violations": ga_l_stats["final_hard_violations"], "Akurasi Solusi": "Approx Soluton"},
            ])
            
            st.dataframe(df_bench, use_container_width=True)
            
            fig_time = px.bar(df_bench, x="Skala", y="Waktu Eksekusi (ms)", color="Metode", barmode="group", title="Perbandingan Waktu Eksekusi (Waktu Komputasi)")
            st.plotly_chart(fig_time, use_container_width=True)