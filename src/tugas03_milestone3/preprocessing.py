from pathlib import Path
import re

# Lokasi folder proyek
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Folder yang berisi dokumen SOP
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"

# Folder untuk menyimpan hasil preprocessing
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Daftar 12 dokumen SOP utama yang akan diproses
SOP_FILES = [
    "SOP_01_Pengajuan_Klaim.txt",
    "SOP_02_Pemeriksaan_Status_Polis.txt",
    "SOP_03_Verifikasi_Dokumen_Medis_Tagihan_RS.txt",
    "SOP_04_Pre_Existing_Conditions.txt",
    "SOP_05_Policy_Exclusions.txt",
    "SOP_06_Fraud_Detection_Investigation.txt",
    "SOP_07_Claim_Benefit_Calculation.txt",
    "SOP_08_Claim_Dispute_and_Appeal.txt",
    "SOP_09_Cashless_and_Pre_Authorization.txt",
    "SOP_10_Claim_Approval_and_Disbursement.txt",
    "SOP_11_Claim_Submission_Deadline_and_Document_Completion.txt",
    "SOP_12_Hospital_Provider_Billing_and_Reconciliation.txt",
]


def clean_text(text: str) -> str:
    """Membersihkan format teks tanpa menghilangkan isi penting."""

    # Menghapus karakter spasi yang tidak diperlukan di awal dan akhir baris
    lines = [line.strip() for line in text.splitlines()]

    # Menghapus baris kosong berulang
    cleaned = "\n".join(line for line in lines if line)

    # Merapikan spasi berulang
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    return cleaned.strip()


def preprocess_documents():
    """Membaca dan membersihkan seluruh dokumen SOP utama."""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for filename in SOP_FILES:
        input_path = CORPUS_DIR / filename

        if not input_path.exists():
            print(f"Dokumen tidak ditemukan: {filename}")
            continue

        # Membaca dokumen dengan encoding UTF-8
        original_text = input_path.read_text(encoding="utf-8-sig")

        # Membersihkan teks
        cleaned_text = clean_text(original_text)

        # Menyimpan hasil ke folder processed
        output_path = PROCESSED_DIR / filename
        output_path.write_text(cleaned_text, encoding="utf-8")

        print(f"Berhasil diproses: {filename}")


if __name__ == "__main__":
    preprocess_documents()