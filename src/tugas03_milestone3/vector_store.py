
from pathlib import Path
import json

import chromadb

# Lokasi proyek
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# File hasil embedding
EMBEDDINGS_FILE = (
    PROJECT_ROOT / "data" / "embeddings" / "embeddings.jsonl"
)

# Folder database ChromaDB
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"

# Nama koleksi
COLLECTION_NAME = "knowledge_base_klaim_asuransi"


def load_embeddings():
    """Membaca dan memvalidasi data embedding."""

    if not EMBEDDINGS_FILE.exists():
        raise FileNotFoundError(
            f"File embedding tidak ditemukan: {EMBEDDINGS_FILE}"
        )

    with EMBEDDINGS_FILE.open("r", encoding="utf-8") as file:
        records = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    if not records:
        raise ValueError("Data embedding kosong.")

    ids = [record["chunk_id"] for record in records]

    if len(ids) != len(set(ids)):
        raise ValueError("Ditemukan ID chunk yang duplikat.")

    for record in records:
        required_fields = [
            "chunk_id",
            "document_id",
            "source",
            "chunk_index",
            "text",
            "embedding"
        ]

        for field in required_fields:
            if field not in record:
                raise ValueError(
                    f"Field {field} tidak ditemukan pada "
                    f"chunk {record.get('chunk_id', 'unknown')}."
                )

        if not record["text"].strip():
            raise ValueError(
                f"Teks kosong pada chunk {record['chunk_id']}."
            )

        if not record["embedding"]:
            raise ValueError(
                f"Embedding kosong pada chunk {record['chunk_id']}."
            )

    return records


def create_vector_database():
    """Menyimpan embedding dan metadata ke ChromaDB."""

    records = load_embeddings()

    print(f"Jumlah embedding dibaca: {len(records)}")

    # Membuat database permanen
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    # Membuat koleksi dengan cosine distance
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # Memastikan konfigurasi koleksi sesuai
    collection_metadata = collection.metadata or {}

    if collection_metadata.get("hnsw:space") != "cosine":
        raise ValueError(
            "Koleksi ChromaDB tidak menggunakan cosine distance. "
            "Gunakan koleksi baru dengan konfigurasi cosine."
        )

    # Menghapus data lama
    old_count = collection.count()

    if old_count > 0:
        old_ids = collection.get(
            limit=old_count
        )["ids"]

        collection.delete(ids=old_ids)

    print(f"Data lama dihapus: {old_count}")

    # Menyiapkan data
    ids = [record["chunk_id"] for record in records]

    documents = [record["text"] for record in records]

    embeddings = [
        record["embedding"]
        for record in records
    ]

    metadatas = [
        {
            "document_id": record["document_id"],
            "source": record["source"],
            "chunk_index": record["chunk_index"],
            "section": record.get("section", "Tidak diketahui")
        }
        for record in records
    ]

    # Menyimpan secara bertahap
    batch_size = 100

    for start in range(0, len(records), batch_size):
        end = min(start + batch_size, len(records))

        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end]
        )

        print(
            f"Berhasil menyimpan data "
            f"{start + 1} sampai {end}"
        )

    # Validasi hasil
    final_count = collection.count()

    print("\n=== VALIDASI CHROMADB ===")
    print(f"Jumlah embedding: {len(records)}")
    print(f"Jumlah data ChromaDB: {final_count}")
    print(f"Lokasi database: {CHROMA_DIR}")

    if final_count != len(records):
        raise RuntimeError(
            "Jumlah data ChromaDB tidak sesuai!"
        )

    # Memeriksa metadata
    sample = collection.get(
        limit=1,
        include=["metadatas"]
    )

    if not sample["metadatas"]:
        raise RuntimeError("Metadata tidak berhasil disimpan.")

    print("Contoh metadata:", sample["metadatas"][0])
    print("Validasi berhasil!")


if __name__ == "__main__":
    create_vector_database()
