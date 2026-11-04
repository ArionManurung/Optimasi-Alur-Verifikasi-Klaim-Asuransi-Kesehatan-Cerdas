
import json
from collections import defaultdict
from pathlib import Path

# Lokasi file hasil chunking
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_FILE = PROJECT_ROOT / "data" / "chunks" / "chunks.jsonl"

# Membaca seluruh chunk
documents = defaultdict(list)

with CHUNKS_FILE.open("r", encoding="utf-8") as file:
    for line in file:
        if line.strip():
            chunk = json.loads(line)
            documents[chunk["document_id"]].append(chunk)

# Memeriksa overlap setiap dokumen
total = 0
valid = 0
invalid = []

for document_id, chunks in documents.items():

    chunks.sort(key=lambda item: item["chunk_index"])

    for previous, current in zip(chunks, chunks[1:]):

        total += 1

        previous_words = previous["text"].split()
        current_words = current["text"].split()

        # Mengambil 30 kata terakhir dan 30 kata pertama
        expected_overlap = previous_words[-30:]
        actual_overlap = current_words[:30]

        if expected_overlap == actual_overlap:
            valid += 1
        else:
            invalid.append(
                (document_id, current["chunk_index"])
            )

# Menampilkan hasil pemeriksaan
print("\n=== HASIL PEMERIKSAAN OVERLAP ===")
print(f"Total pasangan chunk: {total}")
print(f"Overlap valid: {valid}")
print(f"Overlap tidak sesuai: {len(invalid)}")
print(f"Contoh yang tidak sesuai: {invalid[:5]}")
