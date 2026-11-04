
from pathlib import Path
import csv
import math
import re
from collections import Counter, defaultdict

import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. PENGATURAN PROYEK
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
BENCHMARK_DIR = PROJECT_ROOT / "data" / "benchmark"

OUTPUT_FILE = BENCHMARK_DIR / "benchmark_results_hybrid.csv"

COLLECTION_NAME = "knowledge_base_klaim_asuransi"

MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

TOP_K = 3
RETRIEVAL_CANDIDATES = 10
RRF_K = 60
REJECTION_THRESHOLD = 0.50


# ==========================================
# 2. DATA PERTANYAAN BENCHMARK
# ==========================================

TEST_QUERIES = [
    {
        "id": "Q1",
        "query": "Bagaimana prosedur pengajuan klaim reimbursement?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt",
        ],
        "type": "Relevant",
    },
    {
        "id": "Q2",
        "query": "Bagaimana cara nasabah mendapatkan penggantian biaya pengobatan?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_10_Claim_Approval_and_Disbursement.txt",
        ],
        "type": "Synonym",
    },
    {
        "id": "Q3",
        "query": "Dokumen apa saja yang harus diserahkan untuk mengajukan klaim?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt",
        ],
        "type": "Relevant",
    },
    {
        "id": "Q4",
        "query": "Bagaimana cara memeriksa apakah polis asuransi masih aktif?",
        "expected_sources": [
            "SOP_02_Pemeriksaan_Status_Polis.txt",
        ],
        "type": "Relevant",
    },
    {
        "id": "Q5",
        "query": "Bagaimana perusahaan mendeteksi kecurangan dalam pengajuan klaim?",
        "expected_sources": [
            "SOP_06_Fraud_Detection_Investigation.txt",
        ],
        "type": "Relevant",
    },
    {
        "id": "Q6",
        "query": "Bagaimana cara mengetahui status pengajuan klaim saya?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_10_Claim_Approval_and_Disbursement.txt",
            "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt",
        ],
        "type": "Ambiguous",
    },
    {
        "id": "Q7",
        "query": "Mengapa proses klaim saya belum selesai?",
        "expected_sources": [
            "SOP_01_Pengajuan_Klaim.txt",
            "SOP_10_Claim_Approval_and_Disbursement.txt",
            "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt",
        ],
        "type": "Ambiguous",
    },
    {
        "id": "Q8",
        "query": "Bagaimana cara mengurus perpanjangan STNK kendaraan?",
        "expected_sources": [],
        "type": "Out-of-domain",
    },
    {
        "id": "Q9",
        "query": "Bagaimana cara mengajukan pinjaman pendidikan?",
        "expected_sources": [],
        "type": "Out-of-domain",
    },
    {
        "id": "Q10",
        "query": "Bagaimana cara menghitung pajak penghasilan tahunan?",
        "expected_sources": [],
        "type": "Out-of-domain",
    },
]


# ==========================================
# 3. TOKENISASI
# ==========================================

def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


# ==========================================
# 4. ALGORITMA BM25
# ==========================================

class BM25:

    def __init__(self, documents, k1=1.5, b=0.75):

        self.documents = [
            tokenize(doc) for doc in documents
        ]

        self.k1 = k1
        self.b = b

        self.doc_lengths = [
            len(doc) for doc in self.documents
        ]

        self.avgdl = (
            sum(self.doc_lengths) / len(self.doc_lengths)
            if self.doc_lengths else 0
        )

        self.term_frequencies = [
            Counter(doc) for doc in self.documents
        ]

        self.document_frequency = Counter()

        for doc in self.documents:
            for term in set(doc):
                self.document_frequency[term] += 1

        self.total_documents = len(self.documents)

    def score(self, query):

        query_terms = tokenize(query)
        scores = []

        for index, frequencies in enumerate(
            self.term_frequencies
        ):

            score = 0.0
            doc_length = self.doc_lengths[index]

            for term in query_terms:

                frequency = frequencies.get(term, 0)

                if frequency == 0:
                    continue

                df = self.document_frequency[term]

                idf = math.log(
                    1 + (
                        self.total_documents - df + 0.5
                    ) / (df + 0.5)
                )

                length_factor = (
                    1 - self.b
                    + self.b * doc_length / self.avgdl
                    if self.avgdl else 1
                )

                denominator = (
                    frequency + self.k1 * length_factor
                )

                score += (
                    idf
                    * frequency
                    * (self.k1 + 1)
                    / denominator
                )

            scores.append(score)

        return scores


# ==========================================
# 5. MEMUAT CHROMADB DAN MODEL
# ==========================================

