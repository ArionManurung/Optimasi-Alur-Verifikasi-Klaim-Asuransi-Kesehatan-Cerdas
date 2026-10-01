# Tugas 02 Milestone 2: Modul Pemecahan Batasan Keputusan Bisnis (CSP / GA Optimization)

Sistem Inferensi Batasan Keputusan Bisnis (**Constraint Solver Engine**) untuk **Optimasi Penjadwalan Shift Staf Verifikasi Klaim Asuransi Kesehatan Allianz**. Modul ini mengembangkan hasil Milestone 1 (*Uniform Cost Search*) dengan mengintegrasikan dua pendekatan algoritmik utama: **Constraint Satisfaction Problem (CSP)** dengan **AC-3 & Backtracking MRV** serta **Algoritma Genetika (GA)** dengan **Operator Turnamen & Elitisme**.

---

## 📌 Deskripsi Masalah & Context Bisnis

Dalam operasional verifikasi klaim asuransi kesehatan Allianz, alokasi verifikator klaim (dokter examiner, spesialis fraud audit, supervisor persetujuan) dibatasi oleh regulasi ketat:
1. **Sertifikasi Kualifikasi**: Tahap `Verifikasi_RS` wajib dilakukan oleh verifikator bersertifikat medis (`Medical_Reviewer_Cert`), `Audit_Fraud` wajib oleh spesialis fraud (`Fraud_Audit_Cert`), dan `Persetujuan` oleh senior manager (`Senior_Approval_Cert`).
2. **Eksklusivitas Shift**: Seorang staf hanya dapat bertugas di satu tahap klaim pada slot waktu (hari & shift) yang sama.
3. **Batas Jam Kerja Ketenagakerjaan**: Staf tidak boleh melebihi kuota maksimum shift mingguan (maksimum 4-5 shift/minggu).
4. **Aturan Istirahat Wajib**: Staf yang bertugas pada Shift Malam Hari $D$ tidak boleh dijadwalkan pada Shift Pagi Hari $D+1$.

---

## 🧮 Pemodelan Matematis Formal

### 1. Formulasi CSP (Constraint Satisfaction Problem)
* **Variabel ($V$)**:
  $$V = \{ X_{s, d, t} \mid s \in \text{Stages}, d \in \{1 \dots D\}, t \in \text{Shifts} \}$$
  Dengan $\text{Stages} = \{\text{Cek\_Polis}, \text{Verifikasi\_RS}, \text{Audit\_Fraud}, \text{Persetujuan}\}$, $\text{Shifts} = \{\text{Pagi}, \text{Siang}, \text{Malam}\}$.

* **Domain ($D$)**:
  $$D(X_{s,d,t}) = \{ e \in \text{StaffPool} \mid \text{HasQual}(e, \text{ReqQual}(s)) \}$$

* **Batasan Ketat / Hard Constraints ($C_{\text{hard}}$)**:
  1. **Kualifikasi Khusus**: 
     $$\forall X_{s,d,t}, \quad \text{HasQual}(\text{Assign}(X_{s,d,t}), \text{ReqQual}(s)) = \text{True}$$
  2. **Eksklusivitas Shift**:
     $$\forall s_1 \neq s_2, \quad \text{Assign}(X_{s_1,d,t}) \neq \text{Assign}(X_{s_2,d,t})$$
  3. **Kapasitas Beban Kerja Maksimum**:
     $$\forall e \in \text{StaffPool}, \quad \sum_{v \in V} \mathbb{I}(\text{Assign}(v) = e) \le \text{MaxShifts}(e)$$
  4. **Periode Istirahat Antar Shift**:
     $$\text{Assign}(X_{s_1, d, \text{"Malam"}}) \neq \text{Assign}(X_{s_2, d+1, \text{"Pagi"}})$$

---

### 2. Skema Kromosom & Kebugaran GA (Genetic Algorithm)
* **Kromosom**: Vektor integer berukuran $N$ (di mana $N = |V|$), di mana elemen ke-$i$ merepresentasikan index staf dari domain terfilter yang dialokasikan pada variabel $V_i$.
* **Fungsi Kebugaran (Fitness Function)**:
  $$f(\text{Indiv}) = 1000 - (W_{\text{hard}} \times N_{\text{violations}}) + \text{Bonus}_{\text{pref}} - \text{Penalty}_{\text{fairness}}$$
  - $W_{\text{hard}} = 250.0$ (penalti per pelanggaran batasan ketat).
  - $\text{Bonus}_{\text{pref}} = +10.0$ per penyesuaian shift favorit staf.
  - $\text{Penalty}_{\text{fairness}} = 5.0 \times \text{Var}(\text{AssignedShifts})$ (pemerataan beban kerja).

---

## 🛠️ Arsitektur & Algoritma Engine (`solver.py`)

