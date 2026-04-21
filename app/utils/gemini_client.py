import json
from io import BytesIO
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import AIServiceError
from app.models.schemas import DeliveryExtraction


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    def extract_delivery_data(self, file_bytes: bytes, filename: str, content_type: str | None) -> DeliveryExtraction:
        mime_type = content_type or self._guess_mime_type(filename)
        prompt = (
            "Extract delivery note fields and return only valid JSON with keys "
            "po_number, item_code, delivered_qty."
        )
        try:
            response = self.model.generate_content(self._build_delivery_request(file_bytes, filename, mime_type, prompt))
            payload = self._extract_json(response.text)
            return DeliveryExtraction.model_validate(payload)
        except google_exceptions.PermissionDenied as exc:
            raise AIServiceError(
                "Gemini access was denied for the configured project. Check the API key and project access."
            ) from exc
        except (google_exceptions.GoogleAPICallError, ValueError, ValidationError, json.JSONDecodeError) as exc:
            raise AIServiceError("Gemini could not process the delivery note right now.") from exc

    def generate_chat_response(self, message: str, context: dict[str, Any]) -> str:
        prompt = (
            "You are a support chatbot for a supply chain management system. "
            "Answer the user using all relevant information from the supplied database context across every table. "
            "Write concise, professional, user-friendly responses in natural language.\n\n"
            "For delivery status questions, format the response as a clean summary instead of exposing raw database fields. "
            "Do not mention technical field names such as ID, Supplier ID, invoice_id, delivery_id, created_at, updated_at, or table names. "
            "Highlight only the most important details: PO Number, Item Code, Delivered Quantity, Delivery Date, and Status. "
            "Convert timestamps into a readable date format such as 15 April 2026. "
            "If there are multiple matching delivery records, summarize them in a short list. "
            "If no delivery data is found, reply exactly: No delivery records found. "
            "Avoid unnecessary technical explanations such as saying you can provide more information or referring to database context.\n\n"
            "For dispute-related responses, clearly show the expected quantity versus the delivered quantity. "
            "State whether the issue is a shortfall or an excess delivery, and include the difference in units in plain language. "
            "Example phrasing: Expected: 50 units, Delivered: 40 units, Shortfall: 10 units. "
            "If the delivery exceeds the expected amount, use wording such as: Expected: 50 units, Delivered: 60 units, Excess: 10 units. "
            "Keep dispute summaries concise and professional.\n\n"
            "Use this format for delivery status responses:\n"
            "Delivery Status Summary:\n\n"
            "PO Number: <value>\n"
            "Item: <value>\n"
            "Quantity Delivered: <value> units\n"
            "Delivery Date: <readable date>\n"
            "Status: <value>\n\n"
            "For dispute summaries, include these lines when the data is available:\n"
            "Expected Quantity: <value> units\n"
            "Delivered Quantity: <value> units\n"
            "Shortfall: <value> units\n"
            "or\n"
            "Excess: <value> units\n\n"
            "If the context is insufficient for non-delivery questions, say what information is missing in simple language.\n\n"
            f"User message: {message}\n\n"
            f"Database context:\n{json.dumps(context, indent=2)}"
        )
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except google_exceptions.PermissionDenied as exc:
            raise AIServiceError(
                "Gemini access was denied for the configured project. Check the API key and project access."
            ) from exc
        except google_exceptions.GoogleAPICallError as exc:
            raise AIServiceError("Gemini could not generate a chat response right now.") from exc

    @staticmethod
    def _extract_json(raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        return json.loads(cleaned)

    def _build_delivery_request(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        prompt: str,
    ) -> list[Any]:
        if filename.lower().endswith(".docx"):
            docx_text = self._extract_docx_text(file_bytes)
            return [f"{prompt}\n\nDelivery note text:\n{docx_text}"]
        return [{"mime_type": mime_type, "data": file_bytes}, prompt]

    @staticmethod
    def _extract_docx_text(file_bytes: bytes) -> str:
        try:
            with ZipFile(BytesIO(file_bytes)) as archive:
                document_xml = archive.read("word/document.xml")
        except (BadZipFile, KeyError) as exc:
            raise AIServiceError("The uploaded DOCX file could not be read.") from exc

        root = ElementTree.fromstring(document_xml)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        lines: list[str] = []

        for paragraph in root.findall(".//w:p", namespace):
            text_runs = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
            if text_runs:
                lines.append("".join(text_runs))

        extracted = "\n".join(lines).strip()
        if not extracted:
            raise AIServiceError("The uploaded DOCX file did not contain readable text.")
        return extracted

    @staticmethod
    def _guess_mime_type(filename: str) -> str:
        lowered = filename.lower()
        if lowered.endswith(".pdf"):
            return "application/pdf"
        if lowered.endswith(".docx"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if lowered.endswith(".png"):
            return "image/png"
        if lowered.endswith(".jpg") or lowered.endswith(".jpeg"):
            return "image/jpeg"
        return "application/octet-stream"
