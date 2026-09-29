# KenyaBiz AI 🇰🇪

## Multi-Agent AI Business Assistant for Kenyan SMEs

KenyaBiz AI is a multi-agent business assistant designed to support Kenyan small and medium-sized enterprises (SMEs) with common business operations.

The system combines **Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), LangGraph, structured tools, and business workflow automation** to provide a conversational interface for product enquiries, quotations, orders, invoices, payments, and customer support.

The project is developed as an AI agent capstone demonstrating how multiple specialized agents can work together to complete an end-to-end business workflow.

---

## Project Overview

Small businesses frequently handle customer enquiries, product pricing, quotations, orders, invoices, and payment follow-ups manually.

KenyaBiz AI demonstrates how these activities can be coordinated through an intelligent multi-agent system.

A customer can interact with the system using natural language, for example:

> "What products do you have?"

> "How much is an office chair?"

> "I need 5 office chairs and 2 office desks."

> "I want to order 2 office chairs."

> "Generate an invoice for my order."

> "I want to pay for my order."

The system determines the appropriate business function and routes the request to the relevant specialized agent.

---

## Key Features

### 1. Multi-Agent Architecture

KenyaBiz AI uses specialized agents for different business functions:

* **Supervisor Agent** — determines which specialist should handle a request.
* **Customer Support Agent** — answers company, FAQ, delivery, and payment-policy questions using the knowledge base.
* **Sales Agent** — handles product enquiries, prices, stock information, searches, recommendations, and quotations.
* **Order Agent** — processes customer orders and validates products, quantities, and stock.
* **Invoice Agent** — generates invoices for completed orders.
* **Payment Agent** — manages the simulated M-PESA-style payment workflow.

---

## 2. Product Catalogue

The system maintains a product catalogue containing products, prices, stock information, product IDs, and product descriptions.

Example products include:

| Product        | ID   |      Price |
| -------------- | ---- | ---------: |
| Office Chair   | P001 |  KES 8,500 |
| Office Desk    | P002 | KES 15,000 |
| Laptop Stand   | P003 |  KES 4,500 |
| Office Cabinet | P004 | KES 18,000 |
| Visitor Chair  | P005 |  KES 5,500 |
| Executive Desk | P006 | KES 35,000 |
| Monitor Stand  | P007 |  KES 3,500 |
| Keyboard       | P008 |  KES 2,800 |
| Wireless Mouse | P009 |  KES 1,800 |
| Meeting Table  | P010 | KES 45,000 |

The catalogue can be used for:

* Product searches
* Price enquiries
* Stock checks
* Product recommendations
* Quotations

---

## 3. Automated Quotations

The Sales Agent can extract quantities and products from natural-language requests.

For example:

```text
I need 5 office chairs and 2 office desks.
```

The system produces:

```text
Quotation

Office Chair: 5 × KES 8,500.00 = KES 42,500.00
Office Desk: 2 × KES 15,000.00 = KES 30,000.00

Subtotal: KES 72,500.00
Delivery: KES 2,500.00
Total: KES 75,000.00
```

The quotation functionality supports multiple products and calculates the subtotal, delivery fee, and total.

---

## 4. Retrieval-Augmented Generation (RAG)

The Customer Support Agent uses a business knowledge base to answer questions about KenyaBiz.

The knowledge base currently includes:

```text
data/
├── company_profile.md
├── faq.md
├── delivery_policy.md
├── payment_policy.md
└── products.csv
```

The RAG workflow is designed to provide answers grounded in the available KenyaBiz business information rather than relying only on the language model's general knowledge.

The knowledge base covers areas such as:

* Company information
* Frequently asked questions
* Delivery policies
* Payment policies
* Product information

---

## 5. Order Processing

Customers can initiate orders using natural language.

Example:

```text
I want to order 2 office chairs.
```

The Order Agent handles:

* Product identification
* Quantity validation
* Stock validation
* Customer information
* Order confirmation
* Order creation
* Order reference generation

Orders use references in the format:

```text
KBA-YYYYMMDD-XXXX
```

Example:

