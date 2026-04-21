from app.db.supabase_client import SupabaseRepository
from app.utils.gemini_client import GeminiClient


class ChatbotService:
    def __init__(self, repository: SupabaseRepository, gemini_client: GeminiClient) -> None:
        self.repository = repository
        self.gemini_client = gemini_client

    def chat(self, message: str) -> str:
        context = self.repository.get_chat_context()
        return self.gemini_client.generate_chat_response(message=message, context=context)
