# KenyaBiz AI

## Multi-Agent AI Business Assistant for Kenyan SMEs

KenyaBiz AI is a multi-agent business assistant designed to help Kenyan small and medium-sized enterprises (SMEs) manage common customer and sales interactions through a conversational AI system.

The project combines:

* LangGraph-based multi-agent orchestration
* Retrieval-Augmented Generation (RAG)
* Product catalogue and stock lookup
* Product pricing and quotations
* Order processing and confirmation
* PDF invoice generation
* Simulated M-PESA payment processing
* Stateful multi-turn conversations
* Command-line and Streamlit interfaces
* Automated functional and workflow testing

KenyaBiz AI is developed as a capstone prototype demonstrating how AI agents can coordinate business processes rather than responding only as a standalone chatbot.

---

## 1. Project Overview

Many SMEs handle customer enquiries, product requests, quotations, orders, invoices, and payment-related questions manually. This can lead to repetitive work, inconsistent responses, and delays.

KenyaBiz AI provides a single conversational interface through which a customer can:

1. Ask questions about the company.
2. Ask about products, prices, and stock.
3. Request a quotation.
4. Place an order.
5. Confirm an order and provide customer details.
6. Request an invoice.
7. Request simulated M-PESA payment processing.
8. Check payment status.

The system uses specialized agents coordinated through a supervisor and shared conversation state.

---

## 2. Problem Statement

Small businesses often have limited resources for automating customer support and sales operations.

Common challenges include:

* Repeatedly answering the same customer questions.
* Maintaining product and pricing information.
* Preparing quotations manually.
* Capturing customer orders.
* Generating invoices.
* Handling payment-related interactions.
* Maintaining context across multiple customer messages.

KenyaBiz AI addresses these challenges through a prototype multi-agent architecture that combines deterministic business logic, retrieval, LLM-based responses, and workflow state management.

---

## 3. Project Objectives

The main objectives are to:

* Build a practical AI assistant for Kenyan SMEs.
* Demonstrate multi-agent orchestration using LangGraph.
* Implement a lightweight RAG pipeline for company knowledge.
* Provide product catalogue and pricing functionality.
* Validate product availability and stock quantities.
* Generate quotations from customer requests.
* Support multi-turn order conversations.
* Generate PDF invoices automatically.
* Simulate M-PESA payment workflows.
* Test individual agents and complete business workflows.
* Provide both CLI and Streamlit interfaces.

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
          +------------------+------------------+
          |          |          |        |      |
          v          v          v        v      v
      SUPPORT      SALES      ORDER   INVOICE  PAYMENT
          |          |          |        |      |
          v          v          v        v      v
        RAG       Products    Orders   ReportLab Payment
       Knowledge  & Quotes    & State    PDF     Workflow
        Base
```

The supervisor determines which specialized agent should handle the customer's request.

The agents share conversation state so that a workflow can continue across multiple messages.

---

## 5. Key Features

### 5.1 Company and FAQ Questions

Customers can ask questions about:

* The company
* Products and services
* Delivery
* Payments
* Invoices
* Refunds
* Customer support

The support agent retrieves relevant information from the business knowledge base before generating a response.

### 5.2 Product Catalogue

The product catalogue contains product information such as:

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

### 5.3 Product Search

Customers can search using natural-language requests such as:

```text
What products do you sell?
Do you have office chairs?
How much is a keyboard?
Do you have wireless mice?
```

### 5.4 Pricing

The assistant can provide individual product prices and calculate order totals.

Example:

```text
2 keyboards
Product subtotal: KES 5,600
Delivery: KES 2,500
Total: KES 8,100
```

### 5.5 Stock Validation

Before an order is processed, the system checks whether the requested quantity is available.

The current prototype validates stock availability but does not permanently deduct stock after an order is completed.

### 5.6 Quotations

Customers can request quotations containing multiple products.

Example:

```text
5 Office Chairs
2 Office Desks

