# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api, ist_to_utc

import random
import string
import time

OPTIONAL_PAYMENT_FIELDS = [
    "currency",
    "mobile_country_code",
    "customer_email",
    "customer_phone",
    "customer_id",
    "return_url",
    "gateway_id",
    "merchant_id",
    "walletCheckBox",
    "cardsCheckBox",
    "netbankingCheckBox",
    "upiCheckBox",
    "consumerFinanceCheckBox",
    "otcCheckBox",
    "virtualAccountCheckBox",
    "shouldSendMail",
    "shouldSendSMS",
    "shouldSendWhatsapp",
    "showEmiOption",
    "standardEmi",
    "standard_credit",
    "standard_debit",
    "standard_cardless",
    "lowCostEmi",
    "low_cost_credit",
    "low_cost_debit",
    "low_cost_cardless",
    "noCostEmi",
    "no_cost_credit",
    "no_cost_debit",
    "no_cost_cardless",
    "showOnlyEmiOption",
    "mandate_max_amount",
    "mandate_frequency",
    "mandate_start_date",
    "mandate.revokable_by_customer",
    "mandate.block_funds",
    "mandate.frequency",
    "mandate.start_date",
    "mandate.end_date",
    "subventionAmount",
    "selectUDF",
    "offer_details",
    "options.create_mandate",
]


