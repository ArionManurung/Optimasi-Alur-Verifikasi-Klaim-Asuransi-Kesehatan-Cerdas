import heapq

# Pemodelan Graf Kompleks: Alur Verifikasi Klaim Asuransi Kesehatan (Allianz-AdMedika)
# Struktur Graf:
#   Node: Tahapan Verifikasi
#   Edge: (Tetangga, Durasi_Menit, Deskripsi_Proses)
graph_klaim_detail = {
    'Pengajuan': [
        ('Cek_Polis', 5, 'Validasi keaktifan kartu EDC & limit klaim'),
        ('Verifikasi_RS', 15, 'Pemeriksaan fisik & kelengkapan berkas manual')
    ],
    'Cek_Polis': [
        ('Audit_Fraud', 10, 'Cek riwayat klaim & deteksi indikasi fraud'),
        ('Verifikasi_RS', 5, 'Konfirmasi ketersediaan kelas kamar RS')
    ],
    'Verifikasi_RS': [
        ('Audit_Fraud', 5, 'Verifikasi indikasi diagnosa awal dengan tim medis'),
        ('Persetujuan', 20, 'Otorisasi langsung manajer klaim')
    ],
    'Audit_Fraud': [
        ('Persetujuan', 10, 'Penerbitan Surat Jaminan (Guarantee Letter)'),
        ('Pencairan', 20, 'Otorisasi pencairan darurat')
    ],
    'Persetujuan': [
        ('Pencairan', 5, 'Pencairan dana & cetak bukti bayar final')
    ],
    'Pencairan': []
}

def uniform_cost_search_advanced(start_node, goal_node, graph):
    """
    Algoritma Uniform Cost Search (UCS) untuk mencari rute verifikasi 
    dengan total waktu terkecil.
    
    Priority Queue menyimpan tuple: (total_cost, path_nodes, path_descriptions)
    """
    priority_queue = [(0, [start_node], [])]
    visited = {}

    while priority_queue:
        cost, path, log = heapq.heappop(priority_queue)
        current_node = path[-1]

        # Jika sudah mencapai node goal, kembalikan hasil rute optimal
        if current_node == goal_node:
            return cost, path, log

        # Evaluasi node jika belum dikunjungi atau ditemukan biaya yang lebih rendah
        if current_node not in visited or cost < visited[current_node]:
            visited[current_node] = cost
            
            for neighbor, weight, desc in graph[current_node]:
                total_cost = cost + weight
                new_path = path + [neighbor]
                new_log = log + [f"{current_node} -> {neighbor}: {desc} ({weight} menit)"]
                heapq.heappush(priority_queue, (total_cost, new_path, new_log))

    return float("inf"), [], []

if __name__ == "__main__":
    start = 'Pengajuan'
    goal = 'Pencairan'

    print("==========================================================================")
    print("  AGEN AI: OPTIMASI ALUR VERIFIKASI KLAIM ASURANSI KESEHATAN (ADVANCED UCS)")
    print("==========================================================================")
    print(f"Node Awal  : {start}")
    print(f"Node Goal  : {goal}\n")

    total_waktu, rute, rincian = uniform_cost_search_advanced(start, goal, graph_klaim_detail)

    if total_waktu != float("inf"):
        print("[RINCIAN EKSEKUSI TAHAP DEMI TAHAP]")
        for langkah in rincian:
            print(f" • {langkah}")
            
        print("\n[RANGKUMAN HASIL OPTIMASI]")
        print(f"Jalur Tercepat : {' -> '.join(rute)}")
        print(f"Total Durasi   : {total_waktu} Menit")
        print("\nStatus Execution: SUCCESS (0 Error)")
    else:
        print("[ERROR] Jalur verifikasi tidak ditemukan.")
    print("==========================================================================")