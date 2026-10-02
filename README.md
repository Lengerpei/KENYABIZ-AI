# KenyaBiz AI

## Multi-Agent AI Business Assistant for Kenyan SMEs

KenyaBiz AI is a multi-agent business assistant designed to help Kenyan small and medium-sized enterprises (SMEs) manage common customer, sales, ordering, invoicing, and payment-related interactions through a conversational AI system.

The project combines:

* LangGraph-based multi-agent orchestration
* Lightweight Retrieval-Augmented Generation (RAG)
* Product catalogue and stock lookup
* Product pricing and quotations
* Order processing and confirmation
* PDF invoice generation
* Simulated M-PESA payment processing
* Stateful multi-turn conversations
* Command-line and Streamlit interfaces
* Automated functional and workflow testing

KenyaBiz AI is developed as a capstone prototype demonstrating how AI agents can coordinate business processes rather than functioning only as a standalone chatbot.

---

## 1. Project Overview

Many SMEs handle customer enquiries, product requests, quotations, orders, invoices, and payment-related questions manually. This can result in repetitive work, inconsistent responses, and delays.

KenyaBiz AI provides a conversational interface through which a customer can:

1. Ask questions about the company.
2. Ask about products, prices, and stock.
3. Request a quotation.
4. Place an order.
5. Confirm an order and provide a customer name.
6. Request an invoice.
7. Request simulated M-PESA payment processing.
8. Check payment status.

The system uses specialized agents coordinated through a supervisor and shared conversation state.

---

## 2. Problem Statement

Small businesses often have limited resources for automating customer support and sales operations.

Common challenges include:

* Repeatedly answering the same customer questions
* Maintaining product and pricing information
* Preparing quotations manually
* Capturing customer orders
* Generating invoices
* Handling payment-related interactions
* Maintaining context across multiple customer messages

KenyaBiz AI addresses these challenges through a prototype multi-agent architecture that combines deterministic business logic, retrieval, LLM-based responses, and workflow state management.

---

## 3. Project Objectives

The main objectives are to:

* Build a practical AI assistant for Kenyan SMEs
* Demonstrate multi-agent orchestration using LangGraph
* Implement a lightweight RAG pipeline for company knowledge
* Provide product catalogue and pricing functionality
* Validate product availability and stock quantities
* Generate quotations from customer requests
* Support multi-turn order conversations
* Generate PDF invoices automatically
* Simulate M-PESA payment workflows
* Test individual agents and complete business workflows
* Provide both CLI and Streamlit interfaces

---

## 4. Proposed Solution

KenyaBiz AI uses a supervisor-led multi-agent architecture.

```text
                         CUSTOMER
                            |
                            v
                    +----------------+
                    |   SUPERVISOR   |
                    +----------------+
                            |
          +-----------------+-----------------+
          |        |        |        |        |
          v        v        v        v        v
       SUPPORT   SALES    ORDER   INVOICE   PAYMENT
          |        |        |        |        |
          v        v        v        v        v
         RAG    Products  Orders   ReportLab  Payment
       Knowledge & Quotes  & State     PDF     Workflow
         Base
```

The Supervisor determines which specialist agent should handle the customer's request.

The agents share conversation state so that workflows can continue across multiple messages.

Important transactional operations use deterministic application logic, while the LLM-based supervisor provides fallback routing for requests that do not match explicit routing rules.

---

# 5. Key Features

## 5.1 Company and FAQ Questions

Customers can ask questions about:

* The company
* Products and services
* Delivery
* Payments
* Invoices
* Refunds
* Customer support

The Support Agent retrieves relevant information from the business knowledge base before generating a response.

---

## 5.2 Product Catalogue

The product catalogue contains information such as:

* Product ID
* Product name
* Category
* Price
* Available stock

Example products include:

| Product        | Example Price |
| -------------- | ------------: |
| Office Chair   |     KES 8,500 |
| Office Desk    |    KES 15,000 |
| Laptop Stand   |     KES 4,500 |
| Office Cabinet |    KES 18,000 |
| Visitor Chair  |     KES 5,500 |
| Executive Desk |    KES 35,000 |
| Monitor Stand  |     KES 3,500 |
| Keyboard       |     KES 2,800 |
| Wireless Mouse |     KES 1,800 |
| Meeting Table  |    KES 45,000 |

