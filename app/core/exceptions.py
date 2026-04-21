class AppError(Exception):
    def __init__(self, detail: str, status_code: int = 500) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AIServiceError(AppError):
    def __init__(self, detail: str = "AI service is currently unavailable.") -> None:
        super().__init__(detail=detail, status_code=503)
