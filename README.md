# KenyaBiz AI

## Multi-Agent AI Business Assistant for Kenyan SMEs

KenyaBiz AI is a multi-agent business assistant designed to help Kenyan small and medium-sized enterprises (SMEs) manage common customer and business interactions through a conversational AI system.

The system combines **LangGraph orchestration, retrieval-augmented generation (RAG), product and quotation management, order processing, PDF invoice generation, and simulated M-PESA payments** into one conversational workflow.

The application supports both a **command-line interface (CLI)** and a **Streamlit web interface**.

---

# 1. Project Overview

Small and medium-sized businesses often handle customer enquiries, product requests, quotations, orders, invoices, and payments through separate manual processes.

KenyaBiz AI provides a single conversational interface through which a customer can:

- Ask questions about the business
- Ask about products
- Check product prices
- Check product availability
- Request quotations
- Place orders
- Confirm orders
- Provide customer details
- Generate invoices
- Request payment instructions
- Simulate M-PESA payments
- Check payment status
- Continue a conversation across multiple turns

The system uses specialized AI agents for different business functions and a supervisor routing layer to determine which agent should handle each interaction.

---

# 2. Problem Statement

Many Kenyan SMEs still rely heavily on manual communication channels to manage customer enquiries and sales processes.

A typical customer interaction may involve:

1. Asking about the business
2. Asking about available products
3. Requesting prices
4. Asking for a quotation
5. Placing an order
6. Providing customer details
7. Receiving an invoice
8. Making payment
9. Checking payment status

Handling these steps manually can be time-consuming and may result in inconsistent responses, delays, or lost information between different stages of the customer journey.

KenyaBiz AI addresses this problem by integrating these activities into a single conversational multi-agent system.

---

# 3. Project Objectives

The main objectives of KenyaBiz AI are to:

- Develop a multi-agent AI business assistant for Kenyan SMEs.
- Automate common business and customer-support interactions.
- Provide product information and pricing through conversation.
- Validate product availability before accepting orders.
- Generate quotations automatically.
- Support multi-turn order conversations.
- Generate PDF invoices automatically.
- Provide a simulated M-PESA payment workflow.
- Maintain conversation and workflow state across multiple turns.
- Demonstrate practical use of LangGraph for agent orchestration.
- Demonstrate RAG for business knowledge retrieval.
- Provide both CLI and Streamlit interfaces.
- Implement automated tests covering individual components and complete workflows.

---

# 4. Proposed Solution

KenyaBiz AI uses a **supervisor-based multi-agent architecture**.

A customer's message first enters the LangGraph workflow through the Supervisor routing node.

The Supervisor determines the appropriate specialist based on the customer's request.

