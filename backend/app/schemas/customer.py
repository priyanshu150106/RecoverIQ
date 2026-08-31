from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    name: str = Field(..., description="Customer full name")
    email: str = Field(..., description="Customer email address")
    phone: Optional[str] = Field(None, description="Customer phone number")


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    total_paid: int  # in paise
    created_at: datetime

    class Config:
        from_attributes = True
