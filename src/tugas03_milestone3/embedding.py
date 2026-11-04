
from pathlib import Path
import json

from sentence_transformers import SentenceTransformer

# Lokasi proyek
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# File hasil chunking
CHUNKS_FILE = PROJECT_ROOT / "data" / "chunks" / "chunks.jsonl"

# Lokasi penyimpanan embedding
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"
OUTPUT_FILE = EMBEDDINGS_DIR / "embeddings.jsonl"

# Model embedding multilingual
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def create_embeddings():
    """Mengubah setiap chunk teks menjadi vektor embedding."""

    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    # Membaca seluruh chunk
    with CHUNKS_FILE.open("r", encoding="utf-8") as file:
        chunks = [json.loads(line) for line in file if line.strip()]

    print(f"Jumlah chunk yang akan diproses: {len(chunks)}")

    # Memuat model embedding
    print("Memuat model Sentence Transformers...")
    model = SentenceTransformer(MODEL_NAME)

    # Mengambil teks dari setiap chunk
    texts = [chunk["text"] for chunk in chunks]

    # Mengubah teks menjadi vektor
    print("Sedang membuat embedding...")
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    # Menyimpan teks, metadata, dan vektor
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        for chunk, vector in zip(chunks, vectors):
            result = {
                **chunk,
                "embedding": vector.tolist()
            }

            file.write(json.dumps(result, ensure_ascii=False) + "\n")

    print("\nEmbedding selesai!")
    print(f"Total embedding: {len(vectors)}")
    print(f"Dimensi vektor: {vectors.shape[1]}")
    print(f"Hasil disimpan di: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_embeddings()
