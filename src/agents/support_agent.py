from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.rag.retriever import (
    retrieve_documents,
    format_context,
)


# ============================================================
# ENVIRONMENT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(
    PROJECT_ROOT / ".env"
)


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ============================================================
# ANSWER CUSTOMER QUESTION
# ============================================================

def answer_customer_question(
    customer_question,
    retrieved_documents=None,
    top_k=2,
):
    """
    Answer a customer question using the KenyaBiz AI
    business knowledge base.

    If retrieved_documents are not supplied, they are
    retrieved automatically.
    """

    if not customer_question:

        return (
            "Please provide a question so I can "
            "assist you."
        )

    # --------------------------------------------------------
    # STEP 1: RETRIEVE DOCUMENTS
    # --------------------------------------------------------

    if retrieved_documents is None:

        retrieved_documents = retrieve_documents(
            customer_question,
            top_k=top_k,
        )

    # --------------------------------------------------------
    # STEP 2: BUILD CONTEXT
    # --------------------------------------------------------

    context = format_context(
        retrieved_documents
    )

    # --------------------------------------------------------
    # STEP 3: NO RELEVANT INFORMATION
    # --------------------------------------------------------

    if not context:

        return (
            "I could not find enough information in "
            "the KenyaBiz AI business knowledge base "
            "to answer that question accurately."
        )

    # --------------------------------------------------------
    # STEP 4: LLM PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are the Support Agent for KenyaBiz AI,
a fictional Kenyan SME business assistant.

Your job is to answer the customer's question using
ONLY the business information provided in the context.

============================================================
RULES
============================================================

1. Use the provided context as your primary source of truth.

2. Do not invent company policies.

3. Do not invent prices.

4. Do not invent delivery times.

5. Do not invent payment methods.

6. Do not invent products or services.

7. If the requested information is not contained in
   the context, clearly say that the information is
   not available in the KenyaBiz AI knowledge base.

8. Do not guess.

9. Keep the response clear, concise, and customer-friendly.

10. Use KES when discussing prices.

11. KenyaBiz AI uses simulated payment functionality
    for this project.

12. Never claim that a real M-PESA transaction has
    been completed.

13. If the customer asks how to perform an action that
    requires another specialist, explain the relevant
    information from the knowledge base but do not
    pretend that the action has been performed.

============================================================
BUSINESS KNOWLEDGE
============================================================

{context}

============================================================
CUSTOMER QUESTION
============================================================

{customer_question}

============================================================
RESPONSE
============================================================

Provide a direct and helpful answer based only on
the business knowledge above.
"""

    try:

        response = llm.invoke(
            prompt
        )

        return response.content.strip()

    except Exception as exc:

        return (
            "I encountered an error while preparing "
            "your response. Please try again."
        )


# ============================================================
# SUPPORT RESPONSE WITH SOURCES
# ============================================================

def get_support_response(
    customer_question,
    top_k=2,
):
    """
    Retrieve documents once, generate an answer,
    and return both the answer and source information.
    """

    if not customer_question:

        return {
            "question": "",
            "answer": (
                "Please provide a question so I can "
                "assist you."
            ),
            "sources": [],
            "documents": [],
        }

    # --------------------------------------------------------
    # RETRIEVE ONCE
    # --------------------------------------------------------

    retrieved_documents = retrieve_documents(
        customer_question,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # GENERATE ANSWER USING SAME DOCUMENTS
    # --------------------------------------------------------

    answer = answer_customer_question(
        customer_question,
        retrieved_documents=retrieved_documents,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    sources = [
        document["source"]
        for document in retrieved_documents
    ]

    return {
        "question": customer_question,
        "answer": answer,
        "sources": sources,
        "documents": retrieved_documents,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("KENYABIZ AI")
    print("SUPPORT AGENT TEST")
    print("=" * 70)

    questions = [
        "What is KenyaBiz AI?",
        "How long does delivery take?",
        "Can I get an invoice?",
        "Do you support M-PESA?",
        "What currency do you use?",
        "How do I pay?",
        "What payment methods do you support?",
    ]

    for question in questions:

        print()
        print("-" * 70)

        print()
        print("CUSTOMER:")
        print(question)

        result = get_support_response(
            question
        )

        print()
        print("SUPPORT AGENT:")
        print(result["answer"])

        print()
        print("SOURCES:")

        if result["sources"]:

            for source in result["sources"]:

                print(
                    f"- {source}"
                )

        else:

            print("- No relevant sources found.")

    print()
    print("=" * 70)
    print("SUPPORT AGENT TEST COMPLETED")
    print("=" * 70)