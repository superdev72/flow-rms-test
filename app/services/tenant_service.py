"""Tenant service."""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.tenant import Tenant


class TenantService:
    """Service for tenant operations."""

    @staticmethod
    def create_tenant(db: Session, name: str) -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(name=name)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def get_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
        """Get a tenant by ID."""
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()

    @staticmethod
    def list_tenants(db: Session, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """List all tenants."""
        return db.query(Tenant).offset(skip).limit(limit).all()
