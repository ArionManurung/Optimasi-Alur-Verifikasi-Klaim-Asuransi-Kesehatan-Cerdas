import heapq

# Pemodelan Graf Alur Verifikasi Klaim Asuransi Kesehatan
# Node: Tahapan Verifikasi, Edge: Estimasi Waktu (Menit)
graph_klaim = {
    'Pengajuan': {
        'Cek_Polis': 5, 
        'Verifikasi_RS': 15
    },
    'Cek_Polis': {
        'Pengajuan': 5, 
        'Audit_Fraud': 10
    },
    'Verifikasi_RS': {
        'Pengajuan': 15, 
        'Audit_Fraud': 5, 
        'Persetujuan': 20
    },
    'Audit_Fraud': {
        'Cek_Polis': 10, 
        'Verifikasi_RS': 5, 
        'Persetujuan': 10
    },
    'Persetujuan': {
        'Verifikasi_RS': 20, 
        'Audit_Fraud': 10, 
        'Pencairan': 5
    },
    'Pencairan': {
        'Persetujuan': 5
    }
}

def uniform_cost_search(start_node, goal_node, graph):
    priority_queue = [(0, [start_node])]
    visited = set()

    while priority_queue:
        cost, path = heapq.heappop(priority_queue)
        current_node = path[-1]

        if current_node == goal_node:
            return cost, path

        if current_node not in visited:
            visited.add(current_node)
            for neighbor, weight in graph[current_node].items():
                if neighbor not in visited:
                    total_cost = cost + weight
                    new_path = path + [neighbor]
                    heapq.heappush(priority_queue, (total_cost, new_path))

    return float("inf"), []

if __name__ == "__main__":
    start = 'Pengajuan'
    goal = 'Pencairan'

    print("=========================================================")
    print("  AGEN AI: OPTIMASI ALUR VERIFIKASI KLAIM ASURANSI (UCS)  ")
    print("=========================================================")
    print(f"Tahap Awal  : {start}")
    print(f"Tahap Goal  : {goal}\n")

    total_waktu, jalur_optimal = uniform_cost_search(start, goal, graph_klaim)

    if total_waktu != float("inf"):
        print("[HASIL PENCARIAN RUTE OPTIMAL]")
        print("Alur Verifikasi : " + " -> ".join(jalur_optimal))
        print(f"Total Waktu     : {total_waktu} Menit")
        print("\nStatus Execution: SUCCESS (0 Error)")
    else:
        print("[ERROR] Jalur verifikasi tidak ditemukan.")
    print("=========================================================")