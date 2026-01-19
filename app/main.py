"""Main FastAPI application."""
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from app.api import tenants, invoices, transactions, reconciliation
from app.graphql.schema import schema
from app.database import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Invoice Reconciliation API",
    description="Multi-Tenant Invoice Reconciliation API with REST and GraphQL",
    version="1.0.0",
)

# Include REST routers
app.include_router(tenants.router)
app.include_router(invoices.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)

# Include GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Invoice Reconciliation API",
        "docs": "/docs",
        "graphql": "/graphql",
    }
