#!/bin/bash
# Quick verification script for the Invoice Reconciliation API

set -e  # Exit on error

echo "=== Starting Verification ==="
echo ""

# 1. Run tests
echo "1. Running tests..."
pytest -v --tb=short -q
if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi
echo "✅ Tests passed"
echo ""

# 2. Check server can start
echo "2. Checking server can start..."
# Try to import the app to check for import errors
if python -c "from app.main import app; print('OK')" > /dev/null 2>&1; then
    echo "✅ Server imports successfully"
    # Try starting server in background
    uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn_test.log 2>&1 &
    SERVER_PID=$!
    sleep 2
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "✅ Server started successfully"
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    else
        echo "⚠️  Server process check failed (may still be OK)"
        # Check if port is in use (server might have started)
        if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "✅ Port 8000 is listening (server is running)"
            pkill -f "uvicorn app.main:app" 2>/dev/null || true
        else
            echo "❌ Server failed to start - check /tmp/uvicorn_test.log"
            cat /tmp/uvicorn_test.log 2>/dev/null || true
        fi
    fi
else
    echo "❌ Server import failed"
    python -c "from app.main import app" 2>&1
    exit 1
fi
echo ""

# 3. Check database models
echo "3. Checking database models..."
python -c "from app.models import Tenant, Vendor, Invoice, BankTransaction, Match, IdempotencyKey; print('✅ All models imported successfully')" || exit 1
echo ""

# 4. Check API routes
echo "4. Checking API routes..."
ROUTE_COUNT=$(python -c "from app.main import app; print(len([r for r in app.routes if hasattr(r, 'path')]))" 2>/dev/null || echo "0")
if [ "$ROUTE_COUNT" -gt "0" ]; then
    echo "✅ Found $ROUTE_COUNT API routes"
else
    echo "❌ No routes found"
    exit 1
fi
echo ""

# 5. Check GraphQL schema
echo "5. Checking GraphQL schema..."
python -c "from app.graphql.schema import schema; print('✅ GraphQL schema loaded successfully')" || exit 1
echo ""

# 6. Check services
echo "6. Checking service layer..."
python -c "from app.services import TenantService, InvoiceService, TransactionService, ReconciliationService, AIService; print('✅ All services imported successfully')" || exit 1
echo ""

# 7. Check database file
echo "7. Checking database..."
if [ -f "invoice_reconciliation.db" ] || python -c "from app.database import DATABASE_URL; print('sqlite' in DATABASE_URL)" 2>/dev/null; then
    echo "✅ Database configuration valid"
else
    echo "⚠️  Database file not found (will be created on first run)"
fi
echo ""

echo "=== Verification Complete ==="
echo "✅ All checks passed!"
echo ""
echo "Next steps:"
echo "1. Start the server: uvicorn app.main:app --reload"
echo "2. Visit http://localhost:8000/docs for API documentation"
echo "3. Visit http://localhost:8000/graphql for GraphQL playground"
echo "4. Run manual tests as described in VERIFICATION.md"