Subtotal: KES 72,500
Delivery: KES 2,500
Total: KES 75,000
```

### 5.7 Order Processing

The order workflow supports:

* Product identification
* Quantity validation
* Stock validation
* Order confirmation
* Customer name capture
* Customer details capture
* Order reference generation
* Order status management

Example order reference:

```text
KBA-20260930-32RI
```

### 5.8 Invoice Generation

The invoice agent generates PDF invoices using ReportLab.

Invoices are generated from confirmed order information and include relevant order and customer details.

### 5.9 Simulated M-PESA Payments

The payment agent demonstrates a payment workflow using simulated M-PESA transactions.

The prototype can:

* Request payment for an order.
* Generate a simulated payment reference.
* Record payment status.
* Check payment status.

This is a simulation and does not connect to the live Safaricom M-PESA API.

---

## 6. Multi-Agent Architecture

KenyaBiz AI separates responsibilities among specialized agents.

### Supervisor Agent

The supervisor determines which agent should handle a request.

Routing considers:

* The current customer message.
* Existing conversation state.
* Active order workflows.
* Invoice references.
* Payment references.
* Product and quotation requests.

Deterministic routing rules are used for important transactional workflows, while the LLM supervisor can provide fallback routing for requests that do not match explicit rules.

### Support Agent

Handles:

* Company questions
* FAQs
* Delivery questions
* Payment policy questions
* Invoice questions
* General business information

It uses the business knowledge base and RAG retrieval.

### Sales Agent

Handles:

* Product search
* Product prices
* Stock questions
* Quotations
* Product-related requests

### Order Agent

Handles:

* New orders
* Order confirmation
* Customer details
* Stock validation
* Order references
* Order status

### Invoice Agent

Handles:

* Invoice requests
* Order reference validation
* PDF invoice generation

### Payment Agent

Handles:

* Payment requests
* Simulated M-PESA processing
* Payment references
* Payment status

---

## 7. Retrieval-Augmented Generation

KenyaBiz AI includes a lightweight RAG pipeline for business knowledge.

The current implementation uses keyword-based document retrieval rather than vector embeddings.

### Knowledge Base

The knowledge base contains documents such as:

```text
company_profile.md
faq.md
delivery_policy.md
payment_policy.md
```

The retriever:

1. Normalizes the customer query.
2. Removes common stop words.
3. Extracts meaningful keywords.
4. Scores documents based on keyword overlap.
5. Gives additional weight to important business terms.
6. Selects the most relevant documents.
7. Passes the retrieved context to the support agent.

This approach was intentionally kept lightweight and easy to understand for the capstone prototype.

### Future RAG Enhancement

The project includes `faiss-cpu` and `sentence-transformers` in its dependency set, but the current active retrieval implementation does not use them.

Future versions can introduce:

* Sentence embeddings
* FAISS vector search
* Semantic retrieval
* Chunk-level retrieval
* RAG evaluation metrics

---

## 8. Conversation State

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

Assistant: I found 2 Office Chairs. The total is KES 19,500 including delivery. Would you like to proceed?

Customer: Yes.

Assistant: Please provide your name.

Customer: Ambrose Lengerpei.

Assistant: Your order has been created...
```

The conversation state allows the system to understand that the second and third messages belong to the existing order workflow.

---

## 9. End-to-End Workflow

A typical order workflow is:

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
Customer details
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
Payment status
```

The workflow can be interrupted by unrelated questions and then continue when the customer returns to the pending order context.

---

## 10. Database Design

The project uses SQLite for local data persistence.

The database layer supports application data such as:

* Products
* Orders
* Order items
* Payments

Database-related files are located under:

```text
src/database/
```

The local SQLite database is excluded from version control.

---

## 11. Data Architecture

The project combines several data sources:

```text
                         KENYABIZ AI
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
 Product Data          Business Knowledge      Application Data
       |                      |                      |
       v                      v                      v
 products.csv          Markdown documents        SQLite
       |                      |                      |
       +-----------+----------+----------------------+
                   |
                   v
             AI Agent Workflow
```

Product information is used by the sales and order workflows, while business documents support company-related questions.

---

## 12. Technology Stack

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

## 13. Project Structure

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
├── .gitignore
├── README.md
└── requirements.txt
```

Generated files such as local invoices, logs, the SQLite database, Python cache files, and environment variables are excluded through `.gitignore`.

---

## 14. Installation

### 14.1 Clone the Repository

```bash
git clone https://github.com/Lengerpei/KENYABIZ-AI.git
cd KENYABIZ-AI
```

### 14.2 Create a Virtual Environment

Python 3.12 is recommended.

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 14.3 Install Dependencies

```powershell
pip install -r requirements.txt
```

For running the automated tests:

```powershell
pip install pytest
```

---

## 15. Environment Configuration

Create a local `.env` file in the project root.

Example:

```env
GROQ_API_KEY=your_groq_api_key
```

The `.env` file is intentionally excluded from Git.

Do not commit API keys or other credentials to the repository.

---

## 16. Running the CLI

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

## 17. Running the Streamlit Application

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

## 18. Example Conversations

### Company Question

```text
Customer: Tell me about the company.

KenyaBiz AI: [Company information retrieved from the knowledge base]
```

### Product Price

```text
Customer: How much is an office chair?

KenyaBiz AI: An Office Chair costs KES 8,500.
```

### Product Availability

```text
Customer: Do you have keyboards?

KenyaBiz AI: Yes. The Keyboard is available at KES 2,800.
```

### Quotation

```text
Customer: Give me a quotation for 5 office chairs and 2 office desks.

KenyaBiz AI:
Subtotal: KES 72,500
Delivery: KES 2,500
Total: KES 75,000
```

### Order

```text
Customer: I want to order 2 office chairs.

KenyaBiz AI: [Order confirmation request]

Customer: Yes.

KenyaBiz AI: Please provide your name.

Customer: Ambrose Lengerpei.

KenyaBiz AI: [Order confirmation and reference]
```

### Payment