```text
                         ┌─────────────────┐
                         │     START       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   SUPERVISOR    │
                         │     ROUTING     │
                         └────────┬────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
       ┌───────────┐        ┌───────────┐       ┌───────────┐
       │  SUPPORT  │        │   SALES   │       │   ORDER   │
       └─────┬─────┘        └─────┬─────┘       └─────┬─────┘
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
             ┌─────────────┐             ┌─────────────┐
             │   INVOICE   │             │   PAYMENT   │
             └──────┬──────┘             └──────┬──────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                              ┌───────┐
                              │  END  │
                              └───────┘

The LangGraph workflow consists of:

One Supervisor routing node
Five specialist business-processing nodes:
Support
Sales
Order
Invoice
Payment

The Supervisor uses deterministic routing rules for known business workflows and falls back to the LLM-based supervisor when a request does not match the explicit routing conditions.

5. Key Features
5.1 Business Information and FAQ

Customers can ask questions about the business using the knowledge stored in the business documentation.

Examples:

What does KenyaBiz AI do?

Where is the company located?

How can I contact the company?

What payment methods do you accept?

What is your delivery policy?

What is your refund policy?

The Support Agent retrieves relevant business information from the knowledge base before generating a response.

5.2 Product Catalogue

The system maintains a product catalogue containing product information such as:

Product ID
Product name
Description
Price
Stock quantity

Example products include:

Product	Price
Office Chair	KES 8,500
Office Desk	KES 15,000
Laptop Stand	KES 4,500
Office Cabinet	KES 18,000
Visitor Chair	KES 5,500
Executive Desk	KES 35,000
Monitor Stand	KES 3,500
Keyboard	KES 2,800
Wireless Mouse	KES 1,800
Meeting Table	KES 45,000
5.3 Product Search

Customers can ask for products using natural language.

Examples:

What office chairs do you have?

Do you sell keyboards?

Do you have office desks?

What products are available?

The Sales Agent interprets the request and retrieves relevant product information.

5.4 Product Pricing

Customers can request prices directly.

Examples:

How much is an office desk?

What is the price of a keyboard?

How much does an office chair cost?

The system retrieves the current product price from the product catalogue.

5.5 Stock Validation

Before an order is accepted, the Order Agent validates:

Whether the requested product exists.
Whether the requested quantity is valid.
Whether sufficient stock is available.

For example:

I want to order 2 office chairs.

The system checks the product and available quantity before continuing with the order workflow.

The current implementation validates stock availability but does not automatically deduct stock after an order.

5.6 Quotations

Customers can request quotations for multiple products.

For example:

I need 5 office chairs and 2 office desks.

The system calculates:

Office Chairs:
5 × KES 8,500 = KES 42,500

Office Desks:
2 × KES 15,000 = KES 30,000

Subtotal = KES 72,500
Delivery = KES 2,500

Total = KES 75,000

The quotation can then lead into the order confirmation workflow.

6. Multi-Agent Architecture

KenyaBiz AI separates business responsibilities across specialized agents.

This improves maintainability and allows each agent to focus on a specific business function.

The main components are:

Customer
   │
   ▼
Supervisor
   │
   ├── Support Agent
   │
   ├── Sales Agent
   │
   ├── Order Agent
   │
   ├── Invoice Agent
   │
   └── Payment Agent
7. Agent Responsibilities
7.1 Supervisor Agent

The Supervisor is responsible for routing incoming requests.

It identifies whether the customer is asking about:

Business information
Products
Prices
Quotations
Orders
Invoices
Payments
Existing workflow continuation

The implementation uses deterministic routing rules for important workflows before falling back to the LLM supervisor.

This helps maintain reliable behavior for transactional workflows such as ordering and payment.

7.2 Support Agent

The Support Agent handles general business information.

It uses the business knowledge base to answer questions about:

Company information
Services
Payment methods
Delivery
Refunds
General support

The Support Agent uses the RAG retrieval pipeline to obtain relevant business context.

7.3 Sales Agent

The Sales Agent handles product-related enquiries.

Responsibilities include:

Product search
Product information
Product pricing
Stock-related enquiries
Quotations
Multiple-product requests

Example:

How much are 5 office chairs?

The Sales Agent calculates the requested product cost and can prepare a quotation.

7.4 Order Agent

The Order Agent manages the order lifecycle.

The current workflow is:

Customer requests product
        ↓
Product validation
        ↓
Stock validation
        ↓
Quotation
        ↓
Customer confirmation
        ↓
Customer details
        ↓
Order creation
        ↓
Order reference

Example order reference:

KBA-20260930-32RI

The Order Agent validates products and stock before allowing the order to proceed.

7.5 Invoice Agent

The Invoice Agent handles invoice generation.

It can:

Identify an order reference
Validate the order
Retrieve order information
Generate a PDF invoice
Return the generated invoice path

Invoices are generated using ReportLab.

Example:

KBA-20260930-32RI

can be used to identify an order for invoice generation.

7.6 Payment Agent

The Payment Agent manages the simulated payment workflow.

It supports:

Payment instructions
Simulated M-PESA payment
Payment references
Payment status checks

Example payment reference:

MPSXXXXXXXX

The M-PESA integration is currently simulated and does not connect to the live Safaricom M-PESA API.

8. Retrieval-Augmented Generation (RAG)

KenyaBiz AI includes a lightweight Retrieval-Augmented Generation pipeline for business knowledge questions.

The current retrieval implementation is keyword-based rather than vector or embedding-based.

The retrieval process works as follows:

Customer Question
       ↓
Text Normalization
       ↓
Stop Word Removal
       ↓
Keyword Extraction
       ↓
Important Business Terms Weighted
       ↓
Document Scoring
       ↓
Top-k Documents
       ↓
Relevant Context
       ↓
Support Agent
       ↓
Final Response

The retriever:

Normalizes the customer's query.
Removes stop words.
Extracts meaningful keywords.
Gives additional weight to important business terms such as:
payment
M-PESA
invoice
delivery
order
refund
price
business
service
product
customer
Scores business documents according to keyword overlap.
Selects the highest-scoring documents.
Passes the retrieved content to the Support Agent.
Current RAG Implementation

The current implementation uses lightweight keyword retrieval.

Although faiss-cpu and sentence-transformers are included in the project dependencies, they are not currently used by the active retrieval implementation.

They can be used in future versions to introduce semantic or embedding-based retrieval.

9. Conversation State

KenyaBiz AI maintains shared conversation and workflow state.

The state is defined in:

src/state.py

The shared state supports fields including:

Customer message
Conversation history
Pending request
Pending action
Pending order
Order confirmation status
Forced destination
Routing reason
Response
Status
Order reference
Order status
Invoice path
Payment reference
Payment status
Customer information

This state allows the system to maintain context across multiple interactions.

For example:

Customer:
I want to order 2 keyboards.

Assistant:
The total is KES 8,100 including delivery. Would you like to confirm?

Customer:
Yes.

Assistant:
Please provide your name.

Customer:
Ambrose Lengerpei.

Assistant:
Your order has been created...

The system therefore supports multi-turn interactions rather than treating every message as an independent request.

10. End-to-End Business Workflow

A typical customer journey can follow this sequence:

1. Product enquiry
        ↓
2. Price enquiry
        ↓
3. Quotation
        ↓
4. Order request
        ↓
5. Product validation
        ↓
6. Stock validation
        ↓
7. Customer confirmation
        ↓
8. Customer details
        ↓
9. Order creation
        ↓
10. Invoice generation
        ↓
11. Payment request
        ↓
12. Simulated M-PESA payment
        ↓
13. Payment status

Each stage is handled by the appropriate component or agent.

11. Database Design

KenyaBiz AI uses SQLite for local data persistence.

The database contains business information required for order, invoice, and payment processing.

The database implementation is located in:

src/database/

Important files include:

database.py
schema.sql

The SQLite runtime database is generated locally and is excluded from Git using .gitignore.

12. Data Architecture

The project uses several types of data:

Business Knowledge

Stored in business documentation such as:

company_profile.md
faq.md
delivery_policy.md
payment_policy.md

These documents provide the knowledge used by the Support Agent.

Product Data

Product information is used for:

Product search
Price lookup
Stock validation
Quotations
Orders
Transaction Data

SQLite is used to persist transactional information such as:

Customers
Orders
Order items
Payments
Generated Documents

PDF invoices are generated by the Invoice Agent.

Generated invoice files are stored locally and excluded from Git.

13. Technology Stack
Technology	Purpose
Python 3.12	Main programming language
LangGraph	Agent workflow orchestration
LangChain	LLM and agent integration
LangChain Groq	Groq LLM integration
GPT OSS 120B via Groq	LLM used for AI-based reasoning/routing
Streamlit	Web interface
SQLite	Local database
ReportLab	PDF invoice generation
Pandas	Data processing
python-dotenv	Environment configuration
Pytest	Automated testing
FAISS	Installed dependency for potential future retrieval
Sentence Transformers	Installed dependency for potential future semantic retrieval
14. Project Structure
KENYABIZ-AI/
│
├── data/
│   └── documents/
│       ├── company_profile.md
│       ├── faq.md
│       ├── delivery_policy.md
│       └── payment_policy.md
│
├── src/
│   ├── __init__.py
│   ├── graph.py
│   ├── main.py
│   ├── state.py
│   ├── streamlit_app.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py
│   │   ├── support_agent.py
│   │   ├── sales_agent.py
│   │   ├── order_agent.py
│   │   ├── invoice_agent.py
│   │   └── payment_agent.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── schema.sql
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── documents.py
│   │   └── retriever.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── product_tool.py
│   │   ├── quotation_tool.py
│   │   ├── order_tool.py
│   │   ├── invoice_tool.py
│   │   └── payment_tool.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── helpers.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agents.py
│   ├── test_products.py
│   ├── test_quotation.py
│   └── test_workflow.py
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── app.py

Generated files such as Python cache files, logs, invoices, environment files, and the local SQLite database are excluded from version control.

15. Installation
15.1 Clone the Repository
git clone https://github.com/Lengerpei/KENYABIZ-AI.git

Move into the project directory:

cd KENYABIZ-AI
15.2 Create a Virtual Environment

The project was developed using Python 3.12.

Create the environment:

python -m venv .venv

Activate it:

.venv\Scripts\Activate.ps1
15.3 Install Dependencies
pip install -r requirements.txt

If Pytest is not included in the environment, install it separately:

pip install pytest
16. Environment Configuration

Create a .env file in the project root.

Example:

GROQ_API_KEY=your_groq_api_key

The API key should never be committed to Git.

The .env file is excluded through .gitignore.

Do not place API keys directly inside Python source files.

17. Running the Command-Line Interface

The CLI application is implemented through:

src/main.py

Run the application from the project root using:

python -m src.main

You should see:

======================================================================
KENYABIZ AI
MULTI-AGENT BUSINESS ASSISTANT
======================================================================

You can then enter natural-language requests.

Example:

You: How much is an office desk?

The system routes the request to the appropriate agent.

18. Running the Streamlit Interface

KenyaBiz AI also provides a Streamlit web interface.

Run:

streamlit run src/streamlit_app.py

The Streamlit application provides:

Chat interface
Example prompts
Product enquiries
Order interactions
Invoice download
Payment interactions
Conversation state

The Streamlit application uses the KenyaBizConversation class from src/main.py as the conversation engine.

19. Example Conversations
19.1 Product Price
Customer:
How much is a keyboard?

KenyaBiz AI:
A keyboard costs KES 2,800.
19.2 Product Availability
Customer:
Do you have office chairs?

KenyaBiz AI:
Yes. Office Chairs are available at KES 8,500 each.
19.3 Quotation
Customer:
I need 5 office chairs and 2 office desks.

KenyaBiz AI:
Office Chairs:
5 × KES 8,500 = KES 42,500

Office Desks:
2 × KES 15,000 = KES 30,000

Subtotal: KES 72,500
Delivery: KES 2,500
Total: KES 75,000

Would you like to confirm the order?
19.4 Multi-Turn Order
Customer:
I want to order 2 keyboards.

Assistant:
The total including delivery is KES 8,100.
Would you like to confirm the order?

Customer:
Yes.

Assistant:
Please provide your name.

Customer:
Ambrose Lengerpei.

Assistant:
Your order has been created successfully.
19.5 Payment
Customer:
I want to pay for my order.

Assistant:
The system provides the available simulated payment instructions.

Customer:
I have made the payment.

Assistant:
The payment is recorded with a simulated M-PESA reference.
20. Testing

The project includes automated tests covering:

Product functionality
Product validation
Stock validation
Quotations
Individual agents
Order processing
Invoice processing
Payment processing
Multi-turn workflows
Error handling
Workflow interruptions and continuation

Run the complete test suite:

pytest tests -q

The current test suite contains:

200 passed

This confirms that the current automated test suite passes successfully.

21. Workflow Testing

The project includes dedicated end-to-end workflow tests in:

tests/test_workflow.py

The workflow tests cover 14 scenarios, including:

General support request
Product price request
New order request
Complete order workflow
Order workflow interruption
Order continuation
Invoice request
Payment request
Payment completion
Payment status
Unknown product
Insufficient stock
Order decline
Invalid invoice reference

Run workflow tests using:

pytest tests/test_workflow.py -v
22. Functional Testing vs AI Evaluation

The current project has extensive automated functional and workflow testing.

These tests verify that:

Functions return expected results.
Agents handle defined business scenarios.
Orders are validated correctly.
Stock constraints are respected.
Workflow transitions work correctly.
Errors are handled appropriately.
Multi-turn conversations continue correctly.

These tests are different from formal AI evaluation.

Functional testing checks whether the application behaves according to defined requirements.

AI evaluation would measure qualities such as:

Answer relevance
Faithfulness
Retrieval quality
Response quality
Hallucination rate
LLM reasoning performance

Formal RAG/LLM evaluation is therefore considered a future enhancement for KenyaBiz AI.

23. Error Handling

The application includes validation and error handling for several situations.

Examples include:

Unknown Product
The requested product could not be found.
Insufficient Stock
The requested quantity is not currently available.
Invalid Order Reference

The system validates order references before attempting invoice or payment operations.

Invalid Payment Reference

Payment references are validated before processing payment-related requests.

Order Decline

If the customer declines an order confirmation, the order workflow is cancelled without creating the order.

Unrelated Questions During an Order

The workflow preserves pending order information while allowing unrelated support or payment questions to be handled by the appropriate specialist.

24. Security and Configuration

The project follows basic security practices appropriate for a prototype.

API Keys

API keys are stored in environment variables.

.env

is excluded from Git.

Local Database

The runtime SQLite database is excluded from Git:

data/kenyabiz.db
Generated Files

Generated invoices and logs are excluded from version control.

Production Security

The current project is a capstone prototype and does not yet implement:

User authentication
Role-based access control
Production payment security
Encrypted production database storage
API rate limiting
Production monitoring
Enterprise identity management

These would be required before deploying the system in a production environment.

25. Design Principles

KenyaBiz AI follows several design principles.

Separation of Responsibilities

Each agent has a defined business responsibility.

Support → Business information
Sales → Products and quotations
Order → Orders
Invoice → Invoices
Payment → Payments
Supervisor → Routing
State-Aware Conversations

The system maintains workflow state so that conversations can continue across multiple messages.

Deterministic Transaction Routing

Important transaction workflows use deterministic routing rules before LLM fallback.

This helps reduce incorrect routing during activities such as:

Order confirmation
Invoice requests
Payment requests
Order continuation
Modular Architecture

Business logic is separated into:

Agents
Tools
Database
RAG
Graph
State
User interfaces

This makes the system easier to maintain and extend.

26. Current Limitations

KenyaBiz AI is a capstone prototype and has several limitations.

1. M-PESA Is Simulated

The payment system does not currently connect to the live M-PESA API.

2. Stock Is Not Automatically Deducted

The system validates available stock but does not currently reduce inventory after an order is created.

3. Local SQLite Database

SQLite is suitable for the prototype but may need to be replaced by a production database for larger workloads.

4. Keyword-Based RAG

The current RAG implementation uses lightweight keyword matching rather than semantic vector retrieval.

5. No Authentication

The application does not currently implement customer authentication or account management.

6. No Production Payment Integration

Payment processing is simulated and should not be treated as a live financial transaction system.

7. Limited AI Evaluation

The project currently focuses on functional and workflow testing rather than formal LLM evaluation.

8. Prototype Deployment

The current architecture is designed primarily for demonstration, development, and capstone evaluation rather than production deployment.

27. Future Improvements

Future versions of KenyaBiz AI could include:

27.1 Semantic RAG

Replace or complement keyword retrieval with:

Sentence embeddings
Vector search
FAISS
Hybrid retrieval
Semantic reranking

This would improve retrieval for questions that use different wording from the knowledge-base documents.

27.2 Live M-PESA Integration

Integrate the official M-PESA API to support:

Payment requests
Payment confirmation
Transaction callbacks
Transaction verification
Payment reconciliation
27.3 Inventory Management

Implement automatic stock deduction after successful order creation.

Additional inventory features could include:

Stock replenishment
Low-stock alerts
Inventory reports
Product availability forecasting
27.4 Production Database

Move from SQLite to a production database such as:

PostgreSQL
MySQL

This would support greater concurrency and scalability.

27.5 Authentication

Introduce:

Customer accounts
Staff accounts
Role-based permissions
Secure session management
27.6 Formal AI Evaluation

Introduce systematic evaluation of:

RAG retrieval quality
Answer relevance
Faithfulness
Hallucination
Agent routing accuracy
End-to-end response quality
27.7 Observability

Add:

Structured logging
Agent execution tracing
Performance monitoring
Error monitoring
Usage analytics
27.8 Additional Business Integrations

Future versions could integrate with:

Email
SMS
WhatsApp
Accounting systems
Inventory systems
Payment providers
Customer relationship management systems
28. Capstone Significance

KenyaBiz AI demonstrates how modern AI technologies can be combined to solve practical business problems.

The project demonstrates practical implementation of:

Large Language Models
Multi-agent systems
LangGraph
LangChain
Retrieval-Augmented Generation
Conversational state management
Tool-based business processing
Database integration
Automated document generation
Payment workflow simulation
Automated software testing
Streamlit application development

The project also demonstrates how AI can be structured into specialized components rather than relying on a single general-purpose chatbot.

29. Conclusion

KenyaBiz AI provides a practical multi-agent architecture for automating common SME customer and business workflows.

The system combines conversational AI with structured business logic to support:

Business Questions
       ↓
Product Search
       ↓
Pricing
       ↓
Quotations
       ↓
Orders
       ↓
Invoices
       ↓
Payments

Its LangGraph-based architecture allows different agents to specialize in different business functions while maintaining shared conversation state.

The current implementation provides a functional prototype with:

Multi-agent orchestration
RAG-based business support
Product catalogue
Product pricing
Stock validation
Quotations
Multi-turn order processing
PDF invoice generation
Simulated M-PESA payments
CLI interface
Streamlit interface
Automated testing
200 passing tests
14 end-to-end workflow scenarios

The architecture provides a foundation that can be extended toward semantic RAG, live payment integration, production databases, authentication, inventory management, formal AI evaluation, and production deployment.

30. Author

Ambrose Ltiripwa Lengerpei

Data Scientist/AI developer

Kenya

31. Repository

GitHub Repository:

https://github.com/Lengerpei/KENYABIZ-AI

32. Project Status

Status: Capstone Prototype Complete

Current implementation includes:

 Multi-agent architecture
 LangGraph orchestration
 Supervisor routing
 Support Agent
 Sales Agent
 Order Agent
 Invoice Agent
 Payment Agent
 Business knowledge RAG
 Product catalogue
 Product pricing
 Stock validation
 Quotations
 Multi-turn order workflow
 Order confirmation
 PDF invoice generation
 Simulated M-PESA payment
 SQLite database
 CLI interface
 Streamlit interface
 Automated agent tests
 Product tests
 Quotation tests
 End-to-end workflow tests
 Error-handling tests
 200 automated tests passing
 14 workflow scenarios passing

Quick Start
CLI
python -m src.main

Streamlit
streamlit run src/streamlit_app.py

Tests
pytest tests -q

License

This project was developed as an AI capstone project for educational and demonstration purposes.
