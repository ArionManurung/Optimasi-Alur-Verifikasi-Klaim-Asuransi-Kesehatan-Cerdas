
import csv
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. PENGATURAN PROYEK
# ==========================================

ROOT_DIR = Path(__file__).resolve().parents[2]

CHROMA_DIR = ROOT_DIR / "data" / "chroma_db"
OUTPUT_DIR = ROOT_DIR / "data" / "benchmark"

COLLECTION_NAME = "knowledge_base_klaim_asuransi"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

TOP_K = 3

# Threshold sementara, akan dievaluasi kembali.
REJECTION_THRESHOLD = 0.50


# ==========================================
# 2. DATA PERTANYAAN BENCHMARK
# ==========================================

TEST_QUERIES = [
    {
        "id": 1,
        "category": "Relevan",
        "query": "Bagaimana prosedur pengajuan klaim reimbursement?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt"
        ],
    },
    {
        "id": 2,
        "category": "Sinonim",
        "query": "Bagaimana cara nasabah mendapatkan penggantian biaya pengobatan?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_10_Claim_Approval_and_Disbursement.txt"
        ],
    },
    {
        "id": 3,
        "category": "Relevan",
        "query": "Apa saja dokumen yang harus diserahkan untuk mengajukan klaim?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt"
        ],
    },
    {
        "id": 4,
        "category": "Relevan",
        "query": "Bagaimana cara memeriksa keaktifan polis asuransi?",
        "expected_sources": [
            "SOP_02_Pemeriksaan_Status_Polis.txt"
        ],
    },
    {
        "id": 5,
        "category": "Relevan",
        "query": "Bagaimana proses pemeriksaan indikasi kecurangan klaim?",
        "expected_sources": [
            "SOP_06_Fraud_Detection_Investigation.txt"
        ],
    },
    {
        "id": 6,
        "category": "Ambigu",
        "query": "Bagaimana cara mengecek status pengajuan klaim saya?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_10_Claim_Approval_and_Disbursement.txt",
            "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt"
        ],
    },
    {
        "id": 7,
        "category": "Ambigu",
        "query": "Mengapa pengajuan klaim saya belum selesai?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt"
        ],
    },
    {
        "id": 8,
        "category": "Out-of-domain",
        "query": "Bagaimana cara mendaftarkan kendaraan bermotor?",
        "expected_sources": [],
    },
    {
        "id": 9,
        "category": "Out-of-domain",
        "query": "Bagaimana prosedur pengajuan pinjaman pendidikan?",
        "expected_sources": [],
    },
    {
        "id": 10,
        "category": "Out-of-domain",
        "query": "Bagaimana cara menghitung pajak penghasilan?",
        "expected_sources": [],
    },
]


# ==========================================
# 3. MEMUAT MODEL DAN CHROMADB
# ==========================================

print("Memuat model embedding...")

model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

total_data = collection.count()

if total_data == 0:
    raise ValueError("ChromaDB belum memiliki data.")

print("Model dan ChromaDB berhasil dimuat.")
print(f"Jumlah data ChromaDB: {total_data}")


# ==========================================
# 4. MENJALANKAN BENCHMARK
# ==========================================

results = []

for test in TEST_QUERIES:

    query = test["query"]
    expected_sources = test["expected_sources"]

    # Mengubah pertanyaan menjadi embedding.
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )[0].tolist()

    # Menyesuaikan Top-K dengan jumlah data.
    current_top_k = min(TOP_K, total_data)

    # Mencari chunk paling relevan.
    search_result = collection.query(
        query_embeddings=[query_embedding],
        n_results=current_top_k,
        include=["documents", "metadatas", "distances"]
    )

    ids = search_result["ids"][0]
    documents = search_result["documents"][0]
    metadatas = search_result["metadatas"][0]
    distances = search_result["distances"][0]

    # Menghitung cosine similarity.
    similarities = [
        1 - distance for distance in distances
    ]

    retrieved_sources = [
        metadata.get("source", "Tidak diketahui")
        for metadata in metadatas
    ]

    best_similarity = (
        max(similarities) if similarities else 0.0
    )

    # Keputusan penerimaan atau penolakan.
    is_rejected = (
        best_similarity < REJECTION_THRESHOLD
    )

    # Evaluasi retrieval untuk pertanyaan dalam korpus.
    if expected_sources:

        relevant_ranks = [
            rank
            for rank, source in enumerate(
                retrieved_sources, start=1
            )
            if source in expected_sources
        ]

        is_relevant_found = len(relevant_ranks) > 0

        top1_correct = (
            retrieved_sources[0] in expected_sources
            if retrieved_sources else False
        )

        # Reciprocal rank:
        # 1 / posisi hasil relevan pertama.
        reciprocal_rank = (
            1 / relevant_ranks[0]
            if relevant_ranks else 0.0
        )

    else:
        is_relevant_found = None
        top1_correct = None
        reciprocal_rank = None

    # Menyimpan informasi hasil pencarian.
    retrieved_details = []

    for rank, (chunk_id, source, metadata, similarity) in enumerate(
        zip(ids, retrieved_sources, metadatas, similarities),
        start=1
    ):
        retrieved_details.append(
            f"{rank}. {source} | "
            f"{metadata.get('section', 'Tidak diketahui')} | "
            f"{chunk_id} | "
            f"{similarity:.4f}"
        )

    results.append({
        "id": test["id"],
        "category": test["category"],
        "query": query,
        "best_similarity": round(best_similarity, 4),
        "retrieved_results": " || ".join(retrieved_details),
        "expected_sources": "; ".join(expected_sources),
        "is_rejected": is_rejected,
        "is_relevant_found": is_relevant_found,
        "top1_correct": top1_correct,
        "reciprocal_rank": (
            round(reciprocal_rank, 4)
            if reciprocal_rank is not None else ""
        ),
    })

    # Menampilkan hasil pengujian.
    print("\n" + "=" * 65)
    print(f"PERTANYAAN {test['id']}: {query}")
    print(f"Kategori: {test['category']}")
    print(f"Similarity tertinggi: {best_similarity:.4f}")

    for rank, (source, metadata, similarity, document) in enumerate(
        zip(retrieved_sources, metadatas, similarities, documents),
        start=1
    ):
        print(f"\nPeringkat {rank}")
        print("Dokumen:", source)
        print(
            "Bagian SOP:",
            metadata.get("section", "Tidak diketahui")
        )
        print("Chunk ID:", ids[rank - 1])
        print(f"Cosine Similarity: {similarity:.4f}")
        print("Isi:", document[:250], "...")

    print(
        "\nKeputusan sistem:",
        "DITOLAK" if is_rejected else "DITERIMA"
    )

    if expected_sources:
        print(
            "Top-1:",
            "BENAR" if top1_correct else "SALAH"
        )

        print(
            "Hit@3:",
            "BERHASIL" if is_relevant_found else "GAGAL"
        )

        print(
            "Reciprocal Rank:",
            f"{reciprocal_rank:.4f}"
        )


