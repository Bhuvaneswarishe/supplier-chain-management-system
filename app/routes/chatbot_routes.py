from fastapi import APIRouter, Depends

from app.db.supabase_client import SupabaseRepository, get_supabase_repository
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chatbot_service import ChatbotService
from app.utils.gemini_client import GeminiClient

router = APIRouter(tags=["chatbot"])


def get_chatbot_service(
    repository: SupabaseRepository = Depends(get_supabase_repository),
) -> ChatbotService:
    return ChatbotService(repository=repository, gemini_client=GeminiClient())


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    service: ChatbotService = Depends(get_chatbot_service),
) -> ChatResponse:
    return ChatResponse(response=service.chat(payload.message))