1. **CSP Solver (`CSPSolver`)**:
   - **AC-3 (Arc Consistency 3)**: Memangkas domain nilai secara berulang melalui propagasi batasan biner sebelum dan selama pencarian.
   - **Backtracking Search**: Menelusuri ruang pencarian keputusan.
   - **MRV (Minimum Remaining Values)**: Mengembangkan variabel dengan ukuran domain tersisa paling sedikit terlebih dahulu.
   - **Degree Heuristic**: Memecahkan *tie-breaking* berdasarkan variabel dengan jumlah batasan terbanyak terhadap variabel belum terisi.
   - **LCV (Least Constraining Value)**: Mengurutkan nilai domain yang meminimalkan konflik pada variabel tetangga.

2. **GA Solver (`GASolver`)**:
   - **Seleksi**: *k-Tournament Selection* ($k=5$).
   - **Rekombinasi**: *Two-Point Crossover* & *Uniform Crossover* dengan $P_c = 0.85$.
   - **Mutasi**: *Random Resetting & Swap Mutation* dengan $P_m = 0.05$.
   - **Elitisme**: Menyimpan $E=4$ individu terbaik tanpa perubahan ke generasi berikutnya.

---

## 📊 Hasil Analisis Sensitivitas & Performa

Pengujian dilakukan pada dua skala masalah:
* **Skala Kecil**: 3 Hari, 2 Shift, 4 Tahap Klaim (**24 Variabel**, 8 Staf).
* **Skala Besar**: 7 Hari, 3 Shift, 4 Tahap Klaim (**84 Variabel**, 24 Staf).

### Tabel Hasil Benchmark

| Metode Solver | Skala Masalah | Status Solusi | Waktu Eksekusi (ms) | Hard Violations | Node Expanded |
|---|---|---|---|---|---|
| **CSP (AC-3 + MRV)** | Small (24 Vars) | **Exact Solved** | **34.47 ms** | **0** | **24** |
| **GA (Elitism)** | Small (24 Vars) | Feasible Optimal | 4,469.48 ms | 0 | N/A |
| **CSP (AC-3 + MRV)** | Large (84 Vars) | **Exact Solved** | **3,835.36 ms** | **0** | **84** |
| **GA (Elitism)** | Large (84 Vars) | Approx Solution | 40,272.76 ms | 26 | N/A |

### Analisis Temuan:
1. **CSP (AC-3 + Backtracking MRV)** sangat unggul secara eksak (100% legal, 0 pelanggaran batasan) dan menyelesaikan masalah skala besar dalam 3.8 detik tanpa memerlukan *backtracking* tambahan berkat propagasi AC-3 yang presisi.
2. **Algoritma Genetika (GA)** berhasil menemukan solusi optimal pada skala kecil, namun memerlukan evaluasi generasi yang lebih lama pada skala besar untuk menghilangkan seluruh penalti batasan ketat.

---

## 🧪 Pengujian Otomatis & Kasus Ekstrem (*Edge Cases*)

Unit test otomatis disusun menggunakan `pytest` di [`tests/test_solver.py`](file:///c:/Users/ASUS/Documents/Semester%205/CERTAN/Tugas01_Milestone1/tests/test_solver.py):

* `test_ac3_domain_reduction`: Verifikasi pemangkasan domain oleh AC-3.
* `test_csp_backtracking_small_problem`: Solusi penuh tanpa pelanggaran pada skala kecil.
* `test_ga_solver_small_problem`: Uji konvergensi fitness per generasi pada GA.
* `test_edge_case_unsatisfiable_overconstrained`: Penanganan kasus jadwal tidak memungkinkan (over-constrained).
* `test_edge_case_empty_domain`: Penanganan variabel tanpa staf kualifikasi.
* `test_edge_case_single_variable`: Kasus minimal 1 variabel.
* `test_csp_and_ga_large_scale_stability`: Uji stabilitas memori & eksekusi pada 84 variabel.

### Menjalankan Pengujian:
```bash
.venv\Scripts\python.exe -m pytest tests/test_solver.py -v
```

### Menjalankan Benchmark:
```bash
.venv\Scripts\python.exe benchmark.py
```

### Menjalankan App Dashboard Streamlit:
```bash
.venv\Scripts\streamlit run app.py
```

---

## 📁 Struktur Repositori

```
Tugas01_Milestone1/
├── Alianz.py                   # Program utama Milestone 1 (UCS)
├── app.py                      # Interactive Streamlit Dashboard (Milestone 1 & 2)
├── benchmark.py                # Runner Analisis Sensitivitas & Benchmark Performa
├── solver.py                   # Top-level wrapper modul solver CSP & GA
├── pyproject.toml              # Definisi dependensi & proyek
├── README.md                   # Dokumentasi Laporan Proyek
├── src/
│   └── tugas02_milestone2/
│       ├── __init__.py         # Package init
│       ├── domain.py           # Pemodelan domain matematis, variabel & batasan
│       └── solver.py           # Modul algoritma AC-3, Backtracking MRV, dan GA Elitism
└── tests/
    └── test_solver.py          # Modul pengujian otomatis pytest (termasuk edge cases)
```

---

## 🏷️ GitHub Release Tag

Rilis ini telah di-tag dengan versi `v0.2-milestone2`:
```bash
git tag v0.2-milestone2
```