Product information is stored in `data/products.csv`.

---

## 5.3 Product Search

Customers can search using natural-language requests such as:

```text
What products do you sell?

Do you have office chairs?

How much is a keyboard?

Do you have wireless mice?
```

The Sales Agent identifies relevant products from the catalogue.

---

## 5.4 Pricing

The assistant can provide individual product prices and calculate order totals.

Example:

```text
2 keyboards

Product subtotal: KES 5,600
Delivery: KES 2,500
Total: KES 8,100
```

---

## 5.5 Stock Validation

Before an order is processed, the system checks whether the requested quantity is available.

The current prototype validates stock availability but does not permanently deduct stock after an order is completed.

---

## 5.6 Quotations

Customers can request quotations containing multiple products.

Example:

```text
5 Office Chairs
2 Office Desks

Subtotal: KES 72,500
Delivery: KES 2,500
Total: KES 75,000
```

Quotation calculations use deterministic business logic rather than relying on the LLM to perform the calculations.

---

## 5.7 Order Processing

The order workflow supports:

* Product identification
* Quantity validation
* Stock validation
* Order confirmation
* Customer name capture
* Order reference generation
* Order status management

Example order reference:

```text
KBA-YYYYMMDD-XXXX
```

Order references are generated dynamically by the application.

---

## 5.8 Invoice Generation

The Invoice Agent generates PDF invoices using ReportLab.

Invoices are generated from confirmed order information and include relevant order and customer information.

Generated invoice files are stored locally in the `invoices/` directory.

The `invoices/` directory is excluded from version control because invoice files are generated application outputs.

---

## 5.9 Simulated M-PESA Payments

The Payment Agent demonstrates a simulated payment workflow based on the M-PESA payment concept.

The prototype can:

* Create a payment request for an order
* Generate a simulated payment reference
* Record payment status
* Complete a simulated payment
* Check payment status

This is a simulation only. It does not connect to the live Safaricom M-PESA API and does not process real financial transactions.

---

# 6. Multi-Agent Architecture

KenyaBiz AI separates responsibilities among specialized agents.

## Supervisor Agent

The Supervisor determines which specialist agent should handle a request.

Routing considers:

* The current customer message
* Existing conversation state
* Active order workflows
* Invoice references
* Payment references
* Product and quotation requests

Important transactional requests are handled using deterministic routing rules, while the LLM supervisor provides fallback routing.

The Supervisor routes requests to one of five specialist agents:

* Support
* Sales
* Order
* Invoice
* Payment

---

## Support Agent

The Support Agent handles:

* Company questions
* FAQs
* Delivery questions
* Payment policy questions
* Invoice capability questions
* General business information

It uses the business knowledge base and lightweight RAG retrieval.

---

## Sales Agent

The Sales Agent handles:

* Product search
* Product prices
* Stock questions
* Quotations
* Product-related requests
* Product recommendations

---

## Order Agent

The Order Agent handles:

* New orders
* Order confirmation
* Customer name capture
* Stock validation
* Order references
* Order status

---

## Invoice Agent

The Invoice Agent handles:

* Invoice requests
* Order reference validation
* PDF invoice generation

---

## Payment Agent

The Payment Agent handles:

* Payment requests
* Simulated M-PESA processing
* Payment references
* Payment completion
* Payment status

---

# 7. Retrieval-Augmented Generation

KenyaBiz AI includes a lightweight RAG pipeline for business knowledge.

The current implementation uses keyword-based document retrieval rather than vector embeddings.

## Knowledge Base

The business knowledge base contains:

```text
company_profile.md
faq.md
delivery_policy.md
payment_policy.md
```

The documents are stored in the `data/` directory.

The retriever:

