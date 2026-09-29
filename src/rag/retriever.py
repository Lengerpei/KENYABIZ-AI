import re

from src.rag.documents import load_documents


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize text for keyword-based retrieval.
    """

    if not text:
        return ""

    text = text.lower()

    # Normalize common business terminology
    replacements = {
        "payments": "payment",
        "paying": "payment",
        "paid": "payment",
        "pay": "payment",

        "deliveries": "delivery",
        "delivered": "delivery",
        "delivering": "delivery",

        "invoices": "invoice",
        "invoicing": "invoice",

        "customers": "customer",
        "businesses": "business",
        "products": "product",
        "services": "service",

        "orders": "order",
        "ordering": "order",

        "refunds": "refund",
        "refunded": "refund",

        "questions": "question",
        "answers": "answer",
    }

    for old, new in replacements.items():
        text = re.sub(
            rf"\b{re.escape(old)}\b",
            new,
            text
        )

    # Remove punctuation
    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    # Remove extra whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "the",
    "is",
    "are",
    "was",
    "were",
    "a",
    "an",
    "and",
    "or",
    "but",
    "to",
    "of",
    "in",
    "on",
    "at",
    "for",
    "with",
    "from",
    "by",
    "can",
    "could",
    "would",
    "should",
    "i",
    "you",
    "we",
    "they",
    "do",
    "does",
    "did",
    "what",
    "where",
    "when",
    "why",
    "how",
    "your",
    "our",
    "their",
    "me",
    "my",
    "please",
    "tell",
    "about",
    "much",
    "many",
}


# ============================================================
# IMPORTANT BUSINESS TERMS
# ============================================================

IMPORTANT_TERMS = {
    "payment",
    "mpesa",
    "invoice",
    "delivery",
    "order",
    "refund",
    "price",
    "cost",
    "business",
    "service",
    "product",
    "customer",
    "location",
    "contact",
    "support",
}


# ============================================================
# EXTRACT QUERY WORDS
# ============================================================

def extract_query_words(query):
    """
    Extract meaningful words from the user's question.
    """

    normalized_query = normalize_text(query)

    words = normalized_query.split()

    return {
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 1
    }


# ============================================================
# SCORE DOCUMENT
# ============================================================

def score_document(query_words, document_content):
    """
    Calculate relevance score between a query and document.

    Exact keyword matches receive one point.
    Important business terms receive an additional point.
    """

    normalized_content = normalize_text(
        document_content
    )

    document_words = set(
        normalized_content.split()
    )

    matching_words = (
        query_words & document_words
    )

    score = 0

    for word in matching_words:

        score += 1

        if word in IMPORTANT_TERMS:
            score += 2

    return score, matching_words


# ============================================================
# RETRIEVE DOCUMENTS
# ============================================================

def retrieve_documents(
    query,
    top_k=2,
    min_score=1
):
    """
    Retrieve the most relevant business documents.

    Uses lightweight keyword-based retrieval.

    Args:
        query:
            Customer question.

        top_k:
            Maximum number of documents to return.

        min_score:
            Minimum relevance score required.

    Returns:
        List of relevant documents.
    """

    if not query:
        return []

    documents = load_documents()

    if not documents:
        return []

    query_words = extract_query_words(query)

    if not query_words:
        return []

    scored_documents = []

    for document in documents:

        score, matching_words = score_document(
            query_words,
            document["content"]
        )

        if score >= min_score:

            scored_documents.append(
                {
                    "source": document["source"],
                    "content": document["content"],
                    "score": score,
                    "matching_words": sorted(
                        matching_words
                    ),
                }
            )

    # Highest score first
    scored_documents.sort(
        key=lambda document: document["score"],
        reverse=True
    )

    return scored_documents[:top_k]


# ============================================================
# FORMAT CONTEXT
# ============================================================

def format_context(documents):
    """
    Convert retrieved documents into context
    for the LLM.
    """

    if not documents:
        return ""

    context_parts = []

    for document in documents:

        context_parts.append(
            f"--- SOURCE: {document['source']} ---\n"
            f"{document['content']}"
        )

    return "\n\n".join(context_parts)


# ============================================================
# TEST RETRIEVER
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("KENYABIZ AI")
    print("RAG RETRIEVER TEST")
    print("=" * 70)

    questions = [
        "What payment methods do you support?",
        "How can I pay?",
        "Can I pay using M-Pesa?",
        "How long does delivery take?",
        "When will my order arrive?",
        "What does KenyaBiz AI do?",
        "Can I get an invoice?",
        "How do I get my invoice?",
        "What happens if I want a refund?",
    ]

    for question in questions:

        print()
        print("-" * 70)

        print("QUESTION:")
        print(question)

        results = retrieve_documents(
            question,
            top_k=2
        )

        print()
        print("RETRIEVED DOCUMENTS:")

        if not results:

            print("No relevant documents found.")

            continue

        for result in results:

            print(
                f"- {result['source']} "
                f"(score={result['score']}, "
                f"matches={result['matching_words']})"
            )

    print()
    print("=" * 70)
    print("RETRIEVER TEST COMPLETE")
    print("=" * 70)