```text
Customer: I want to pay for order KBA-XXXXXXXX-XXXX.

KenyaBiz AI: [Simulated payment request]
```

These examples illustrate the intended interaction patterns; actual references are generated dynamically.

---

## 19. Testing

The project contains automated tests covering agents, product tools, quotations, and complete workflows.

Run all tests with:

```powershell
pytest tests -q
```

### Current Test Result

The current test suite contains:

```text
200 passed
```

The test suite covers:

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

---

## 20. Workflow Testing

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

The workflow tests are designed to verify that agents work together rather than testing each component in isolation.

---

## 21. Functional Testing vs AI Evaluation

The current project has a strong automated functional test suite.

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

Possible evaluation areas include:

* Answer relevancy
* Faithfulness
* Context relevance
* Retrieval quality
* Response consistency
* Multi-turn conversation quality

Potential evaluation tools include RAGAS and DeepEval.

---

## 22. Error Handling

The application includes safeguards for common errors.

Examples include:

* Unknown products
* Invalid quantities
* Insufficient stock
* Invalid order references
* Invalid invoice references
* Invalid payment references
* Declined orders
* Missing customer details
* LLM/API errors
* Rate-limit errors

Where appropriate, the support agent can fall back to retrieved business knowledge when an LLM request is temporarily unavailable because of a rate-limit condition.

---

## 23. Security and Configuration

The current prototype follows basic security practices:

* API keys are stored in environment variables.
* `.env` is excluded from version control.
* Generated local files are excluded from version control.
* The application does not expose API keys in normal responses.

The prototype does not yet implement:

* User authentication
* Role-based access control
* Production secrets management
* Encrypted customer records
* Production payment security
* Production-grade API security

These are important considerations for a production deployment.

---

## 24. Design Principles

The project follows several design principles.

### Separation of Responsibilities

Each agent has a focused business responsibility.

### Stateful Conversations

Conversation state is shared across agents to support multi-turn workflows.

### Deterministic Transaction Logic

Important business operations such as order validation, stock checks, invoice references, and payment references use deterministic application logic.

### Retrieval-Grounded Support

Company-related responses are grounded in the business knowledge base.

### Testability

Agents and workflows are separated so that individual components and complete workflows can be tested.

### Extensibility

The architecture allows additional agents, tools, retrieval methods, and business capabilities to be added later.

---

## 25. Current Limitations

KenyaBiz AI is a capstone prototype and has several limitations:

1. The RAG implementation currently uses keyword-based retrieval.
2. FAISS and sentence-transformer semantic retrieval are not yet active.
3. M-PESA processing is simulated.
4. Stock is validated but not permanently deducted after an order.
5. SQLite is intended for local prototype use.
6. User authentication is not implemented.
7. The application does not provide production-grade payment integration.
8. Formal LLM evaluation is limited.
9. Responses depend partly on external LLM availability and API limits.
10. The system has not been deployed as a production commercial application.

---

## 26. Future Improvements

Potential future improvements include:

### Semantic RAG

Replace or supplement keyword retrieval with:

* Sentence embeddings
* FAISS vector search
* Semantic similarity
* Better document chunking

### Real M-PESA Integration

Integrate with an appropriate M-PESA API for real payment processing in a secure production environment.

### Authentication

Add:

* Customer authentication
* Staff authentication
* Role-based access control

### Advanced Database Management

Introduce production-ready database infrastructure and stronger transaction management.

### Inventory Management

Automatically update stock after confirmed orders and support inventory reconciliation.

### AI Evaluation

Introduce systematic evaluation using:

* RAGAS
* DeepEval
* Custom business-specific evaluation datasets

### Deployment

Deploy the application using an appropriate cloud or enterprise environment with:

* Secure secrets management
* Monitoring
* Logging
* Error tracking
* Scalable infrastructure

---

## 27. Capstone Significance

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

This makes the project a practical demonstration of agentic AI applied to a Kenyan SME business context.

---

## 28. Conclusion

KenyaBiz AI provides a working prototype of a multi-agent business assistant capable of supporting common SME customer and sales workflows.

The current implementation demonstrates the integration of AI agents with deterministic business tools and stateful workflow management.

With further development in semantic retrieval, authentication, inventory management, payment integration, AI evaluation, and production deployment, the architecture can be extended into a more complete business automation platform.

---

## 29. Author

**Ambrose Ltiripwa Lengerpei**

Data Science / AI Developer
Kenya

KenyaBiz AI was developed as a capstone project demonstrating practical applications of agentic AI, RAG, data processing, and workflow automation.

---

## 30. Repository

GitHub:

https://github.com/Lengerpei/KENYABIZ-AI

---

## 31. Project Status

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

## Quick Start

```powershell
git clone https://github.com/Lengerpei/KENYABIZ-AI.git
cd KENYABIZ-AI

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install pytest

python -m src.main
```

For the Streamlit interface:

```powershell
streamlit run src/streamlit_app.py
```

For testing:

```powershell
pytest tests -q
```

---

## License

This project is developed as an educational and capstone prototype.