```text
KBA-20260929-J6E1
```

---

## 6. Invoice Generation

After an order is created, the Invoice Agent can generate an invoice using the order reference.

Example:

```text
Generate invoice for KBA-20260929-J6E1
```

The system generates a PDF invoice containing information such as:

* Order reference
* Customer
* Ordered products
* Quantities
* Product prices
* Subtotal
* Delivery fee
* Total amount

Generated invoices are stored in the project's invoice directory.

---

## 7. Simulated M-PESA Payment Workflow

KenyaBiz AI includes a simulated M-PESA-style payment workflow for demonstration purposes.

The system can:

* Create a payment request
* Generate a payment reference
* Associate the payment with an order
* Display the payment amount
* Track payment status

Example:

```text
Payment reference: MPSP91GE12F
Payment status: PENDING
Payment method: M-PESA-SIMULATION
```

This is a **simulation for the AI capstone** and does not connect to the real M-PESA payment infrastructure.

---

# System Architecture

The system uses a supervisor-based multi-agent architecture implemented with LangGraph.

```text
                         CUSTOMER
                            │
                            ▼
                    ┌───────────────┐
                    │   SUPERVISOR  │
                    │     AGENT     │
                    └───────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     ┌─────────┐       ┌─────────┐       ┌─────────┐
     │ SUPPORT │       │  SALES  │       │  ORDER  │
     │  AGENT  │       │  AGENT  │       │  AGENT  │
     └────┬────┘       └────┬────┘       └────┬────┘
          │                 │                 │
          ▼                 ▼                 ▼
        RAG             PRODUCTS           ORDERS
      KNOWLEDGE        QUOTATIONS         VALIDATION
        BASE
                            │
                            │
                            ▼
                     ┌─────────────┐
                     │   INVOICE   │
                     │    AGENT    │
                     └──────┬──────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   PAYMENT   │
                     │    AGENT    │
                     └─────────────┘
```

---

# Technology Stack

## Programming Language

* Python 3.12

## AI and Agent Frameworks

* LangGraph
* LangChain
* LangChain Groq
* Groq LLMs

## Retrieval / RAG

* Retrieval-based business knowledge system
* Product and business-policy knowledge base
* Vector/retrieval components included in the project dependencies

## Data and Storage

* CSV product catalogue
* Markdown knowledge-base documents
* SQL database schema
* File-based invoice generation

## Testing

* pytest

## Interface

* Python command-line interface
* Streamlit components/dependencies for application interface development

---

# Project Structure

```text
KENYABIZ-AI/
│
├── data/
│   ├── company_profile.md
│   ├── delivery_policy.md
│   ├── faq.md
│   ├── payment_policy.md
│   └── products.csv
│
├── src/
│   ├── agents/
│   ├── tools/
│   ├── graph.py
│   ├── state.py
│   ├── main.py
│   └── ...
│
├── tests/
│   ├── test_agents.py
│   ├── test_products.py
│   ├── test_quotation.py
│   └── ...
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

> The exact contents of `src/` may evolve as the project continues through evaluation and refinement.

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/Lengerpei/KENYABIZ-AI.git
cd KENYABIZ-AI
```

## 2. Create a virtual environment

Python 3.12 is recommended.

### Windows PowerShell

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

Add the required API credentials, for example:

```text
GROQ_API_KEY=your_groq_api_key
```

Do not commit `.env` or API keys to GitHub.

The repository `.gitignore` excludes environment files from version control.

---

# Running the Application

From the project root:

```powershell
python -m src.main
```

The application starts an interactive conversational interface.

Example:

```text
======================================================================
KENYABIZ AI
MULTI-AGENT BUSINESS ASSISTANT
======================================================================

Welcome to KenyaBiz AI.

You: What products do you have?
```

The user can type:

```text
exit
```

or:

```text
quit
```

to end the session.

---

# Example Business Workflow

A typical customer interaction can follow this workflow:

