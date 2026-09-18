"""
Visualisasi graf alur verifikasi klaim Allianz.
Menghasilkan file graph_alianz.png dengan jalur optimal (hasil UCS) disorot.

"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from Alianz import graph_allianz, ucs_claim_verification

# --- Bangun graf -------------------------------------------------------------
G = nx.Graph()
for node, tetangga in graph_allianz.items():
    for n, bobot in tetangga.items():
        G.add_edge(node, n, weight=bobot)

# Tata letak manual supaya alur terbaca dari kiri ke kanan
pos = {
    "Pengajuan":     (0.0,  0.0),
    "Cek_Polis":     (1.3,  1.1),
    "Verifikasi_RS": (1.3, -1.1),
    "Audit_Fraud":   (2.6,  0.9),
    "Persetujuan":   (3.9,  0.0),
    "Pencairan":     (5.2,  0.0),
}

# --- Jalur optimal -----------------------------------------------------------
total, jalur = ucs_claim_verification("Pengajuan", "Pencairan", graph_allianz)
edge_optimal = [(jalur[i], jalur[i + 1]) for i in range(len(jalur) - 1)]
edge_optimal_set = {frozenset(e) for e in edge_optimal}
edge_biasa = [e for e in G.edges() if frozenset(e) not in edge_optimal_set]

# --- Gambar ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6))

nx.draw_networkx_edges(G, pos, edgelist=edge_biasa, width=2,
                       edge_color="#b0b7c3", ax=ax)
nx.draw_networkx_edges(G, pos, edgelist=edge_optimal, width=4,
                       edge_color="#e8590c", ax=ax)

warna_node = ["#e8590c" if n in jalur else "#4c6ef5" for n in G.nodes()]
nx.draw_networkx_nodes(G, pos, node_size=4800, node_color=warna_node,
                       edgecolors="white", linewidths=2.5, ax=ax)
label_node = {n: n.replace("_", "\n") for n in G.nodes()}
nx.draw_networkx_labels(G, pos, labels=label_node, font_size=9,
                        font_color="white", font_weight="bold", ax=ax)

label_bobot = {(u, v): f"{d['weight']} mnt" for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=label_bobot, font_size=9,
                             bbox=dict(boxstyle="round,pad=0.25", fc="white",
                                       ec="#dee2e6"), ax=ax)

jalur_teks = " \u2192 ".join(jalur)
ax.set_title("Graf Alur Verifikasi Klaim Allianz\n"
             f"Jalur optimal (UCS): {jalur_teks}  =  {total} menit",
             fontsize=13, fontweight="bold", pad=18)
ax.axis("off")
ax.margins(0.12)
plt.tight_layout()
plt.savefig("graph_alianz.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Tersimpan: graph_alianz.png")