1. Normalizes the customer query.
2. Removes common stop words.
3. Extracts meaningful keywords.
4. Scores documents based on keyword overlap.
5. Gives additional weight to important business terms.
6. Selects the most relevant documents.
7. Passes the retrieved context to the Support Agent.

This approach was intentionally kept lightweight and easy to understand for the capstone prototype.

## Current RAG Implementation

The current application does not use vector embeddings or vector databases.

The active implementation is based on keyword matching and document relevance scoring.

## Future RAG Enhancement

Future versions can introduce:

* Sentence embeddings
* FAISS vector search
* Semantic retrieval
* Chunk-level retrieval
* Hybrid retrieval
* RAG evaluation metrics

FAISS and Sentence Transformers are therefore considered future enhancements and are not required dependencies for the current implementation.

---

# 8. Conversation State

A shared `KenyaBizState` object maintains information required across the conversation.

Examples include:

* Customer message
* Conversation history
* Pending request
* Pending action
* Pending order
* Order confirmation status
* Destination agent
* Routing reason
* Order reference
* Order status
* Invoice path
* Payment reference
* Payment status
* Customer information

This allows the system to support multi-turn workflows.

Example:

```text
Customer: I want to order 2 office chairs.

Assistant: Your requested products are available.
Please confirm that you would like to proceed with the order.

Customer: Yes.

Assistant: Please provide your name.

Customer: Ambrose Lengerpei.

Assistant: Order created successfully.
```

The conversation state allows the system to understand that the second and third messages belong to the existing order workflow.

---

# 9. End-to-End Workflow

A typical business workflow is:

```text
Customer request
       |
       v
Supervisor routing
       |
       v
Sales / Order Agent
       |
       v
Product identification
       |
       v
Stock validation
       |
       v
Quotation / total
       |
       v
Customer confirmation
       |
       v
Customer name
       |
       v
Order creation
       |
       v
Invoice generation
       |
       v
Simulated payment
       |
       v
Payment completion
       |
       v
Payment status
```

The workflow can be interrupted by unrelated questions and then continue when the customer returns to the pending order context.

---

# 10. Verified End-to-End Workflow

The complete business transaction workflow has been manually verified through the CLI.

A successful test followed this sequence:

```text
1. Customer requests 2 office chairs
2. System validates product availability
3. System requests order confirmation
4. Customer confirms
5. System requests customer name
6. Customer provides name
7. System creates an order reference
8. Customer requests an invoice
9. System generates a PDF invoice
10. Customer requests payment
11. System creates a simulated M-PESA payment request
12. Customer confirms payment
13. System marks payment as PAID
14. Customer checks payment status
```

Example generated order reference:

```text
KBA-20261002-XHZL
```

The exact order and payment references are generated dynamically and will differ between runs.

This demonstrates coordination between the Supervisor, Sales, Order, Invoice, and Payment components.

---

# 11. Database Design

The project uses SQLite for local data persistence.

The database layer supports application data such as:

* Products
* Orders
* Order items
* Payments

Database-related source files are located under:

```text
src/database/
```

The local SQLite database is generated for application use and is excluded from version control.

The database schema is defined in:

```text
src/database/schema.sql
```

---

# 12. Data Architecture

The project combines several data sources:

```text
                         KENYABIZ AI
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
    Product Data       Business Knowledge   Application Data
          |                   |                   |
          v                   v                   v
    products.csv       Markdown documents       SQLite
          |                   |                   |
          +-------------------+-------------------+
                              |
                              v
                       AI Agent Workflow
```

Product information is used by the Sales and Order workflows, while business documents support company-related questions.

---

# 13. Technology Stack

| Technology            | Purpose                                |
| --------------------- | -------------------------------------- |
| Python 3.12           | Application development                |
| LangGraph             | Multi-agent workflow orchestration     |
| LangChain             | LLM and agent integration              |
| LangChain Core        | Core LLM abstractions                  |
| ChatGroq              | LLM integration                        |
| Groq                  | Language model inference               |
| Streamlit             | Web interface                          |
| SQLite                | Local database                         |
| ReportLab             | PDF invoice generation                 |
| pandas                | Data processing                        |
| python-dotenv         | Environment configuration              |
| pytest                | Automated testing                      |
| FAISS                 | Planned vector retrieval enhancement   |
| Sentence Transformers | Planned semantic retrieval enhancement |