```text
Customer
   │
   ▼
Product enquiry
   │
   ▼
Sales Agent
   │
   ▼
Quotation
   │
   ▼
Order request
   │
   ▼
Order Agent
   │
   ▼
Order reference
   │
   ▼
Invoice Agent
   │
   ▼
PDF invoice
   │
   ▼
Payment Agent
   │
   ▼
Simulated M-PESA payment
```

---

# Testing

The project uses pytest for automated testing.

Run the complete test suite:

```powershell
pytest -v
```

Run the agent tests:

```powershell
pytest tests\test_agents.py -v
```

The current development baseline has:

```text
186 tests passed
```

This confirms that the current automated unit and integration test suite passes successfully.

Further evaluation will be conducted separately to measure the performance of the AI agents and RAG system on realistic user scenarios.

---

# Testing Areas

The automated tests currently cover areas including:

### Sales

* Product identification
* Product aliases
* Quantity extraction
* Multi-product quantities
* Product catalogue
* Price requests
* Stock requests
* Product search
* Recommendations
* Quotations
* Sales request classification

### Orders

* Product validation
* Quantity validation
* Stock validation
* Product matching
* Order creation
* Order references
* Order response formatting

### Support

* Knowledge-base retrieval
* Support responses
* Fallback handling

### Invoice

* Invoice generation
* Order lookup
* Invoice formatting

### Payment

* Payment request creation
* Payment references
* Payment status
* Order/payment association

### Integration

* Agent interaction
* Workflow execution
* Business process validation

---

# Evaluation

The automated test suite verifies software correctness, while the AI evaluation phase will assess the quality of the AI system itself.

Planned evaluation areas include:

* Supervisor routing accuracy
* Sales response accuracy
* Product identification accuracy
* Quotation accuracy
* RAG faithfulness
* RAG answer relevancy
* Knowledge-base retrieval quality
* Order workflow success
* Invoice workflow success
* Payment workflow success
* End-to-end task completion

The evaluation results will be added to the repository after the evaluation phase is completed.

---

# Current Development Status

The core KenyaBiz AI multi-agent workflow is operational.

### Completed

* Multi-agent architecture
* Supervisor routing
* Customer support functionality
* Business knowledge base
* Product catalogue
* Sales agent
* Product search
* Price enquiries
* Stock checks
* Product recommendations
* Multi-product quotations
* Order processing
* Invoice generation
* Simulated payment workflow
* LangGraph orchestration
* Automated tests
* GitHub repository

### In Progress

* AI/RAG evaluation
* End-to-end evaluation
* Evaluation dataset
* Error analysis
* Conversation-flow refinement
* Final documentation
* Architecture documentation
* Final demonstration preparation

---

# Known Limitations

The current project is a capstone demonstration rather than a production commerce platform.

Current limitations include:

* The payment workflow is simulated and does not connect to real M-PESA.
* Customer order conversations require further refinement for some confirmation and customer-information scenarios.
* The AI evaluation baseline is still being developed.
* The application does not yet represent a production-grade payment or order-management infrastructure.
* Business data is demonstration data rather than a live enterprise database.
* Additional security, authentication, monitoring, logging, and deployment controls would be required for production use.

---

# Future Improvements

Potential future improvements include:

* Real M-PESA API integration
* Persistent customer accounts
* Production database integration
* Improved conversational state management
* Better customer-information collection
* Real-time inventory management
* Delivery tracking
* Authentication and authorization
* Admin dashboard
* Analytics and reporting
* Improved RAG evaluation
* Automated agent evaluation
* Cloud deployment
* Production monitoring and logging

---

# Project Objectives

The project aims to demonstrate practical application of:

* Multi-agent AI systems
* Agent orchestration
* Retrieval-Augmented Generation
* Tool calling
* Structured data extraction
* Business workflow automation
* Conversational AI
* Automated testing
* AI system evaluation

The project also demonstrates how AI agents can be combined with deterministic business tools to create more reliable business workflows.

---

# Author

**Ambrose Lengerpei**

Kenya

GitHub:

https://github.com/Lengerpei/KENYABIZ-AI

---

# License

This project is developed as an AI capstone project for educational and demonstration purposes.