# ==========================================
# 5. MENYIMPAN HASIL BENCHMARK
# ==========================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

output_file = OUTPUT_DIR / "benchmark_results.csv"

with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=results[0].keys()
    )

    writer.writeheader()
    writer.writerows(results)


# ==========================================
# 6. MENGHITUNG METRIK EVALUASI
# ==========================================

ood_results = [
    result for result in results
    if result["category"] == "Out-of-domain"
]

in_domain_results = [
    result for result in results
    if result["category"] != "Out-of-domain"
]


# ------------------------------------------
# A. EVALUASI PENOLAKAN OOD
# ------------------------------------------

# OOD yang benar-benar ditolak.
true_positive = sum(
    result["is_rejected"]
    for result in ood_results
)

# Pertanyaan dalam korpus yang salah ditolak.
false_positive = sum(
    result["is_rejected"]
    for result in in_domain_results
)

# Pertanyaan OOD yang salah diterima.
false_negative = (
    len(ood_results) - true_positive
)

# Pertanyaan dalam korpus yang benar diterima.
true_negative = (
    len(in_domain_results) - false_positive
)


# ------------------------------------------
# B. OOD PRECISION DAN RECALL
# ------------------------------------------

ood_precision = (
    true_positive / (true_positive + false_positive)
    if (true_positive + false_positive) > 0
    else 0
)

ood_recall = (
    true_positive / (true_positive + false_negative)
    if (true_positive + false_negative) > 0
    else 0
)


# ------------------------------------------
# C. AKURASI KEPUTUSAN SISTEM
# ------------------------------------------

correct_decisions = true_positive + true_negative

decision_accuracy = (
    correct_decisions / len(results)
    if results else 0
)


# ------------------------------------------
# D. EVALUASI RETRIEVAL
# ------------------------------------------

successful_retrieval = sum(
    bool(result["is_relevant_found"])
    for result in in_domain_results
)

top1_success = sum(
    bool(result["top1_correct"])
    for result in in_domain_results
)

hit_at_3 = (
    successful_retrieval / len(in_domain_results)
    if in_domain_results else 0
)

top1_accuracy = (
    top1_success / len(in_domain_results)
    if in_domain_results else 0
)

# Mean Reciprocal Rank.
mrr = (
    sum(
        result["reciprocal_rank"]
        for result in in_domain_results
    ) / len(in_domain_results)
    if in_domain_results else 0
)


# ==========================================
# 7. MENAMPILKAN RINGKASAN
# ==========================================

print("\n" + "=" * 65)
print("RINGKASAN EVALUASI BENCHMARK")
print("=" * 65)

print(f"Total pertanyaan: {len(results)}")
print(f"Pertanyaan dalam korpus: {len(in_domain_results)}")
print(f"Pertanyaan OOD: {len(ood_results)}")

print("\n--- EVALUASI RETRIEVAL ---")

print(
    f"Top-1 Accuracy: {top1_success}/"
    f"{len(in_domain_results)} "
    f"({top1_accuracy * 100:.2f}%)"
)

print(
    f"Hit@3: {successful_retrieval}/"
    f"{len(in_domain_results)} "
    f"({hit_at_3 * 100:.2f}%)"
)

print(f"MRR: {mrr:.4f}")

print("\n--- EVALUASI OOD ---")

print(
    f"OOD berhasil ditolak: "
    f"{true_positive}/{len(ood_results)}"
)

print(f"OOD Rejection Precision: {ood_precision * 100:.2f}%")
print(f"OOD Rejection Recall: {ood_recall * 100:.2f}%")

print("\n--- CONFUSION MATRIX KEPUTUSAN ---")

print(f"True Positive (OOD ditolak): {true_positive}")
print(f"False Positive (dalam korpus ditolak): {false_positive}")
print(f"True Negative (dalam korpus diterima): {true_negative}")
print(f"False Negative (OOD diterima): {false_negative}")

print("\n--- AKURASI KEPUTUSAN ---")

print(f"Decision Accuracy: {decision_accuracy * 100:.2f}%")

print("\n" + "=" * 65)
print("BENCHMARK SELESAI")
print("=" * 65)

print(f"Threshold sementara: {REJECTION_THRESHOLD}")
print(f"File hasil: {output_file}")
