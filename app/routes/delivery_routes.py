from fastapi import APIRouter, Depends, File, UploadFile

from app.db.supabase_client import SupabaseRepository, get_supabase_repository
from app.models.schemas import DeliveryUploadResponse
from app.services.delivery_service import DeliveryService
from app.utils.gemini_client import GeminiClient

router = APIRouter(tags=["delivery"])


def get_delivery_service(
    repository: SupabaseRepository = Depends(get_supabase_repository),
) -> DeliveryService:
    return DeliveryService(repository=repository, gemini_client=GeminiClient())


@router.post("/upload-delivery-note", response_model=DeliveryUploadResponse)
async def upload_delivery_note(
    file: UploadFile = File(...),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryUploadResponse:
    return await service.process_delivery_note(file)
