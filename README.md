# Multi-Tenant Invoice Reconciliation API

Invoice reconciliation system with REST and GraphQL APIs, built with Python 3.13, FastAPI, Strawberry GraphQL, and SQLAlchemy 2.0.

## Setup and Run Instructions

### Prerequisites
- Python 3.13.5

### Quick Start

```bash
# 1. Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Or you can use sh files to setup and run.
```bash
./setup.sh
./run.sh
```
The API will be available at:
- REST API Docs: http://localhost:8000/docs
- GraphQL Playground: http://localhost:8000/graphql

### Running Tests

```bash
pytest -v
```

Expected: 10 tests pass

## Testing the API

### REST API Testing (Browser)

1. Start the server: `uvicorn app.main:app --reload`
2. Open http://localhost:8000/docs
3. Use the interactive Swagger UI to test endpoints

### REST API Testing (Command Line)

```bash
# Create tenant
curl -X POST "http://localhost:8000/tenants" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Company"}'

# Create invoice (replace 1 with tenant_id)
curl -X POST "http://localhost:8000/tenants/1/invoices" \
  -H "Content-Type: application/json" \
  -d '{"amount": "500.00", "invoice_number": "INV-001"}'

# Import transactions
curl -X POST "http://localhost:8000/tenants/1/bank-transactions/import" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-1" \
  -d '{"transactions": [{"posted_at": "2024-01-15T10:00:00", "amount": "500.00", "description": "Payment"}]}'

# Run reconciliation
curl -X POST "http://localhost:8000/tenants/1/reconcile"

# Get AI explanation
curl "http://localhost:8000/tenants/1/reconcile/explain?invoice_id=1&transaction_id=1"
```

### GraphQL Testing (Browser - Recommended)

1. Start the server: `uvicorn app.main:app --reload`
2. Open http://localhost:8000/graphql
3. Use the GraphQL Playground to run queries:

**Create Tenant:**
```graphql
mutation {
  createTenant(input: { name: "Test Company" }) {
    id
    name
  }
}
```

**Query Tenants:**
```graphql
query {
  tenants {
    id
    name
  }
}
```

**Create Invoice:**
```graphql
mutation {
  createInvoice(tenantId: 1, input: { amount: "500.00", invoiceNumber: "INV-001" }) {
    id
    amount
    status
  }
}
```

**Get AI Explanation:**
```graphql
query {
  explainReconciliation(tenantId: 1, invoiceId: 1, transactionId: 1) {
    explanation
  }
}
```

### GraphQL Testing (Command Line)

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ tenants { id name } }"}'
```

### AI Explanation Testing

The AI explanation works without an OpenAI API key (uses fallback).

**Test without API key:**
```bash
unset OPENAI_API_KEY
curl "http://localhost:8000/tenants/1/reconcile/explain?invoice_id=1&transaction_id=1"
```

Expected: Returns deterministic explanation based on match criteria.

## Key Design Decisions and Tradeoffs

### Architecture

**Clean separation of concerns:**
- Models: SQLAlchemy ORM models
- Schemas: Pydantic validation
- Services: Business logic (reusable by REST and GraphQL)
- API: REST endpoints (FastAPI)
- GraphQL: Queries and mutations (Strawberry)

**Tradeoff:** More files but better maintainability and testability.

### Multi-Tenant Isolation

**Approach:** Every database query filters by `tenant_id`. All service methods require `tenant_id` as a parameter.

**Tradeoff:** Slightly more verbose queries but ensures data isolation at the database level.

### Database

**SQLite for development:** Simple setup, no external dependencies.

**Tradeoff:** Not suitable for production scale, but easy to swap for PostgreSQL.

### AI Integration

**Fallback-first design:** System works without OpenAI API key using deterministic explanations.

**Tradeoff:** Less sophisticated explanations without API key, but system remains functional.

## Reconciliation Scoring Approach

**Scoring algorithm (0-100 points):**

1. **Amount Matching (40 points max)**
   - Exact match: 40 points
   - Within 1% tolerance: 30 points
   - Within 5% tolerance: 15 points

2. **Date Proximity (20 points max)**
   - Same day: 20 points
   - Within 1 day: 15 points
   - Within 3 days: 10 points
   - Within 7 days: 5 points

3. **Text Similarity (20 points max)**
   - Uses Python's `difflib.SequenceMatcher` to compare descriptions
   - Score = similarity_ratio × 20

4. **Vendor Name Bonus (10 points max)**
   - If vendor name appears in transaction description: +10 points

**Minimum threshold:** Matches with score < 30 are not proposed.

**Design rationale:** Deterministic, explainable, fast, and handles common real-world scenarios.

## Idempotency Approach

**Implementation:**

1. **Idempotency Key Storage:** Keys stored in database with:
   - The key itself (unique per tenant)
   - SHA-256 hash of request payload
   - Cached response data

2. **Request Flow:**
   - Same key + same payload hash → return cached response (200)
   - Same key + different payload hash → return 409 Conflict
   - New key → process request and store key

3. **Transaction Safety:** Idempotency check and transaction import happen in the same database transaction.

**Design rationale:** Prevents duplicate imports on retries, maintains data integrity, and provides clear error handling.

## Tests

All tests run locally with pytest. Test coverage includes:

- Invoice CRUD operations
- Bank transaction import with idempotency
- Reconciliation matching algorithm
- Match confirmation workflow
- AI explanation (mocked and fallback)
- Multi-tenant data isolation

Run tests:
```bash
pytest -v
```

Expected: 10 tests pass.

## Project Structure

```
app/
├── models/          # Database models
├── schemas/         # Pydantic schemas
├── services/        # Business logic
├── api/             # REST endpoints
├── graphql/         # GraphQL schema
├── database.py      # DB configuration
└── main.py          # FastAPI app

tests/               # Test suite
requirements.txt     # Dependencies
```

## Environment Variables (Optional)

Create `.env` file:
```
DATABASE_URL=sqlite:///./invoice_reconciliation.db
OPENAI_API_KEY=your_key_here  # Optional
```

## API Endpoints

### REST API
- `POST /tenants` - Create tenant
- `GET /tenants` - List tenants
- `POST /tenants/{id}/invoices` - Create invoice
- `GET /tenants/{id}/invoices` - List invoices (with filters)
- `DELETE /tenants/{id}/invoices/{id}` - Delete invoice
- `POST /tenants/{id}/bank-transactions/import` - Import transactions (with Idempotency-Key header)
- `POST /tenants/{id}/reconcile` - Run reconciliation
- `POST /tenants/{id}/reconcile/matches/{id}/confirm` - Confirm match
- `GET /tenants/{id}/reconcile/explain?invoice_id=X&transaction_id=Y` - Get AI explanation

### GraphQL
- Queries: `tenants`, `invoices`, `bankTransactions`, `matchCandidates`, `explainReconciliation`
- Mutations: `createTenant`, `createInvoice`, `deleteInvoice`, `importBankTransactions`, `reconcile`, `confirmMatch`

Access GraphQL Playground at http://localhost:8000/graphql