def load_resources():

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    data = collection.get(
        include=["documents", "metadatas"]
    )

    ids = data["ids"]
    documents = data["documents"]
    metadatas = data["metadatas"]

    if not ids:
        raise ValueError("ChromaDB tidak memiliki data.")

    if (
        len(ids) != len(documents)
        or len(ids) != len(metadatas)
    ):
        raise ValueError(
            "Jumlah ID, dokumen, dan metadata tidak sama."
        )

    if any(not doc for doc in documents):
        raise ValueError(
            "Terdapat dokumen kosong di ChromaDB."
        )

    if any(
        not metadata or "source" not in metadata
        for metadata in metadatas
    ):
        raise ValueError(
            "Metadata source tidak lengkap."
        )

    # Memastikan semua expected_sources tersedia di ChromaDB.
    available_sources = {
        metadata["source"] for metadata in metadatas
    }

    expected_sources = {
        source
        for test in TEST_QUERIES
        for source in test["expected_sources"]
    }

    missing_sources = (
        expected_sources - available_sources
    )

    if missing_sources:
        raise ValueError(
            "Sumber berikut tidak ditemukan di ChromaDB:\n"
            + "\n".join(sorted(missing_sources))
        )

    print(f"Jumlah data ChromaDB: {len(ids)}")
    print(f"Jumlah dokumen sumber: {len(available_sources)}")
    print("Validasi expected_sources berhasil.")
    print("Memuat model embedding...")

    model = SentenceTransformer(MODEL_NAME)

    print("Membangun indeks BM25...")

    bm25 = BM25(documents)

    return collection, model, bm25, ids, documents, metadatas


# ==========================================
# 6. DENSE SEARCH
# ==========================================

def dense_search(collection, model, query):

    query_vector = model.encode(
        [query],
        normalize_embeddings=True
    )

    results = collection.query(
        query_embeddings=query_vector.tolist(),
        n_results=min(
            RETRIEVAL_CANDIDATES,
            collection.count()
        ),
        include=["metadatas", "distances"]
    )

    retrieved = []

    for index, metadata in enumerate(
        results["metadatas"][0]
    ):

        retrieved.append({
            "id": results["ids"][0][index],
            "source": metadata["source"],
            "score": (
                1 - results["distances"][0][index]
            ),
            "rank": index + 1,
        })

    return retrieved


# ==========================================
# 7. BM25 SEARCH
# ==========================================

def bm25_search(bm25, ids, metadatas, query):

    scores = bm25.score(query)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:RETRIEVAL_CANDIDATES]

    retrieved = []

    for index in ranked_indices:

        if scores[index] <= 0:
            continue

        retrieved.append({
            "id": ids[index],
            "source": metadatas[index]["source"],
            "score": scores[index],
            "rank": len(retrieved) + 1,
        })

    return retrieved


# ==========================================
# 8. MENGUBAH CHUNK MENJADI DOKUMEN UNIK
# ==========================================

