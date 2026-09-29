import os
import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT CONVERSATION ENGINE
# ============================================================

from src.main import KenyaBizConversation


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="KenyaBiz AI",
    page_icon="🇰🇪",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */
    .stApp {
        background-color: #f7f9fc;
    }

    /* Main content width */
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Header */
    .kenyabiz-header {
        text-align: center;
        padding: 10px 0 25px 0;
    }

    .kenyabiz-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .kenyabiz-subtitle {
        font-size: 17px;
        color: #667085;
        margin-bottom: 10px;
    }

    /* Chat messages */
    .chat-user {
        background: #e8f1ff;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0 12px 60px;
    }

    .chat-ai {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 8px 60px 16px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .chat-label {
        font-size: 12px;
        font-weight: 700;
        color: #667085;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Information cards */
    .info-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
    }

    .info-title {
        font-size: 14px;
        font-weight: 700;
        color: #344054;
        margin-bottom: 8px;
    }

    .info-value {
        font-size: 18px;
        font-weight: 700;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }

    .sidebar-title {
        font-size: 22px;
        font-weight: 800;
        margin-bottom: 3px;
    }

    .sidebar-subtitle {
        color: #667085;
        font-size: 13px;
        margin-bottom: 20px;
    }

    /* Example questions */
    .example-box {
        background: #f8fafc;
        border: 1px solid #e4e7ec;
        border-radius: 10px;
        padding: 10px;
        margin: 6px 0;
        font-size: 13px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #98a2b3;
        font-size: 12px;
        margin-top: 35px;
        padding-top: 15px;
        border-top: 1px solid #eaecf0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "conversation" not in st.session_state:
    st.session_state.conversation = KenyaBizConversation()

if "messages" not in st.session_state:
    st.session_state.messages = []


conversation = st.session_state.conversation


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_currency(value):
    """Format a number as Kenyan Shillings."""
    try:
        return f"KES {float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def format_ai_response(response):
    """
    Improve common formatting problems from the backend
    while preserving the actual response content.
    """

    if not response:
        return ""

    # Normalize excessive blank lines
    response = response.replace("\r\n", "\n")

    # Add spacing around common order fields
    replacements = {
        "Order reference:": "\n\n**Order reference:**",
        "Customer:": "\n\n**Customer:**",
        "Subtotal:": "\n\n**Subtotal:**",
        "Delivery fee:": "\n\n**Delivery fee:**",
        "Total:": "\n\n**Total:**",
        "Order status:": "\n\n**Order status:**",
        "Payment reference:": "\n\n**Payment reference:**",
        "Amount:": "\n\n**Amount:**",
        "Payment method:": "\n\n**Payment method:**",
        "Payment status:": "\n\n**Payment status:**",
        "Invoice file:": "\n\n**Invoice file:**",
    }

    for old, new in replacements.items():
        response = response.replace(old, new)

    # Make common headings clearer
    response = response.replace(
        "Order items:",
        "\n\n### Order items"
    )

    response = response.replace(
        "Order summary:",
        "\n\n### Order summary"
    )

    return response.strip()


def get_invoice_path():
    """Return the current invoice path if available."""

    invoice_path = getattr(conversation, "invoice_path", None)

    if invoice_path:
        path = Path(invoice_path)

        if path.exists():
            return path

    return None


def reset_conversation():
    """Reset the conversation."""

    st.session_state.conversation = KenyaBizConversation()
    st.session_state.messages = []

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-title">
            🇰🇪 KenyaBiz AI
        </div>

        <div class="sidebar-subtitle">
            Multi-Agent Business Assistant
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🔄 New Conversation",
        use_container_width=True,
    ):
        reset_conversation()

    st.divider()

    st.markdown("### What I can do")

    st.markdown(
        """
        🛍️ **Product enquiries**  
        Check products, prices and stock.

        🧾 **Quotations & orders**  
        Build customer orders and calculate totals.

        📄 **Invoices**  
        Generate invoices for confirmed orders.

        💳 **Payments**  
        Create and track simulated M-PESA payments.

        🧭 **Step-by-step guidance**  
        Guide customers through the purchasing process.
        """
    )

    st.divider()

    st.markdown("### 💡 Try asking")

    examples = [
        "What office chairs do you have?",
        "How much is an office desk?",
        "I need 2 office chairs",
        "I need 2 office chairs and 1 office desk",
        "Generate an invoice",
        "I want to pay for my order",
    ]

    for example in examples:
        st.markdown(
            f"""
            <div class="example-box">
                {example}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Current order information
    order_reference = getattr(
        conversation,
        "order_reference",
        None,
    )

    order_status = getattr(
        conversation,
        "order_status",
        None,
    )

    payment_reference = getattr(
        conversation,
        "payment_reference",
        None,
    )

    if order_reference:

        st.markdown("### 📦 Current Order")

        st.info(
            f"**Order:** {order_reference}\n\n"
            f"**Status:** {order_status or 'PENDING'}"
        )

    if payment_reference:

        st.markdown("### 💳 Payment")

        st.success(
            f"**Payment reference:**\n\n"
            f"{payment_reference}"
        )

    # Invoice download
    invoice_path = get_invoice_path()

    if invoice_path:

        st.markdown("### 📄 Invoice")

        with open(invoice_path, "rb") as invoice_file:

            st.download_button(
                label="⬇️ Download Invoice",
                data=invoice_file.read(),
                file_name=invoice_path.name,
                mime="application/pdf",
                use_container_width=True,
            )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="kenyabiz-header">

        <div class="kenyabiz-title">
            🇰🇪 KenyaBiz AI
        </div>

        <div class="kenyabiz-subtitle">
            Multi-Agent Business Assistant for Kenyan SMEs
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# WELCOME MESSAGE
# ============================================================

if not st.session_state.messages:

    st.markdown(
        """
        <div class="info-card">

        <div class="info-title">
            👋 Welcome to KenyaBiz AI
        </div>

        I can help you with products, prices, quotations,
        orders, invoices and simulated M-PESA payments.

        <br><br>

        <strong>Try asking:</strong><br>
        "What office chairs do you have?"

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message["role"]
    content = message["content"]

    if role == "user":

        st.markdown(
            f"""
            <div class="chat-user">

                <div class="chat-label">
                    You
                </div>

                {content}

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        formatted = format_ai_response(content)

        st.markdown(
            f"""
            <div class="chat-ai">

                <div class="chat-label">
                    KenyaBiz AI
                </div>

                {formatted}

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_message = st.chat_input(
    "Ask KenyaBiz AI something..."
)


if user_message:

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    # Generate response
    with st.spinner("KenyaBiz AI is thinking..."):

        try:

            response = conversation.handle_message(
                user_message
            )

        except Exception as e:

            response = (
                "Sorry, I encountered an error while "
                f"processing your request.\n\n"
                f"Error: {e}"
            )

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        KenyaBiz AI • Multi-Agent SME Assistant<br>

        Built for Kenyan business workflows •
        M-PESA payments are simulated for demonstration

    </div>
    """,
    unsafe_allow_html=True,
)