---

# 14. Project Structure

```text
KENYABIZ-AI/
│
├── data/
│   ├── company_profile.md
│   ├── faq.md
│   ├── delivery_policy.md
│   ├── payment_policy.md
│   └── products.csv
│
├── src/
│   ├── agents/
│   │   ├── invoice_agent.py
│   │   ├── order_agent.py
│   │   ├── payment_agent.py
│   │   ├── sales_agent.py
│   │   ├── supervisor.py
│   │   └── support_agent.py
│   │
│   ├── database/
│   │   ├── database.py
│   │   └── schema.sql
│   │
│   ├── rag/
│   │   ├── documents.py
│   │   └── retriever.py
│   │
│   ├── tools/
│   │   ├── invoice_tool.py
│   │   ├── order_tool.py
│   │   ├── payment_tool.py
│   │   ├── product_tool.py
│   │   └── quotation_tool.py
│   │
│   ├── utils/
│   │   ├── config.py
│   │   └── helpers.py
│   │
│   ├── graph.py
│   ├── main.py
│   ├── state.py
│   └── streamlit_app.py
│
├── tests/
│   ├── conftest.py
│   ├── test_agents.py
│   ├── test_products.py
│   ├── test_quotation.py
│   └── test_workflow.py
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

Generated files such as local invoices, logs, the SQLite database, Python cache files, and environment variables are excluded through `.gitignore`.

---

# 15. Installation

## 15.1 Clone the Repository

```powershell
git clone https://github.com/Lengerpei/KENYABIZ-AI.git

cd KENYABIZ-AI
```

## 15.2 Create a Virtual Environment

Python 3.12 is recommended.

On Windows:

```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1
```

## 15.3 Install Dependencies

```powershell
pip install -r requirements.txt
```

The requirements file includes the dependencies required to run the application and automated tests.

---

# 16. Environment Configuration

Create a local `.env` file in the project root.

The repository provides `.env.example` as a configuration template.

Copy `.env.example` to `.env` and provide your own API key.

Example:

```env
GROQ_API_KEY=your_groq_api_key

KENYABIZ_DATABASE=

DEFAULT_DELIVERY_FEE=2500

CURRENCY=KES
```

## Environment Variables

| Variable               | Description                                        | Default             |
| ---------------------- | -------------------------------------------------- | ------------------- |
| `GROQ_API_KEY`         | API key used for Groq LLM access                   | None                |
| `KENYABIZ_DATABASE`    | Optional custom SQLite database path               | Application default |
| `DEFAULT_DELIVERY_FEE` | Default delivery fee used by quotations and orders | `2500`              |
| `CURRENCY`             | Currency used by the application                   | `KES`               |

The `.env` file is intentionally excluded from Git.

**Never commit real API keys, passwords, tokens, or other credentials to the repository.**

---

# 17. Running the CLI

From the project root:

```powershell
python -m src.main
```

The application starts the KenyaBiz AI conversational interface.

Example:

```text
======================================================================
KENYABIZ AI
MULTI-AGENT BUSINESS ASSISTANT
======================================================================

You: What payment methods do you accept?

KenyaBiz AI: ...
```

To end the session:

```text
exit
```

To reset the conversation:

```text
reset
```

---

# 18. Running the Streamlit Application

The Streamlit interface is located at:

```text
src/streamlit_app.py
```

Run:

```powershell
streamlit run src/streamlit_app.py
```

This launches the browser-based interface for interacting with KenyaBiz AI.

---

# 19. Example Conversations

## Company Question

```text
Customer: Tell me about the company.

KenyaBiz AI: [Company information retrieved from the knowledge base]
```

## Product Price

```text
Customer: How much is an office chair?

KenyaBiz AI: An Office Chair costs KES 8,500.
```

## Product Availability

```text
Customer: Do you have keyboards?