def collapse_to_documents(results):

    document_results = {}

    for item in results:

        source = item["source"]

        if source not in document_results:
            document_results[source] = {
                "source": source,
                "score": item["score"],
                "best_chunk_id": item["id"],
            }

        elif item["score"] > document_results[source]["score"]:
            document_results[source]["score"] = item["score"]
            document_results[source]["best_chunk_id"] = item["id"]

    ranked_documents = sorted(
        document_results.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    for rank, item in enumerate(
        ranked_documents,
        start=1
    ):
        item["rank"] = rank

    return ranked_documents


# ==========================================
# 9. HYBRID SEARCH DENGAN RRF
# ==========================================

def hybrid_search(dense_results, bm25_results):

    chunk_scores = defaultdict(float)
    chunk_sources = {}

    for results in [dense_results, bm25_results]:

        for item in results:

            chunk_id = item["id"]

            chunk_scores[chunk_id] += (
                1 / (RRF_K + item["rank"])
            )

            chunk_sources[chunk_id] = item["source"]

    # Mengambil skor RRF tertinggi untuk setiap dokumen.
    # Menghindari keuntungan hanya karena jumlah chunk lebih banyak.

    document_scores = {}

    for chunk_id, score in chunk_scores.items():

        source = chunk_sources[chunk_id]

        if (
            source not in document_scores
            or score > document_scores[source]["score"]
        ):
            document_scores[source] = {
                "source": source,
                "score": score,
                "best_chunk_id": chunk_id,
            }

    ranked_documents = sorted(
        document_scores.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    for rank, item in enumerate(
        ranked_documents,
        start=1
    ):
        item["rank"] = rank

    return ranked_documents


# ==========================================
# 10. EVALUASI DOKUMEN UNIK
# ==========================================

def evaluate(results, expected_sources):

    if not expected_sources:
        return {
            "top1": None,
            "hit_at_3": None,
            "rr": None,
        }

    retrieved_sources = [
        item["source"]
        for item in results[:TOP_K]
    ]

    top1 = (
        bool(retrieved_sources)
        and retrieved_sources[0] in expected_sources
    )

    hit_at_3 = any(
        source in expected_sources
        for source in retrieved_sources
    )

    reciprocal_rank = 0.0

    for rank, source in enumerate(
        retrieved_sources,
        start=1
    ):

        if source in expected_sources:
            reciprocal_rank = 1 / rank
            break

    return {
        "top1": int(top1),
        "hit_at_3": int(hit_at_3),
        "rr": reciprocal_rank,
    }


# ==========================================
# 11. MENAMPILKAN HASIL
# ==========================================

def display_results(method, results):

    print(f"\n{method}:")

    for item in results[:TOP_K]:

        print(
            f"  Rank {item['rank']}: "
            f"{item['source']} "
            f"(score: {item['score']:.4f})"
        )


# ==========================================
# 12. MENJALANKAN BENCHMARK
# ==========================================

def run_benchmark():

    (
        collection,
        model,
        bm25,
        ids,
        documents,
        metadatas,
    ) = load_resources()

    rows = []

    methods = {
        "Dense": [],
        "BM25": [],
        "Hybrid": [],
    }

    ood_correct = 0
    ood_total = 0

    print(
        "\n========== HASIL HYBRID BENCHMARK =========="
    )

    for test in TEST_QUERIES:

        query = test["query"]
        expected = test["expected_sources"]

        # Pencarian berdasarkan chunk.
        dense_chunks = dense_search(
            collection, model, query
        )

        bm25_chunks = bm25_search(
            bm25, ids, metadatas, query
        )

        # Semua metode diubah menjadi dokumen unik.
        dense_results = collapse_to_documents(
            dense_chunks
        )

        bm25_results = collapse_to_documents(
            bm25_chunks
        )

        hybrid_results = hybrid_search(
            dense_chunks,
            bm25_chunks
        )

        all_results = {
            "Dense": dense_results,
            "BM25": bm25_results,
            "Hybrid": hybrid_results,
        }

        print(f"\n{test['id']} - {test['type']}")
        print(f"Pertanyaan: {query}")

        for method, results in all_results.items():

            metrics = evaluate(results, expected)

            methods[method].append(metrics)

            display_results(method, results)

            top_sources = [
                item["source"]
                for item in results[:TOP_K]
            ]

            rows.append({
                "query_id": test["id"],
                "query": query,
                "type": test["type"],
                "method": method,
                "expected_sources": ";".join(expected),
                "retrieved_sources": ";".join(top_sources),
                "top1_correct": metrics["top1"],
                "hit_at_3": metrics["hit_at_3"],
                "reciprocal_rank": metrics["rr"],
            })

        # OOD tetap menggunakan similarity Dense.
        if test["type"] == "Out-of-domain":

            ood_total += 1

            best_similarity = (
                dense_chunks[0]["score"]
                if dense_chunks else 0
            )

            rejected = (
                best_similarity < REJECTION_THRESHOLD
            )

            if rejected:
                ood_correct += 1

            print(
                f"\nOOD Dense similarity: "
                f"{best_similarity:.4f}"
            )

            print(f"Ditolak sistem: {rejected}")

    # ======================================
    # 13. RINGKASAN METRIK
    # ======================================

    print(
        "\n========== RINGKASAN METRIK =========="
    )

    for method, results in methods.items():

        valid_results = [
            item for item in results
            if item["top1"] is not None
        ]

        if not valid_results:
            continue

        total = len(valid_results)

        top1_accuracy = (
            sum(item["top1"] for item in valid_results)
            / total * 100
        )

        hit_at_3 = (
            sum(item["hit_at_3"] for item in valid_results)
            / total * 100
        )

        mrr = (
            sum(item["rr"] for item in valid_results)
            / total
        )

        print(f"\n{method}:")
        print(f"Top-1 Accuracy: {top1_accuracy:.2f}%")
        print(f"Hit@3: {hit_at_3:.2f}%")
        print(f"MRR: {mrr:.4f}")

    # ======================================
    # 14. RINGKASAN OOD
    # ======================================

    ood_accuracy = (
        ood_correct / ood_total * 100
        if ood_total else 0
    )

    print("\nOOD Rejection:")
    print(f"Berhasil ditolak: {ood_correct}/{ood_total}")
    print(f"Tingkat penolakan OOD: {ood_accuracy:.2f}%")

    # ======================================
    # 15. MENYIMPAN CSV
    # ======================================

    BENCHMARK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        fieldnames = [
            "query_id",
            "query",
            "type",
            "method",
            "expected_sources",
            "retrieved_sources",
            "top1_correct",
            "hit_at_3",
            "reciprocal_rank",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"\nHasil benchmark disimpan di: {OUTPUT_FILE}"
    )


# ==========================================
# 16. PROGRAM UTAMA
# ==========================================

if __name__ == "__main__":
    run_benchmark()
