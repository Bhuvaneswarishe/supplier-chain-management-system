import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from postgrest.exceptions import APIError
from supabase import Client, create_client

from app.core.exceptions import AppError
from app.core.config import get_settings


class SupabaseRepository:
    def __init__(self, client: Client) -> None:
        self.client = client
        self.invoice_table = "invoices"
        settings = get_settings()
        self.supabase_url = settings.supabase_url.rstrip("/")
        self.supabase_key = settings.supabase_key
        self.chat_tables = settings.supabase_chat_tables

    def get_invoice(self, supplier_id: str, po_number: str, item_code: str) -> dict | None:
        try:
            response = (
                self.client.table(self.invoice_table)
                .select("*")
                .eq("supplier_id", supplier_id)
                .eq("po_number", po_number)
                .eq("item_code", item_code)
                .limit(1)
                .execute()
            )
        except APIError as exc:
            self._raise_query_error(exc, po_number)
        return response.data[0] if response.data else None

    def get_invoices_by_po_number(self, po_number: str, item_code: str) -> list[dict]:
        try:
            response = (
                self.client.table(self.invoice_table)
                .select("*")
                .eq("po_number", po_number)
                .eq("item_code", item_code)
                .execute()
            )
        except APIError as exc:
            self._raise_query_error(exc, po_number)
        return response.data or []

    def create_delivery_record(
        self,
        supplier_id: str | None,
        invoice_id: int | None,
        po_number: str,
        item_code: str,
        delivered_qty: int,
    ) -> dict:
        payload = {
            "supplier_id": supplier_id,
            "invoice_id": invoice_id,
            "po_number": po_number,
            "item_code": item_code,
            "delivered_qty": delivered_qty,
        }
        response = self.client.table("delivery_records").insert(payload).execute()
        return response.data[0]

    def create_dispute(
        self,
        delivery_id: int,
        supplier_id: str | None,
        invoice_id: int | None,
        issue_type: str,
        invoice_qty: int | None,
        delivered_qty: int,
    ) -> dict:
        payload = {
            "invoice_id": invoice_id,
            "delivery_id": delivery_id,
            "supplier_id": supplier_id,
            "issue_type": issue_type,
            "invoice_qty": invoice_qty,
            "delivered_qty": delivered_qty,
            "status": "open",
        }
        response = self.client.table("disputes").insert(payload).execute()
        return response.data[0]

    def get_chat_context(self, limit: int = 10) -> dict:
        context: dict[str, list[dict] | dict[str, str]] = {}
        table_errors: dict[str, str] = {}

        for table_name in self.list_accessible_tables():
            try:
                response = self.client.table(table_name).select("*").limit(limit).execute()
                context[table_name] = response.data or []
            except APIError as exc:
                table_errors[table_name] = str(exc)

        if table_errors:
            context["_table_errors"] = table_errors

        return context

    def list_accessible_tables(self) -> list[str]:
        if self.chat_tables:
            return sorted(set(self.chat_tables))

        discovered_tables = self._discover_table_names()
        if discovered_tables:
            return discovered_tables

        return sorted(
            {
                "delivery_records",
                "disputes",
                self.invoice_table,
                "onboarding_docs",
                "rfps",
                "supplier_admin_reviews",
                "suppliers",
                "support_tickets",
            }
        )

    def _discover_table_names(self) -> list[str]:
        request = Request(
            f"{self.supabase_url}/rest/v1/",
            headers={
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Accept": "application/openapi+json",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            return []

        paths = payload.get("paths", {})
        table_names = {
            path.strip("/").split("/")[0]
            for path in paths
            if path.startswith("/")
            and not path.startswith("/rpc/")
            and path.strip("/")
        }
        return sorted(table_names)

    @staticmethod
    def _raise_query_error(exc: APIError, po_number: str) -> None:
        if exc.code == "22P02":
            raise AppError(
                detail=(
                    f"Extracted PO number '{po_number}' could not be used with the current Supabase schema."
                ),
                status_code=400,
            ) from exc
        raise exc


def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


def get_supabase_repository() -> SupabaseRepository:
    return SupabaseRepository(get_supabase_client())