KenyaBiz AI: Yes. The Keyboard is available at KES 2,800.
```

## Quotation

```text
Customer: Give me a quotation for 5 office chairs and 2 office desks.

KenyaBiz AI:

Subtotal: KES 72,500
Delivery: KES 2,500
Total: KES 75,000
```

## Order

```text
Customer: I want to order 2 office chairs.

KenyaBiz AI: Your requested products are available.
Please confirm that you would like to proceed with the order.

Customer: Yes.

KenyaBiz AI: Please provide your name.

Customer: Ambrose Lengerpei.

KenyaBiz AI: Order created successfully.
```

## Invoice

```text
Customer: Generate an invoice for KBA-XXXXXXXX-XXXX.

KenyaBiz AI: [Invoice generated]
```

## Payment

```text
Customer: I want to pay for order KBA-XXXXXXXX-XXXX.

KenyaBiz AI: [Simulated payment request]
```

Actual order and payment references are generated dynamically.

---

# 20. Testing

The project contains automated tests covering agents, product tools, quotations, and complete workflows.

Run all tests with:

```powershell
pytest tests -q
```

## Current Test Result

The current automated test suite contains:

```text
200 passed
```

The tests cover:

* Agent behavior
* Product lookup
* Product validation
* Stock validation
* Quotation calculations
* Order processing
* Invoice workflows
* Payment workflows
* Conversation routing
* Multi-turn order conversations
* Error handling
* Invalid inputs
* Order cancellation and decline scenarios

The passing test result represents the current verified state of the repository at the time of documentation.

---

# 21. Workflow Testing

The workflow test suite contains 14 end-to-end scenarios covering important business conversations.

Examples include:

* Company support questions
* Product price requests
* New orders
* Complete order workflows
* Order interruptions
* Order continuation
* Invoice requests
* Payment requests
* Payment completion
* Payment status checks
* Unknown products
* Insufficient stock
* Declined orders
* Invalid invoice references

The workflow tests are designed to verify that agents work together rather than testing each component only in isolation.

---

# 22. Functional Testing vs AI Evaluation

The current project has an automated functional test suite.

Functional tests verify deterministic application behavior such as:

* Correct product identification
* Correct prices
* Stock validation
* Order creation
* Invoice generation
* Payment workflow
* Routing
* Error handling

These tests do not fully measure the quality of LLM-generated responses.

Formal AI evaluation is therefore treated as a future enhancement.

Potential evaluation areas include:

* Answer relevancy
* Faithfulness
* Context relevance
* Retrieval quality
* Response consistency
* Multi-turn conversation quality

Potential evaluation tools include:

* RAGAS
* DeepEval
* Custom business-specific evaluation datasets

---

# 23. Error Handling

The application includes safeguards for common errors.

Examples include:

* Unknown products
* Invalid quantities
* Insufficient stock
* Invalid order references
* Invalid invoice references
* Invalid payment references
* Declined orders
* Missing customer information
* LLM/API errors
* Rate-limit errors

Where appropriate, the application can provide fallback behavior for certain support requests when LLM availability is temporarily affected.

---

# 24. Security and Configuration

The current prototype follows basic security practices:

* API keys are stored in environment variables.
* `.env` is excluded from version control.
* Generated local files are excluded from version control.
* The application does not intentionally expose API keys in normal responses.

The prototype does not yet implement:

* User authentication
* Role-based access control
* Production secrets management
* Encrypted customer records
* Production payment security
* Production-grade API security

These would be required considerations for a production deployment.

---

# 25. Design Principles

The project follows several design principles.

## Separation of Responsibilities

Each agent has a focused business responsibility.

## Stateful Conversations

Conversation state is shared across agents to support multi-turn workflows.

## Deterministic Transaction Logic

Important business operations such as order validation, stock checks, invoice references, quotation calculations, and payment references use deterministic application logic.

## Retrieval-Grounded Support

Company-related responses are supported by information retrieved from the business knowledge base.

## Testability

Agents, tools, and workflows are separated so that individual components and complete workflows can be tested.

## Extensibility

The architecture allows additional agents, tools, retrieval methods, and business capabilities to be added later.

---

# 26. Current Limitations

KenyaBiz AI is a capstone prototype and has several limitations:

1. The RAG implementation currently uses keyword-based retrieval.
2. FAISS and Sentence Transformers semantic retrieval are not yet active.
3. M-PESA processing is simulated.
4. Stock is validated but not permanently deducted after an order.
5. SQLite is intended for local prototype use.
6. User authentication is not implemented.
7. The application does not provide production-grade payment integration.
8. Formal LLM evaluation is limited.
9. Responses depend partly on external LLM availability and API limits.
10. The system has not been deployed as a production commercial application.

These limitations are documented to distinguish the current prototype capabilities from future production requirements.

---

# 27. Future Improvements

Potential future improvements include:

## Semantic RAG

Replace or supplement keyword retrieval with:

* Sentence embeddings
* FAISS vector search
* Semantic similarity
* Improved document chunking
* Hybrid retrieval

## Real M-PESA Integration

Integrate with an appropriate M-PESA API for real payment processing in a secure production environment.

## Authentication

Add:

* Customer authentication
* Staff authentication
* Role-based access control

## Advanced Database Management

Introduce production-ready database infrastructure and stronger transaction management.

## Inventory Management

Automatically update stock after confirmed orders and support inventory reconciliation.

## AI Evaluation

Introduce systematic evaluation using:

* RAGAS
* DeepEval
* Custom business-specific evaluation datasets

## Deployment

Deploy the application using an appropriate cloud or enterprise environment with:

* Secure secrets management
* Monitoring
* Logging
* Error tracking
* Scalable infrastructure

---

# 28. Capstone Significance

KenyaBiz AI demonstrates how multiple AI agents can be combined with traditional software engineering and business logic to automate a realistic SME workflow.

The project goes beyond a simple chatbot by combining:

* Multi-agent orchestration
* RAG
* Structured product data
* Business rules
* Stateful conversations
* Database operations
* Document generation
* Simulated payment processing
* Automated testing

This provides a practical demonstration of agentic AI applied to a Kenyan SME business context.

---

# 29. Conclusion

KenyaBiz AI provides a working prototype of a multi-agent business assistant capable of supporting common SME customer and sales workflows.

The current implementation demonstrates the integration of AI agents with deterministic business tools and stateful workflow management.

The verified prototype supports:

```text
Customer Support
      ↓
