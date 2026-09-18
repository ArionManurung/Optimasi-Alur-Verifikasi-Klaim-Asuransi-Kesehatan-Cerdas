import heapq

# Formulasi Graf Alur Verifikasi Klaim Allianz (Node: {Tetangga: Waktu_Menit})
graph_allianz = {
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

waktu_opt, jalur_opt = ucs_claim_verification('Pengajuan', 'Pencairan', graph_allianz)
print(f"Jalur Optimal : {' -> '.join(jalur_opt)}")
print(f"Total Waktu   : {waktu_opt} Menit")