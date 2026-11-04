
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# Lokasi proyek
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Lokasi database ChromaDB
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"

# Konfigurasi model dan koleksi
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "knowledge_base_klaim_asuransi"

# Batas similarity untuk memberi peringatan hasil pencarian
REJECTION_THRESHOLD = 0.50


def load_search_system():
    """Memuat model embedding dan database ChromaDB."""

    print("Memuat model embedding...")
    model = SentenceTransformer(MODEL_NAME)

    print("Menghubungkan ke ChromaDB...")
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    print(f"Jumlah data dalam ChromaDB: {collection.count()}")

    return model, collection


def semantic_search(query, model, collection, top_k=3):
    """Mencari chunk SOP berdasarkan kemiripan makna."""

    total_data = collection.count()

    if total_data == 0:
        print("Basis pengetahuan masih kosong.")
        return

    # Menyesuaikan jumlah hasil dengan data yang tersedia
    top_k = min(top_k, total_data)

    # Mengubah pertanyaan menjadi embedding
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )[0].tolist()

    # Mencari chunk paling relevan di ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    print("\n" + "=" * 60)
    print("PERTANYAAN:", query)
    print("=" * 60)

    if not results["ids"] or not results["ids"][0]:
        print("Tidak ditemukan hasil pencarian.")
        return

    best_similarity = 1 - results["distances"][0][0]

    # Memberi peringatan jika similarity hasil tertinggi rendah
    if best_similarity < REJECTION_THRESHOLD:
        print("\nPERINGATAN: Hasil pencarian belum cukup relevan.")
        print("Informasi yang ditemukan perlu diperiksa kembali.")
    else:
        print("\nHasil pencarian ditemukan.")

    # Menampilkan hasil pencarian
    for index, chunk_id in enumerate(results["ids"][0]):

        distance = results["distances"][0][index]

        # Mengubah cosine distance menjadi cosine similarity
        similarity = 1 - distance

        metadata = results["metadatas"][0][index]
        document = results["documents"][0][index]

        print(f"\n--- Peringkat {index + 1} ---")
        print("Dokumen:", metadata.get("source", "Tidak diketahui"))
        print("Bagian SOP:", metadata.get("section", "Tidak diketahui"))
        print("Chunk ID:", chunk_id)
        print(f"Cosine Similarity: {similarity:.4f}")
        print("Isi Chunk:")
        print(document)


if __name__ == "__main__":

    model, collection = load_search_system()

    print("\n=== PENGUJIAN SEMANTIC SEARCH ===")

    test_queries = [
        "Bagaimana cara memeriksa keaktifan polis asuransi?",
        "Bagaimana cara memeriksa apakah polis asuransi masih aktif?",
        "Bagaimana prosedur pemeriksaan status polis?"
    ]

    for query in test_queries:
        semantic_search(
            query=query,
            model=model,
            collection=collection,
            top_k=3
        )
