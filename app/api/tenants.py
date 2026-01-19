"""Tenant REST endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.tenant_service import TenantService
from app.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=201)
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant."""
    return TenantService.create_tenant(db, tenant.name)


@router.get("", response_model=List[TenantResponse])
def list_tenants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all tenants."""
    return TenantService.list_tenants(db, skip=skip, limit=limit)
