"""Tenant schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TenantCreate(BaseModel):
    """Schema for creating a tenant."""
    name: str


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
