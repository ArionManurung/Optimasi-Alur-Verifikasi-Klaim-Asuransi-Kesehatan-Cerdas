
from pathlib import Path
import json
import re

from .preprocessing import SOP_FILES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
OUTPUT_FILE = CHUNKS_DIR / "chunks.jsonl"

CHUNK_SIZE = 200
CHUNK_OVERLAP = 30


def remove_corpus_header(text: str) -> str:
    """Menghapus bagian header umum korpus sebelum isi SOP."""
    pattern = re.compile(
        r"\b1\.\s*KODE\s+DAN\s+JUDUL\s+DOKUMEN\b",
        re.IGNORECASE
    )
    match = pattern.search(text)

    if match:
        return text[match.start():].strip()

    return text.strip()


def get_document_title(text: str, filename: str) -> str:
    """Mengambil judul dokumen dari isi SOP."""
    match = re.search(
        r"Judul Dokumen\s*:\s*([^\n]+)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return filename.replace(".txt", "").replace("_", " ")


def split_into_sections(text: str) -> list[dict]:
    """
    Memisahkan dokumen berdasarkan judul bagian bernomor,
    misalnya 1. KODE DAN JUDUL DOKUMEN atau 2. TUJUAN.
    """
    heading_pattern = re.compile(
        r"(?m)^\s*(\d{1,2})\.\s+([A-Z][A-Z\s/&()-]*)\s*$"
    )

    matches = list(heading_pattern.finditer(text))

    if not matches:
        return [{"heading": "Isi Dokumen", "text": text.strip()}]

    sections = []

    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

        heading = f"{match.group(1)}. {match.group(2).strip()}"
        content = text[start:end].strip()

        sections.append({
            "heading": heading,
            "text": content
        })

    return sections


def recursive_split(text: str, max_words: int) -> list[str]:
    """
    Memecah teks secara bertahap:
    paragraf -> kalimat -> kata.
    """
    text = text.strip()

    if not text:
        return []

    if len(text.split()) <= max_words:
        return [text]

    paragraphs = re.split(r"\n\s*\n", text)

    if len(paragraphs) > 1:
        result = []
        for paragraph in paragraphs:
            result.extend(recursive_split(paragraph, max_words))
        return result

    sentences = re.split(r"(?<=[.!?])\s+", text)

    if len(sentences) > 1:
        result = []
        for sentence in sentences:
            result.extend(recursive_split(sentence, max_words))
        return result

    words = text.split()
    result = []

    for start in range(0, len(words), max_words):
        result.append(" ".join(words[start:start + max_words]))

    return result


def create_word_chunks(text: str, max_words: int) -> list[str]:
    """Menggabungkan potongan teks hingga batas kata tercapai."""
    pieces = recursive_split(text, max_words)

    chunks = []
    current_words = []

    for piece in pieces:
        piece_words = piece.split()

        if len(current_words) + len(piece_words) <= max_words:
            current_words.extend(piece_words)
        else:
            if current_words:
                chunks.append(" ".join(current_words))

            current_words = piece_words

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def add_overlap(chunks: list[str]) -> list[str]:
    """Menambahkan 30 kata terakhir dari chunk sebelumnya."""
    overlapped_chunks = []

    for index, chunk in enumerate(chunks):
        if index == 0:
            overlapped_chunks.append(chunk)
            continue

        previous_words = chunks[index - 1].split()
        current_words = chunk.split()

        overlap_words = previous_words[-CHUNK_OVERLAP:]
        combined_words = overlap_words + current_words

        overlapped_chunks.append(" ".join(combined_words))

    return overlapped_chunks


def create_chunks():
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []
    processed_documents = 0

    for filename in SOP_FILES:
        file_path = PROCESSED_DIR / filename

        if not file_path.exists():
            print(f"Dokumen tidak ditemukan: {filename}")
            continue

        text = file_path.read_text(encoding="utf-8")
        text = remove_corpus_header(text)

        document_id = filename.replace(".txt", "")
        document_title = get_document_title(text, filename)

        sections = split_into_sections(text)
        document_chunk_index = 0

        for section in sections:
            section_heading = section["heading"]
            section_text = section["text"]

            if not section_text:
                continue

            # Konteks judul dokumen dan bagian selalu disertakan.
            context = (
                f"Dokumen: {document_title}. "
                f"Bagian: {section_heading}."
            )

            context_word_count = len(context.split())
            body_limit = CHUNK_SIZE - context_word_count

            if body_limit <= CHUNK_OVERLAP:
                raise ValueError(
                    f"Konteks terlalu panjang pada {filename}: "
                    f"{section_heading}"
                )

            base_chunks = create_word_chunks(
                section_text,
                body_limit
            )

            # Overlap hanya dilakukan di dalam bagian yang sama.
            final_chunks = add_overlap(base_chunks)

            for chunk_text in final_chunks:
                document_chunk_index += 1

                full_text = f"{context} {chunk_text}"

                all_chunks.append({
                    "document_id": document_id,
                    "document_title": document_title,
                    "section": section_heading,
                    "source": filename,
                    "chunk_id": (
                        f"{document_id}_chunk_{document_chunk_index}"
                    ),
                    "chunk_index": document_chunk_index,
                    "text": full_text
                })

        processed_documents += 1

        document_total = sum(
            1 for chunk in all_chunks
            if chunk["source"] == filename
        )

        print(f"{filename}: {document_total} chunk")

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        for chunk in all_chunks:
            file.write(
                json.dumps(chunk, ensure_ascii=False) + "\n"
            )

    word_counts = [
        len(chunk["text"].split())
        for chunk in all_chunks
    ]

    print("\nChunking selesai!")
    print(f"Total dokumen: {processed_documents}")
    print(f"Total chunk: {len(all_chunks)}")
    print(f"Target ukuran dasar: {CHUNK_SIZE} kata")
    print(f"Overlap: {CHUNK_OVERLAP} kata")

    if word_counts:
        print(f"Kata minimum per chunk: {min(word_counts)}")
        print(f"Kata maksimum per chunk: {max(word_counts)}")
        print(
            "Chunk melebihi batas 230 kata: "
            f"{sum(count > 230 for count in word_counts)}"
        )

    print(f"Hasil disimpan di: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_chunks()
