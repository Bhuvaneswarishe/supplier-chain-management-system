from fastapi import UploadFile

from app.db.supabase_client import SupabaseRepository
from app.models.schemas import DeliveryUploadResponse
from app.utils.gemini_client import GeminiClient


class DeliveryService:
    def __init__(self, repository: SupabaseRepository, gemini_client: GeminiClient) -> None:
        self.repository = repository
        self.gemini_client = gemini_client

    async def process_delivery_note(self, upload: UploadFile) -> DeliveryUploadResponse:
        file_bytes = await upload.read()
        extracted = self.gemini_client.extract_delivery_data(
            file_bytes=file_bytes,
            filename=upload.filename or "upload.bin",
            content_type=upload.content_type,
        )

        issues: list[str] = []
        supplier_id: str | None = None
        invoice_id: int | None = None
        invoice_qty: int | None = None

        matching_invoices = self.repository.get_invoices_by_po_number(extracted.po_number, extracted.item_code)
        if not matching_invoices:
            issues.append("Invoice not found")
        elif len(matching_invoices) > 1:
            issues.append("Multiple invoices found for PO number and item code")
        else:
            invoice = matching_invoices[0]
            supplier_id = str(invoice["supplier_id"])
            invoice_id = int(invoice["id"])
            invoice_qty = int(invoice["quantity"])
            if extracted.delivered_qty < invoice_qty:
                issues.append("Shortfall")
            elif extracted.delivered_qty > invoice_qty:
                issues.append("Excess delivery")

        status = "matched" if not issues else "disputed"
        delivery_record = self.repository.create_delivery_record(
            supplier_id=supplier_id,
            invoice_id=invoice_id,
            po_number=extracted.po_number,
            item_code=extracted.item_code,
            delivered_qty=extracted.delivered_qty,
        )

        if status == "disputed":
            for issue in issues:
                self.repository.create_dispute(
                    delivery_id=delivery_record["id"],
                    supplier_id=supplier_id,
                    invoice_id=invoice_id,
                    issue_type=issue,
                    invoice_qty=invoice_qty,
                    delivered_qty=extracted.delivered_qty,
                )

        return DeliveryUploadResponse(
            status=status,
            issues=issues,
            delivery_id=delivery_record["id"],
        )
