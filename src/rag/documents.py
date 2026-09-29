from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"


# ============================================================
# DOCUMENT FILES
# ============================================================

DOCUMENT_FILES = [
    "company_profile.md",
    "faq.md",
    "delivery_policy.md",
    "payment_policy.md",
]


# ============================================================
# LOAD DOCUMENTS
# ============================================================

def load_documents():
    """
    Load all KenyaBiz AI business documents.

    Returns:
        list of dictionaries containing:
        - source
        - content
    """

    documents = []

    for filename in DOCUMENT_FILES:

        file_path = DATA_DIR / filename

        if not file_path.exists():
            print(
                f"Warning: document not found: "
                f"{file_path}"
            )
            continue

        content = file_path.read_text(
            encoding="utf-8"
        )

        documents.append(
            {
                "source": filename,
                "content": content,
            }
        )

    return documents


# ============================================================
# GET DOCUMENT
# ============================================================

def get_document(filename):
    """
    Load one specific business document.
    """

    file_path = DATA_DIR / filename

    if not file_path.exists():
        return None

    return file_path.read_text(
        encoding="utf-8"
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KENYABIZ AI")
    print("Business Document Loader")
    print("=" * 60)

    documents = load_documents()

    print()
    print(
        f"Loaded {len(documents)} document(s)."
    )

    print()

    for document in documents:

        print(
            f"- {document['source']}"
        )

    print()
    print("=" * 60)