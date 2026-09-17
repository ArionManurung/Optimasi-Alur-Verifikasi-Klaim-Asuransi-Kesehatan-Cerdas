import matplotlib.pyplot as plt
import networkx as nx

# Pemodelan Graf Alur Verifikasi Klaim Asuransi Health (Allianz-AdMedika)
# Structured graph edges with weights (menit)
edges_with_weights = [
    ("Pengajuan", "Cek_Polis", 5),
    ("Pengajuan", "Verifikasi_RS", 15),
    ("Cek_Polis", "Audit_Fraud", 10),
    ("Cek_Polis", "Verifikasi_RS", 5),
    ("Verifikasi_RS", "Audit_Fraud", 5),
    ("Verifikasi_RS", "Persetujuan", 20),
    ("Audit_Fraud", "Persetujuan", 10),
    ("Audit_Fraud", "Pencairan", 20),
    ("Persetujuan", "Pencairan", 5),
]


def draw_and_save_graph():
    G = nx.DiGraph()

    for u, v, w in edges_with_weights:
        G.add_edge(u, v, weight=w)

    pos = {
        "Pengajuan": (0, 1),
        "Cek_Polis": (1, 2),
        "Verifikasi_RS": (1, 0),
        "Audit_Fraud": (2, 2),
        "Persetujuan": (2, 0),
        "Pencairan": (3, 1),
    }

    plt.figure(figsize=(10, 6))

    # Optimal path highlights
    optimal_edges = [
        ("Pengajuan", "Cek_Polis"),
        ("Cek_Polis", "Audit_Fraud"),
        ("Audit_Fraud", "Persetujuan"),
        ("Persetujuan", "Pencairan"),
    ]

    edge_colors = [
        "green" if (u, v) in optimal_edges else "gray" for u, v in G.edges()
    ]
    edge_widths = [3.0 if (u, v) in optimal_edges else 1.2 for u, v in G.edges()]

    # Draw Nodes & Edges
    nx.draw_networkx_nodes(G, pos, node_size=2500, node_color="lightblue")
    nx.draw_networkx_labels(
        G, pos, font_size=9, font_family="sans-serif", font_weight="bold"
    )

    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=G.edges(),
        edge_color=edge_colors,
        width=edge_widths,
        arrowsize=20,
        connectionstyle="arc3,rad=0.1",
    )

    # Draw Edge Labels (Weights)
    edge_labels = nx.get_edge_attributes(G, "weight")
    formatted_edge_labels = {k: f"{v}m" for k, v in edge_labels.items()}
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=formatted_edge_labels, font_size=10, font_color="red"
    )

    plt.title(
        "Graf Ruang Keadaan Optimasi Alur Verifikasi Klaim Asuransi (UCS)",
        fontsize=12,
        fontweight="bold",
    )
    plt.axis("off")
    plt.tight_layout()

    # Save to PNG file
    output_path = "graph_ucs_asuransi.png"
    plt.savefig(output_path, dpi=300)
    print(f"[SUCCESS] Gambar graf berhasil dibuat dan disimpan ke {output_path}")


if __name__ == "__main__":
    draw_and_save_graph()