import streamlit as st
import pandas as pd
import plotly.express as px
import heapq
import time

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# ---------------------------------------------------------
st.set_page_config(
    page_title="Allianz Claim AI Copilot",
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS STYLING
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #f4f7fc;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        border: 1px solid #eef2f8;
    }
    .kpi-title { color: #6c757d; font-size: 0.85rem; font-weight: 500; margin-bottom: 8px; }
    .kpi-value { color: #1e293b; font-size: 1.6rem; font-weight: 700; }
    .kpi-sub { font-size: 0.78rem; margin-top: 4px; font-weight: 600; }
    .text-green { color: #10b981; }
    
    .right-card {
        background: white;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        border: 1px solid #eef2f8;
        margin-bottom: 16px;
    }
    .quote-card {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border-radius: 14px;
        padding: 18px;
        color: #0369a1;
        font-style: italic;
        text-align: center;
        font-weight: 600;
    }
    div[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. GRAF ALUR KLAIM & FUNGSI UCS
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
# 4. SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("<h3 style='color:#003781; font-weight:700;'>🟦 Allianz <span style='font-size:0.8rem; color:#64748b;'>Claim AI</span></h3>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio(
        "Menu Utama",
        ["🏠 Dashboard", "📄 Klaim", "📊 Analitik & Laporan", "👥 Nasabah", "📁 Dokumen", "🤖 AI Copilot", "⚙️ Pengaturan"],
        index=0
    )
    st.markdown("---")
    st.info("💡 **UCS Engine:** Menggunakan algoritma Uniform Cost Search untuk menentukan rute keputusan tercepat.")

# ---------------------------------------------------------
# 5. LAYOUT UTAMA & SIDE PANEL
# ---------------------------------------------------------
col_main, col_right = st.columns([2.6, 1.1])

with col_main:
    st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 14px; margin-bottom: 20px; border: 1px solid #eef2f8;'>
            <h2 style='margin:0; color:#1e293b;'>Halo, Rimanda! 👋</h2>
            <p style='margin:4px 0 0 0; color:#64748b;'>Selamat datang di Allianz Claim AI Copilot. Sistem cerdas untuk membantu navigasi dan optimasi alur pemrosesan klaim asuransi.</p>
        </div>
    """, unsafe_allow_html=True)

    # 4 KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Total Klaim Hari Ini</div><div class='kpi-value'>48</div><div class='kpi-sub text-green'>↑ 12% vs kemarin</div></div>", unsafe_allow_html=True)
    with k2:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Rata-rata Waktu Proses</div><div class='kpi-value'>2.4 hari</div><div class='kpi-sub text-green'>↓ 32% vs bulan lalu</div></div>", unsafe_allow_html=True)
    with k3:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Tingkat Penyelesaian</div><div class='kpi-value'>96%</div><div class='kpi-sub text-green'>↑ 5% vs bulan lalu</div></div>", unsafe_allow_html=True)
    with k4:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Nasabah Aktif</div><div class='kpi-value'>1.248</div><div class='kpi-sub text-green'>↑ 8% vs bulan lalu</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row
    c_chart1, c_chart2 = st.columns([1.6, 1])
    with c_chart1:
        st.markdown("##### 📈 Tren Klaim 7 Hari Terakhir")
        dates = ['12 Sep', '13 Sep', '14 Sep', '15 Sep', '16 Sep', '17 Sep', '18 Sep']
        df_trend = pd.DataFrame({'Tanggal': dates, 'Diterima': [38, 28, 42, 50, 35, 48, 54], 'Selesai': [22, 18, 26, 28, 20, 26, 32]})
        fig_line = px.line(df_trend, x='Tanggal', y=['Diterima', 'Selesai'], color_discrete_sequence=['#003781', '#60a5fa'], markers=True)
        fig_line.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10), legend_title_text='')
        st.plotly_chart(fig_line, use_container_width=True)

    with c_chart2:
        st.markdown("##### 🍰 Jenis Klaim")
        df_pie = pd.DataFrame({'Kategori': ['Kesehatan', 'Kendaraan', 'Jiwa', 'Lainnya'], 'Jumlah': [42, 25, 18, 15]})
        fig_pie = px.pie(df_pie, values='Jumlah', names='Kategori', hole=0.6, color_discrete_sequence=['#003781', '#3b82f6', '#93c5fd', '#cbd5e1'])
        fig_pie.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabel Klaim
    st.markdown("##### 📄 Klaim Terbaru")
    data_klaim = {
        "No. Klaim": ["CL-2026-0487", "CL-2026-0486", "CL-2026-0485", "CL-2026-0484", "CL-2026-0483"],
        "Jenis Klaim": ["Kesehatan", "Kendaraan", "Jiwa", "Kesehatan", "Kendaraan"],
        "Nasabah": ["Siti Nurhaliza", "Andi Pratama", "Maria Febriani", "Rizky Hidayat", "Dewi Lestari"],
        "Tanggal Pengajuan": ["18 Sep 2026, 10:12", "18 Sep 2026, 09:45", "17 Sep 2026, 16:30", "17 Sep 2026, 14:20", "17 Sep 2026, 11:05"],
        "Status": ["Dalam Proses", "Diverifikasi", "Disetujui", "Selesai", "Dalam Proses"]
    }
    st.dataframe(pd.DataFrame(data_klaim), use_container_width=True)


# ---------------------------------------------------------
# 6. PANEL KANAN: AI COPILOT INTERAKTIF (CHAT READY)
# ---------------------------------------------------------
with col_right:
    st.markdown("""
        <div class='right-card'>
            <h4 style='margin:0; color:#003781;'>🤖 AI Copilot</h4>
            <p style='font-size:0.8rem; color:#64748b;'>Tanyakan rute klaim, status, atau instruksi optimasi.</p>
        </div>
    """, unsafe_allow_html=True)

    # Session State Chat History khusus Panel Kanan
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            ("assistant", "Halo Rimanda! Aku **Allianz AI Copilot**. Ketik **'rute'** untuk hitung jalur UCS atau tanyakan sesuatu!")
        ]

    # Container Chat Box dengan Scrollbar Limit
    chat_container = st.container(height=260)
    with chat_container:
        for role, text in st.session_state.chat_history:
            if role == "user":
                st.markdown(f"<div style='background:#e0f2fe; padding:8px 12px; border-radius:10px; margin-bottom:8px; text-align:right; color:#0369a1;'><b>Kamu:</b> {text}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background:#f1f5f9; padding:8px 12px; border-radius:10px; margin-bottom:8px; color:#1e293b;'><b>Copilot:</b> {text}</div>", unsafe_allow_html=True)

    # Input Form khusus dalam Kolom Kanan
    with st.form(key="copilot_form", clear_on_submit=True):
        user_prompt = st.text_input("Pesan ke Copilot...", placeholder="Ketik 'rute' atau pesan lain...")
        submit_btn = st.form_submit_button("Kirim ↗️", use_container_width=True)

    if submit_btn and user_prompt:
        # Simpan pesan user
        st.session_state.chat_history.append(("user", user_prompt))
        
        prompt_l = user_prompt.lower()
        if any(k in prompt_l for k in ["rute", "hitung", "jalur", "ucs", "optimal"]):
            cost, path = ucs_claim_verification("Pengajuan", "Pencairan", GRAPH_ALLIANZ)
            res = f"<b>Rute Optimal (UCS):</b><br>{' ➔ '.join(path)}<br>⏱️ <b>Estimasi:</b> {cost} Menit"
        elif "status" in prompt_l:
            res = "Klaim terbaru <b>#CL-2026-0487</b> saat ini berstatus <i>'Dalam Proses'</i>."
        else:
            res = f"Aku menerima pesanmu: <i>'{user_prompt}'</i>. Ketik <b>'rute'</b> untuk melihat demonstrasi UCS!"
            
        st.session_state.chat_history.append(("assistant", res))
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Card Notifikasi Terbaru
    st.markdown("""
        <div class='right-card'>
            <h5 style='margin-top:0; color:#1e293b;'>🔔 Notifikasi Terbaru</h5>
            <div style='font-size:0.82rem; margin-bottom:10px;'>
                <b>Klaim #CL-2026-0487</b><br>
                <span style='color:#64748b;'>Status diperbarui menjadi "Dalam Proses"</span>
            </div>
            <div style='font-size:0.82rem; margin-bottom:10px;'>
                <b>Dokumen Baru Diterima</b><br>
                <span style='color:#64748b;'>Polis nasabah Budi Santoso</span>
            </div>
            <div style='font-size:0.82rem;'>
                <b>Klaim #CL-2026-0472</b><br>
                <span style='color:#64748b;'>Telah disetujui dan siap dicairkan</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Banner Quote Allianz
    st.markdown("""
        <div class='quote-card'>
            "Lebih cepat, lebih mudah, lebih pasti."
            <br><br>
            <span style='font-size:0.85rem; font-weight:700;'>Allianz 🟦</span>
        </div>
    """, unsafe_allow_html=True)