Product Search
      ↓
Pricing & Quotations
      ↓
Order Processing
      ↓
Invoice Generation
      ↓
Simulated Payment
      ↓
Payment Status
```

With further development in semantic retrieval, authentication, inventory management, payment integration, AI evaluation, and production deployment, the architecture can be extended into a more complete business automation platform.

---

# 30. Author

**Ambrose Ltiripwa Lengerpei**

Data Science / AI Developer

Kenya

KenyaBiz AI was developed as a capstone project demonstrating practical applications of agentic AI, RAG, data processing, and workflow automation.

---

# 31. Repository

GitHub:

https://github.com/Lengerpei/KENYABIZ-AI

---

# 32. Project Status

**Capstone Prototype Complete**

Current implementation includes:

* Multi-agent architecture
* Stateful conversation workflow
* Business knowledge retrieval
* Product catalogue
* Product pricing
* Stock validation
* Quotations
* Order processing
* PDF invoice generation
* Simulated M-PESA payment workflow
* CLI interface
* Streamlit interface
* Automated tests
* 200 passing tests
* 14 end-to-end workflow scenarios

The project is suitable for capstone demonstration and further development toward a production system.

---

# 33. Quick Start

```powershell
git clone https://github.com/Lengerpei/KENYABIZ-AI.git

cd KENYABIZ-AI

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create `.env` using `.env.example` and add your Groq API key.

Run the CLI:

```powershell
python -m src.main
```

Run the Streamlit interface:

```powershell
streamlit run src/streamlit_app.py
```

Run the automated tests:

```powershell
pytest tests -q
```

Expected current test result:

```text
200 passed
```

---

# 34. License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for the complete license terms.

---
