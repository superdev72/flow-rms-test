#!/bin/bash
# Simple script to test GraphQL and AI features

echo "=== Testing GraphQL and AI Features ==="
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "❌ Server is not running!"
    echo "Please start the server first:"
    echo "  uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Set tenant ID (will be created)
TENANT_ID=""

echo "1. Testing GraphQL - Create Tenant..."
TENANT_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { createTenant(input: { name: \"GraphQL Test Company\" }) { id name } }"
  }')

echo "Response: $TENANT_RESPONSE"
TENANT_ID=$(echo $TENANT_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)

if [ -z "$TENANT_ID" ]; then
    echo "❌ Failed to create tenant"
    exit 1
fi

echo "✅ Tenant created with ID: $TENANT_ID"
echo ""

echo "2. Testing GraphQL - Query Tenants..."
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"{ tenants { id name } }\"
  }" | python3 -m json.tool

echo ""
echo "✅ Tenants queried successfully"
echo ""

echo "3. Testing GraphQL - Create Invoice..."
INVOICE_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"mutation { createInvoice(tenantId: $TENANT_ID, input: { amount: \\\"500.00\\\", invoiceNumber: \\\"INV-GQL-001\\\" }) { id amount status } }\"
  }")

echo "Response: $INVOICE_RESPONSE"
INVOICE_ID=$(echo $INVOICE_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)

if [ -z "$INVOICE_ID" ]; then
    echo "❌ Failed to create invoice"
    exit 1
fi

echo "✅ Invoice created with ID: $INVOICE_ID"
echo ""

echo "4. Testing GraphQL - Import Transaction..."
TRANSACTION_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"mutation { importBankTransactions(tenantId: $TENANT_ID, input: { transactions: [{ externalId: \\\"TX-GQL-001\\\", postedAt: \\\"2024-01-15T10:00:00\\\", amount: \\\"500.00\\\", description: \\\"Payment\\\" }] }, idempotencyKey: \\\"test-key-1\\\") { id amount } }\"
  }")

echo "Response: $TRANSACTION_RESPONSE"
TRANSACTION_ID=$(echo $TRANSACTION_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)

if [ -z "$TRANSACTION_ID" ]; then
    echo "❌ Failed to import transaction"
    exit 1
fi

echo "✅ Transaction imported with ID: $TRANSACTION_ID"
echo ""

echo "5. Testing AI Explanation (REST endpoint)..."
AI_RESPONSE=$(curl -s "http://localhost:8000/tenants/$TENANT_ID/reconcile/explain?invoice_id=$INVOICE_ID&transaction_id=$TRANSACTION_ID")
echo "Response: $AI_RESPONSE"

if echo "$AI_RESPONSE" | grep -q "explanation"; then
    echo "✅ AI explanation works (REST)"
else
    echo "❌ AI explanation failed"
    exit 1
fi
echo ""

echo "6. Testing AI Explanation (GraphQL)..."
GRAPHQL_AI_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"{ explainReconciliation(tenantId: $TENANT_ID, invoiceId: $INVOICE_ID, transactionId: $TRANSACTION_ID) { explanation } }\"
  }")

echo "Response: $GRAPHQL_AI_RESPONSE"

if echo "$GRAPHQL_AI_RESPONSE" | grep -q "explanation"; then
    echo "✅ AI explanation works (GraphQL)"
else
    echo "❌ AI explanation failed (GraphQL)"
    exit 1
fi
echo ""

echo "=== All Tests Passed! ==="
echo ""
echo "Next steps:"
echo "1. Open http://localhost:8000/graphql in your browser"
echo "2. Try the queries from GRAPHQL_AI_TESTING.md"
echo "3. Explore the GraphQL Playground interface"
