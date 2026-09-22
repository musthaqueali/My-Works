from pydantic import BaseModel, Field
from typing import Optional

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    google_id: Optional[str] = None
    auth_type: Optional[str] = "signin" # 'signin' or 'signup'
    centre_name: Optional[str] = None
    centre_code: Optional[str] = None
    phone: Optional[str] = None

class NormalLoginRequest(BaseModel):
    email: str
    password: str

class NormalRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    centre_name: Optional[str] = "Al-Madina Testing Station"
    centre_code: Optional[str] = "KL-11-PUC-408"
    phone: Optional[str] = "9847012345"



class CustomerPUCCreate(BaseModel):
    owner_name: str = Field(..., example="Arjun Kumar")
    plate_number: str = Field(..., example="TS08BA2535")
    mobile_number: str = Field(..., example="9104332181")
    validity_period: str = Field(default="1 Year")
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    fee_amount: float = Field(default=60.00)

class NotificationSendRequest(BaseModel):
    record_id: Optional[int] = None
    plate_number: str
    mobile_number: str
    owner_name: Optional[str] = "Valued Customer"
    expiry_date: Optional[str] = None
    channel: str = Field(default="SMS")

class CashfreeOrderRequest(BaseModel):
    plan_name: str = Field(..., example="Monthly Subscription (₹150/mo)")
    amount: float = Field(..., example=150.00)
    sms_credits: int = Field(default=1000)
    customer_name: Optional[str] = "Musthaque Ali"
    customer_phone: Optional[str] = "9847012345"

class CashfreeVerifyRequest(BaseModel):
    order_id: str
