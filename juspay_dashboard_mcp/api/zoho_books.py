# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import json
import logging
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import quote, urlencode

from juspay_dashboard_mcp.api.utils import get_admin_host, post, sanitize_merchant_id

logger = logging.getLogger(__name__)

_DATE_KEYS = (
    "created_date",
    "created_date_start",
    "created_date_end",
    "created_date_before",
    "created_date_after",
    "due_date",
    "due_date_start",
    "due_date_end",
    "due_date_before",
    "due_date_after",
)

def _build_admin_body(payload: dict, meta_info: Optional[dict], mid_from_meta: Optional[str]) -> dict:
    merchant_id = sanitize_merchant_id(payload.get("merchantId"), mid_from_meta)
    if not merchant_id:
        raise ValueError("merchantId is required for admin/JUSPAY context.")
    tenant_id = (meta_info or {}).get("tenant_id")
    if not tenant_id:
        raise ValueError("tenantAccountId is required for admin/JUSPAY context.")
    return {"merchantId": merchant_id, "tenantAccountId": tenant_id}


def _today_from_context(meta_info: Optional[dict]) -> str:
    current_timestamp = (meta_info or {}).get("current_timestamp")
    if current_timestamp:
        try:
            return datetime.fromisoformat(current_timestamp.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except ValueError:
            logger.warning("Invalid current_timestamp in meta_info: %s", current_timestamp)
    return datetime.now().strftime("%Y-%m-%d")


def _first_of_month(date_value: str) -> str:
    return date.fromisoformat(date_value).replace(day=1).isoformat()


def _build_query_params(payload: dict, meta_info: Optional[dict]) -> tuple[dict[str, str], dict[str, Any]]:
    params: dict[str, str] = {}

    for key in _DATE_KEYS:
        value = payload.get(key)
        if value:
            params[key] = value

    if not params:
        today = _today_from_context(meta_info)
        params["created_date_start"] = _first_of_month(today)
        params["created_date_end"] = today

    status = payload.get("status")
    if status:
        params["status"] = status

    return params, dict(params)


def _parse_customer_names(response: dict) -> list[str]:
    names: list[str] = []
    for row in response.get("rows") or []:
        raw = row.get("value", "")
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            parsed = raw

        if isinstance(parsed, list):
            names.extend(str(item) for item in parsed if item)
        elif parsed:
            names.append(str(parsed))

    return list(dict.fromkeys(names))


def _parse_period(invoice: dict) -> Optional[str]:
    custom_fields = invoice.get("custom_fields") or []
    if isinstance(custom_fields, list):
        for cf in custom_fields:
            if isinstance(cf, dict) and cf.get("api_name") == "cf_period":
                return cf.get("value")
    return invoice.get("cf_period") or invoice.get("cf_period_unformatted")


def _to_float(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_invoices(raw_invoices: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_invoices, list):
        return []

    invoices = []
    for invoice in raw_invoices:
        if not isinstance(invoice, dict):
            continue
        invoices.append(
            {
                "invoice_id": invoice.get("invoice_id", ""),
                "invoice_number": invoice.get("invoice_number", ""),
                "status": invoice.get("status", ""),
                "amount": _to_float(invoice.get("total")),
                "amount_due": _to_float(invoice.get("balance")),
                "created_date": invoice.get("date", ""),
                "due_date": invoice.get("due_date", ""),
                "payment_expected_date": invoice.get("payment_expected_date", ""),
                "period": _parse_period(invoice),
                "invoice_url": str(invoice.get("invoice_url") or "").strip(),
            }
        )
    return invoices


async def list_zoho_books_invoices(payload: dict, meta_info: dict = None) -> dict:
    host, isadmin = await get_admin_host(meta_info=meta_info)

    token_response = (meta_info or {}).get("token_response") or {}
    mid_from_meta = token_response.get("merchantId") or (meta_info or {}).get("merchantId")

    body = _build_admin_body(payload, meta_info, mid_from_meta) if isadmin else {}
    path_prefix = "/ec/v1/admin" if isadmin else "/ec/v1"

    customer_name = payload.get("customer_name")
    if not customer_name:
        response = await post(f"{host}{path_prefix}/list/zohoBooksMerchantKeyValueMapping", body, None, meta_info)
        customer_names = _parse_customer_names(response)
        if not customer_names:
            return {
                "status": "error",
                "error": "No Zoho Books customer account configured for this merchant.",
            }
        if len(customer_names) > 1:
            return {
                "status": "customer_selection_required",
                "customer_names": customer_names,
                "message": f"Found {len(customer_names)} Zoho Books customer accounts. Please specify which one to use.",
            }
        customer_name = customer_names[0]

    query_params, date_range_used = _build_query_params(payload, meta_info)
    query_string = urlencode(query_params)
    api_url = f"{host}{path_prefix}/list/zohoBooks/invoices/{quote(customer_name, safe='')}"
    if query_string:
        api_url = f"{api_url}?{query_string}"

    response = await post(api_url, body, None, meta_info)
    invoices = _parse_invoices(response.get("invoices"))

    _SUMMARY_KEYS = {"invoice_number", "status", "amount", "invoice_url"}

    return {
        "status": "success",
        "customer_name": customer_name,
        "total_count": len(invoices),
        "invoices": [
            {k: v for k, v in inv.items() if k in _SUMMARY_KEYS}
            for inv in invoices
        ],
        "invoice_details": {
            inv["invoice_number"]: {k: v for k, v in inv.items() if k not in _SUMMARY_KEYS}
            for inv in invoices
        },
        "date_range_used": date_range_used,
        "page_context": response.get("page_context"),
        "message": response.get("message"),
    }
