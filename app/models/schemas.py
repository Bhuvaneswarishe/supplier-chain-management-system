from typing import Literal

from pydantic import BaseModel, Field


class DeliveryExtraction(BaseModel):
    po_number: str = Field(min_length=1)
    item_code: str = Field(min_length=1)
    delivered_qty: int = Field(ge=0)


class DeliveryUploadResponse(BaseModel):
    status: Literal["matched", "disputed"]
    issues: list[str]
    delivery_id: int


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str