async def list_payment_links_v1_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Calls the Juspay Portal API to retrieve a list of payment links within a specified time range.

    Args:
        payload (dict): Should contain 'qFilters', 'date_from', and 'date_to' as required by the API.
            - qFilters: Query filters for the API (dict)
            - date_from: Start date/time in ISO 8601 format (required)
            - date_to: End date/time in ISO 8601 format (required)
            - offset: Pagination offset (optional, default 0)

    Returns:
        dict: The parsed JSON response from the List Payment Links API.

    Raises:
        Exception: If the API call fails.
    """
    host = await get_juspay_host_from_api(meta_info=meta_info)
    api_url = f"{host}/api/ec/v1/paymentLinks/list"

    request_payload = {}

    if "qFilters" in payload:
        request_payload["qFilters"] = payload["qFilters"]
    else:
        request_payload["qFilters"] = {
            "field": "order_source_object",
            "condition": "Equals",
            "val": "PAYMENT_LINK",
        }

    if "offset" in payload:
        request_payload["offset"] = payload["offset"]

    date_from_str = payload.get("date_from")
    date_to_str = payload.get("date_to")

    if not date_from_str or not date_to_str:
        raise ValueError("Both 'date_from' and 'date_to' are required in the payload")

    date_from_str = ist_to_utc(date_from_str)
    date_to_str = ist_to_utc(date_to_str)

    request_payload["filters"] = {
        "dateCreated": {"gte": date_from_str, "lte": date_to_str}
    }

    return await post(api_url, request_payload, None, meta_info)


def generate_order_id() -> str:
    """
    Generate a unique order ID with the following rules:
    - Alphanumeric characters only
    - Alphabets should be capital always
    - Length should be less than 21 characters

    Returns:
        str: Generated order ID
    """
    timestamp = str(int(time.time()))[-8:]
    random_chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    order_id = f"{timestamp}{random_chars}"

    if len(order_id) >= 21:
        order_id = order_id[:20]

    return order_id


async def create_payment_link_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates a payment link using the Juspay Portal API.

    Args:
        payload (dict): Should contain payment link creation parameters:
            Required:
            - amount: Payment amount (required)

            Optional:
            - currency: Payment currency (default: "INR")
            - customer_email: Customer email address
            - customer_phone: Customer phone number
            - customer_id: Unique customer identifier
            - order_id: Unique order identifier (auto-generated if not provided)
            - return_url: URL to redirect after payment
            - gateway_id: Gateway identifier
            - merchant_id: Merchant identifier
            - mobile_country_code: Country code (default: "+91")
            - payment_filter: Payment method filters with emiOptions
            - metaData: Additional metadata

            Note: If any EMI option is enabled in payment_filter.emiOptions,
                  at least one card type (credit/debit/cardless) must be enabled within that EMI type.

    Returns:
        dict: The parsed JSON response from the Create Payment Link API.

    Raises:
        Exception: If the API call fails or EMI validation fails.
    """
    host = "https://portal.juspay.in"
    api_url = f"{host}/ec/v1/paymentLinks"

    request_data = {}

    if "amount" in payload:
        request_data["amount"] = payload["amount"]

    is_hdfc = False
    if meta_info:
        token_response = meta_info.get("token_response")
        if isinstance(token_response, dict):
            valid_host = token_response.get("validHost")
            if valid_host in ["dashboard.smartgateway.hdfcbank.com", "dashboard.smartgateway.hdfcbank.com/"]:
                is_hdfc = True
    if is_hdfc:
        request_data["payment_page_client_id"] = meta_info["token_response"]["merchantId"]
    elif "payment_page_client_id" in payload:
        request_data["payment_page_client_id"] = payload["payment_page_client_id"]
    else:
        raise Exception("The payment page client id is missing. Can you please provide it?")

    wallet_enabled = payload.get("walletCheckBox", True)
    cards_enabled = payload.get("cardsCheckBox", True)
    netbanking_enabled = payload.get("netbankingCheckBox", True)
    upi_enabled = payload.get("upiCheckBox", True)
    consumer_finance_enabled = payload.get("consumerFinanceCheckBox", True)
    otc_enabled = payload.get("otcCheckBox", True)
    virtual_account_enabled = payload.get("virtualAccountCheckBox", True)

    request_data["walletCheckBox"] = wallet_enabled
    request_data["cardsCheckBox"] = cards_enabled
    request_data["netbankingCheckBox"] = netbanking_enabled
    request_data["upiCheckBox"] = upi_enabled
    request_data["consumerFinanceCheckBox"] = consumer_finance_enabled
    request_data["otcCheckBox"] = otc_enabled
    request_data["virtualAccountCheckBox"] = virtual_account_enabled

    if "payment_filter" not in payload:
        request_data["payment_filter"] = {}
    else:
        request_data["payment_filter"] = payload["payment_filter"].copy()

    request_data["payment_filter"]["allowDefaultOptions"] = True
    request_data["payment_filter"]["options"] = [
        {"paymentMethodType": "UPI", "enable": upi_enabled},
        {"paymentMethodType": "WALLET", "enable": wallet_enabled},
        {"paymentMethodType": "CARD", "enable": cards_enabled},
        {"paymentMethodType": "NB", "enable": netbanking_enabled},
        {"paymentMethodType": "OTC", "enable": otc_enabled},
        {"paymentMethodType": "VIRTUAL_ACCOUNT", "enable": virtual_account_enabled},
        {"paymentMethodType": "CONSUMER_FINANCE", "enable": consumer_finance_enabled},
    ]

    user_provided_order_id = "order_id" in payload and payload["order_id"]

    if user_provided_order_id:
        request_data["order_id"] = payload["order_id"]
    else:
        request_data["order_id"] = generate_order_id()

    request_data["showEmiOption"] = payload.get("showEmiOption", False)
    request_data["standardEmi"] = payload.get("standardEmi", False)
    request_data["standard_credit"] = payload.get("standard_credit", False)
    request_data["standard_debit"] = payload.get("standard_debit", False)
    request_data["standard_cardless"] = payload.get("standard_cardless", False)
    request_data["lowCostEmi"] = payload.get("lowCostEmi", False)
    request_data["low_cost_credit"] = payload.get("low_cost_credit", False)
    request_data["low_cost_debit"] = payload.get("low_cost_debit", False)
    request_data["low_cost_cardless"] = payload.get("low_cost_cardless", False)
    request_data["noCostEmi"] = payload.get("noCostEmi", False)
    request_data["no_cost_credit"] = payload.get("no_cost_credit", False)
    request_data["no_cost_debit"] = payload.get("no_cost_debit", False)
    request_data["no_cost_cardless"] = payload.get("no_cost_cardless", False)

    if "emiOptions" not in request_data["payment_filter"]:
        request_data["payment_filter"]["emiOptions"] = {}

    request_data["payment_filter"]["emiOptions"]["standardEmi"] = {
        "enable": request_data["standardEmi"],
        "credit": {"enable": request_data["standard_credit"]},
        "debit": {"enable": request_data["standard_debit"]},
        "cardless": {"enable": request_data["standard_cardless"]},
    }
    request_data["payment_filter"]["emiOptions"]["lowCostEmi"] = {
        "enable": request_data["lowCostEmi"],
        "credit": {"enable": request_data["low_cost_credit"]},
        "debit": {"enable": request_data["low_cost_debit"]},
        "cardless": {"enable": request_data["low_cost_cardless"]},
    }
    request_data["payment_filter"]["emiOptions"]["noCostEmi"] = {
        "enable": request_data["noCostEmi"],
        "credit": {"enable": request_data["no_cost_credit"]},
        "debit": {"enable": request_data["no_cost_debit"]},
        "cardless": {"enable": request_data["no_cost_cardless"]},
    }
    request_data["payment_filter"]["emiOptions"]["showOnlyEmi"] = False

    if "options" not in payload:
        request_data["options"] = {"create_mandate": "REQUIRED"}
    else:
        options = payload["options"].copy()
        if "create_mandate" not in options:
            options["create_mandate"] = "REQUIRED"
        request_data["options"] = options

    for field in OPTIONAL_PAYMENT_FIELDS:
        if field in payload:
            request_data[field] = payload[field]

    if "metaData" in payload:
        request_data["metaData"] = payload["metaData"]

    max_retries = 3
    retry_count = 0

    while retry_count <= max_retries:
        try:
            return await post(api_url, request_data, None, meta_info)

        except Exception as e:
            error_message = str(e).lower()

            order_id_conflict = any(
                keyword in error_message
                for keyword in [
                    "order_id already exists",
                    "order id already exists",
                    "duplicate order",
                    "order already exists",
                    "orderid already exists",
                ]
            )

            # Only retry if:
            # 1. It's an order ID conflict
            # 2. The order ID was generated (not user-provided)
            # 3. We haven't exceeded max retries
            if (
                order_id_conflict
                and not user_provided_order_id
                and retry_count < max_retries
            ):
                retry_count += 1
                request_data["order_id"] = generate_order_id()
                continue
            else:
                raise e

    raise Exception(f"Failed to create payment link after {max_retries} retries")


async def create_autopay_link_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Creates an autopay payment link using the Juspay Portal API.

    Autopay registration involves customers providing consent to initiate recurring payments.
    The registration of autopay and the debit of the actual order amount occur simultaneously.

    IMPORTANT: All required fields must be explicitly provided by the user. Do not assume or auto-generate these values.

    Args:
        payload (dict): Should contain autopay link creation parameters:
            Required (USER MUST PROVIDE ALL OF THESE):
            - amount: One-time payment amount (REQUIRED - ask user for specific amount)
            - mandate_max_amount: Max mandate amount for future payments (REQUIRED - ask user to specify this amount)
            - mandate_start_date: Mandate creation date in YYYY-MM-DD format (REQUIRED - ask user for specific date)
            - mandate_end_date: Future date after which mandate stops in YYYY-MM-DD format (REQUIRED - ask user for specific end date)
            - mandate_frequency: Payment frequency (REQUIRED - ask user to choose from: ONETIME, DAILY, WEEKLY, FORTNIGHTLY, BIMONTHLY, MONTHLY, QUARTERLY, HALFYEARLY, YEARLY, ASPRESENTED)

            Optional:
            - currency: Payment currency (default: "INR")
            - customer_email: Customer email address
            - customer_phone: Customer phone number
            - customer_id: Unique customer identifier
            - order_id: Unique order identifier (auto-generated if not provided)
            - return_url: URL to redirect after payment
            - gateway_id: Gateway identifier
            - merchant_id: Merchant identifier
            - mobile_country_code: Country code (default: "+91")
            - mandate.revokable_by_customer: Whether mandate is revokable by customer
            - mandate.block_funds: Whether to block funds for mandate
            - payment_filter: Payment method filters with emiOptions
            - options: Additional options (should include create_mandate)
            - metaData: Additional metadata

            Note: If any EMI option is enabled in payment_filter.emiOptions,
                  at least one card type (credit/debit/cardless) must be enabled within that EMI type.

    Returns:
        dict: The parsed JSON response from the Create Autopay Link API.

    Raises:
        Exception: If the API call fails or required autopay fields are missing.
    """
    is_hdfc = False
    if meta_info:
        token_response = meta_info.get("token_response")
        if isinstance(token_response, dict):
            valid_host = token_response.get("validHost")
            if valid_host in ["dashboard.smartgateway.hdfcbank.com", "dashboard.smartgateway.hdfcbank.com/"]:
                is_hdfc = True
    if is_hdfc:
        payload["payment_page_client_id"] = meta_info["token_response"]["merchantId"]
    elif "payment_page_client_id" not in payload:
        raise Exception("The payment page client id is missing. Can you please provide it?")
    required_autopay_fields = [
        "amount",
        "mandate_max_amount",
        "mandate_start_date",
        "mandate_end_date",
        "mandate_frequency",
    ]

    missing_fields = [
        field for field in required_autopay_fields if field not in payload
    ]
    if missing_fields:
        raise Exception(
            f"Missing required autopay fields. Please ask the user to provide: {', '.join(missing_fields)}"
        )

    valid_frequencies = [
        "ONETIME",
        "DAILY",
        "WEEKLY",
        "FORTNIGHTLY",
        "BIMONTHLY",
        "MONTHLY",
        "QUARTERLY",
        "HALFYEARLY",
        "YEARLY",
        "ASPRESENTED",
    ]
    if payload["mandate_frequency"] not in valid_frequencies:
        raise Exception(
            f"Invalid mandate_frequency '{payload['mandate_frequency']}'. Please ask user to choose from: {', '.join(valid_frequencies)}"
        )
        
    host = "https://portal.juspay.in"
    api_url = f"{host}/ec/v1/paymentLinks"

    request_data = {}

    for field in required_autopay_fields:
        if field in payload:
            request_data[field] = payload[field]

    if "payment_page_client_id" in payload:
        request_data["payment_page_client_id"] = payload["payment_page_client_id"]

    wallet_enabled = payload.get("walletCheckBox", True)
    cards_enabled = payload.get("cardsCheckBox", True)
    netbanking_enabled = payload.get("netbankingCheckBox", True)
    upi_enabled = payload.get("upiCheckBox", True)
    consumer_finance_enabled = payload.get("consumerFinanceCheckBox", True)
    otc_enabled = payload.get("otcCheckBox", True)
    virtual_account_enabled = payload.get("virtualAccountCheckBox", True)

    request_data["walletCheckBox"] = wallet_enabled
    request_data["cardsCheckBox"] = cards_enabled
    request_data["netbankingCheckBox"] = netbanking_enabled
    request_data["upiCheckBox"] = upi_enabled
    request_data["consumerFinanceCheckBox"] = consumer_finance_enabled
    request_data["otcCheckBox"] = otc_enabled
    request_data["virtualAccountCheckBox"] = virtual_account_enabled

    if "payment_filter" not in payload:
        request_data["payment_filter"] = {}
    else:
        request_data["payment_filter"] = payload["payment_filter"].copy()

    request_data["payment_filter"]["allowDefaultOptions"] = True
    request_data["payment_filter"]["options"] = [
        {"paymentMethodType": "UPI", "enable": upi_enabled},
        {"paymentMethodType": "WALLET", "enable": wallet_enabled},
        {"paymentMethodType": "CARD", "enable": cards_enabled},
        {"paymentMethodType": "NB", "enable": netbanking_enabled},
        {"paymentMethodType": "OTC", "enable": otc_enabled},
        {"paymentMethodType": "VIRTUAL_ACCOUNT", "enable": virtual_account_enabled},
        {"paymentMethodType": "CONSUMER_FINANCE", "enable": consumer_finance_enabled},
    ]

    user_provided_order_id = "order_id" in payload and payload["order_id"]
    if user_provided_order_id:
        request_data["order_id"] = payload["order_id"]
    else:
        request_data["order_id"] = generate_order_id()

    request_data["showEmiOption"] = payload.get("showEmiOption", False)
    request_data["standardEmi"] = payload.get("standardEmi", False)
    request_data["standard_credit"] = payload.get("standard_credit", False)
    request_data["standard_debit"] = payload.get("standard_debit", False)
    request_data["standard_cardless"] = payload.get("standard_cardless", False)
    request_data["lowCostEmi"] = payload.get("lowCostEmi", False)
    request_data["low_cost_credit"] = payload.get("low_cost_credit", False)
    request_data["low_cost_debit"] = payload.get("low_cost_debit", False)
    request_data["low_cost_cardless"] = payload.get("low_cost_cardless", False)
    request_data["noCostEmi"] = payload.get("noCostEmi", False)
    request_data["no_cost_credit"] = payload.get("no_cost_credit", False)
    request_data["no_cost_debit"] = payload.get("no_cost_debit", False)
    request_data["no_cost_cardless"] = payload.get("no_cost_cardless", False)

    if "emiOptions" not in request_data["payment_filter"]:
        request_data["payment_filter"]["emiOptions"] = {}

    request_data["payment_filter"]["emiOptions"]["standardEmi"] = {
        "enable": request_data["standardEmi"],
        "credit": {"enable": request_data["standard_credit"]},
        "debit": {"enable": request_data["standard_debit"]},
        "cardless": {"enable": request_data["standard_cardless"]},
    }
    request_data["payment_filter"]["emiOptions"]["lowCostEmi"] = {
        "enable": request_data["lowCostEmi"],
        "credit": {"enable": request_data["low_cost_credit"]},
        "debit": {"enable": request_data["low_cost_debit"]},
        "cardless": {"enable": request_data["low_cost_cardless"]},
    }
    request_data["payment_filter"]["emiOptions"]["noCostEmi"] = {
        "enable": request_data["noCostEmi"],
        "credit": {"enable": request_data["no_cost_credit"]},
        "debit": {"enable": request_data["no_cost_debit"]},
        "cardless": {"enable": request_data["no_cost_cardless"]},
    }
    request_data["payment_filter"]["emiOptions"]["showOnlyEmi"] = False

    if "options" not in payload:
        request_data["options"] = {"create_mandate": "REQUIRED"}
    else:
        options = payload["options"].copy()
        if "create_mandate" not in options:
            options["create_mandate"] = "REQUIRED"
        request_data["options"] = options

    for field in OPTIONAL_PAYMENT_FIELDS:
        if field in payload:
            request_data[field] = payload[field]


    if "metaData" in payload:
        request_data["metaData"] = payload["metaData"]

    max_retries = 3
    retry_count = 0

    while retry_count <= max_retries:
        try:
            return await post(api_url, request_data, None, meta_info)

        except Exception as e:
            error_message = str(e).lower()

            order_id_conflict = any(
                keyword in error_message
                for keyword in [
                    "order_id already exists",
                    "order id already exists",
                    "duplicate order",
                    "order already exists",
                    "orderid already exists",
                ]
            )

            if (
                order_id_conflict
                and not user_provided_order_id
                and retry_count < max_retries
            ):
                retry_count += 1
                request_data["order_id"] = generate_order_id()
                continue
            else:
                raise e

    raise Exception(f"Failed to create autopay link after {max_retries} retries")
