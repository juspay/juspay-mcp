# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import json
import mcp.types as types
import inspect
import logging
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport

from juspay_mcp import response_schema
from juspay_mcp.api import *
import juspay_mcp.api_schema as api_schema
import juspay_mcp.utils as util

logger = logging.getLogger(__name__)
app = Server("juspay")

from contextvars import ContextVar
juspay_request_credentials: ContextVar[dict | None] = ContextVar('juspay_request_credentials', default=None)

def set_juspay_request_credentials(credentials):
    """Set Juspay credentials for the current request context."""
    juspay_request_credentials.set(credentials)
    
def get_juspay_request_credentials():
    """Get Juspay credentials from current request context."""
    return juspay_request_credentials.get()

AVAILABLE_TOOLS = [
    util.make_api_config(
        name="session_api_juspay",
        description="Creates a new Juspay session for a given order.",
        model=api_schema.session.JuspaySessionPayload,
        handler=session.session_api_juspay,
        response_schema=response_schema.session_response_schema,
    ),
    util.make_api_config(
        name="order_status_api_juspay",
        description="""This is a Server-to-Server API that returns the status of the order along with other details in encrypted format using its `order_id`.

Key features:
- Returns order status and comprehensive order details in encrypted format.
- Provides payment method details (card, UPI, netbanking, wallet information).
- Includes transaction details (txn_id, gateway information, amounts).
- Shows refund information if applicable.
- Includes payment gateway response details.
- Supports optional query parameter to receive complete gateway response.

Use this tool to check the current status of an order, verify payment completion before order fulfillment, retrieve transaction details for reconciliation, or fetch comprehensive order information for customer support inquiries. Essential for validating amount and status before fulfilling orders.""",
        model=api_schema.order.JuspayOrderStatusPayload,
        handler=order.order_status_api_juspay,
        response_schema=response_schema.order_status_response_schema,
    ),
    util.make_api_config(
        name="create_refund_juspay",
        description="Initiates a refund for a specific Juspay order using its `order_id`.",
        model=api_schema.refund.JuspayRefundPayload,
        handler=refund.create_refund_juspay,
        response_schema=response_schema.refund_creation_response_schema,
    ),
    util.make_api_config(
        name="get_customer_juspay",
        description="""This is a Server-to-Server API which returns the customer object for the given identifier using the `customer_id`.

Key features:
- Returns complete customer information associated with the customer_id.
- Provides customer details including email, mobile number, name, and creation dates.
- Supports optional query parameter to get client auth token for SDK integration.
- Returns customer object with object_reference_id and contact information.

Use this tool to retrieve customer profile information, verify customer details, fetch customer data for order processing, or obtain customer information for support inquiries. Essential for customer management and authentication workflows.""",
        model=api_schema.customer.JuspayGetCustomerPayload,
        handler=customer.get_customer_juspay,
        response_schema=response_schema.get_customer_response_schema,
    ),
    util.make_api_config(
        name="create_customer_juspay",
        description="Creates a new customer in Juspay with the provided details.",
        model=api_schema.customer.JuspayCreateCustomerPayload,
        handler=customer.create_customer_juspay,
        response_schema=response_schema.create_customer_response_schema,
    ),
    util.make_api_config(
        name="update_customer_juspay",
        description="Updates an existing customer in Juspay with the provided details.",
        model=api_schema.customer.JuspayUpdateCustomerPayload,
        handler=customer.update_customer_juspay,
        response_schema=response_schema.update_customer_response_schema,
    ),
    util.make_api_config(
        name="order_fulfillment_sync_juspay",
        description="Updates the fulfillment status of a Juspay order.",
        model=api_schema.order.JuspayOrderFulfillmentPayload,
        handler=order.order_fulfillment_sync,
        response_schema=response_schema.order_fulfillment_response_schema,
    ),
    util.make_api_config(
        name="create_txn_refund_juspay",
        description="Initiates a refund based on transaction ID (instead of order ID).",
        model=api_schema.refund.JuspayTxnRefundPayload,
        handler=refund.create_txn_refund_juspay,
        response_schema=response_schema.txn_refund_response_schema,
    ),
    util.make_api_config(
        name="create_txn_juspay",
        description="Creates an order and processes payment in a single API call.",
        model=api_schema.txn.JuspayCreateTxnPayload,
        handler=txn.create_txn_juspay,
        response_schema=response_schema.create_txn_response_schema,
    ),
    util.make_api_config(
        name="create_moto_txn_juspay",
        description="Creates an order with MOTO (Mail Order/Telephone Order) authentication.",
        model=api_schema.txn.JuspayCreateMotoTxnPayload,
        handler=txn.create_moto_txn_juspay,
        response_schema=response_schema.create_moto_txn_response_schema,
    ),
    util.make_api_config(
        name="add_card_juspay",
        description="Adds a new card to the Juspay system for a customer.",
        model=api_schema.card.JuspayAddCardPayload,
        handler=card.add_card_juspay,
        response_schema=response_schema.add_card_response_schema,
    ),
    util.make_api_config(
        name="list_cards_juspay",
        description="""List all the cards stored for a customer using the `customer_id`. This API returns only tokens and other metadata relevant to the cards stored in Juspay Locker.

Key features:
- Returns all cards stored for a specific customer.
- Provides card tokens and metadata from Juspay Locker.
- Includes card details such as brand, issuer, expiry, last four digits, and card type.
- Shows tokenization status and CVV-less support information.
- Supports optional parameters to check CVV-less support, mandate support, and ATM PIN auth support.
- Returns card fingerprint, card reference, and PAR for tokens.

Use this tool to retrieve a customer's saved cards for payment processing, display saved payment methods in checkout flows, verify card tokenization status, or check card eligibility for specific payment features like CVV-less transactions or mandates. Essential for implementing saved card functionality and one-click payments.""",
        model=api_schema.card.JuspayListCardsPayload,
        handler=card.list_cards_juspay,
        response_schema=response_schema.list_cards_response_schema,
    ),
    util.make_api_config(
        name="delete_card_juspay",
        description="Deletes a saved card from the Juspay system.",
        model=api_schema.card.JuspayDeleteCardPayload,
        handler=card.delete_card_juspay,
        response_schema=response_schema.delete_card_response_schema,
    ),
    util.make_api_config(
        name="update_card_juspay",
        description="Updates details for a saved card.",
        model=api_schema.card.JuspayUpdateCardPayload,
        handler=card.update_card_juspay,
        response_schema=response_schema.update_card_response_schema,
    ),
    util.make_api_config(
        name="get_card_info_juspay",
        description="""Get card details using card BIN (Bank Identification Number) up to 9 digits. This Server-to-Server API can also check if a card is eligible for ATM PIN, Mandate, direct OTP payments, or tokenization.

Key features:
- Accepts card BIN with variable length ranging from 6 to 9 digits.
- Returns card details including country, brand, bank, card type, and card sub-type.
- Supports eligibility checks for CVV-less payments (works only for Token BINs).

Use this tool to retrieve card information before processing payments, validate card eligibility for specific payment features, determine card issuer and type, or check support for advanced payment methods like mandates and tokenization. Essential for payment method validation and feature enablement.""",
        model=api_schema.card.JuspayCardInfoPayload,
        handler=card.get_card_info_juspay,
        response_schema=response_schema.card_info_response_schema,
    ),
    util.make_api_config(
        name="get_bin_list_juspay",
        description="""Get the list of BINs (Bank Identification Numbers) based on the authentication type.

Key features:
- Returns a list of eligible BINs for specified authentication type.
- Supports filtering by authentication type: "OTP" for native OTP supported BINs or "VIES" for VIES supported BINs.
- Provides BIN numbers as an array in the response.

Use this tool to retrieve BINs that support specific authentication methods, validate card eligibility for OTP or VIES authentication, or filter payment options based on supported authentication types. Essential for implementing authentication-specific payment flows.""",
        model=api_schema.card.JuspayBinListPayload,
        handler=card.get_bin_list_juspay,
        response_schema=response_schema.bin_list_response_schema,
    ),
    util.make_api_config(
        name="get_saved_payment_methods",
        description="""Fetch a customer's saved payment methods using the `customer_id`. This API helps create a faster and smoother checkout experience.

Key features:
- Retrieves saved payment methods for a specific customer.
- Supports fetching Virtual Payment Addresses (VPAs), Cards, and Wallets.
- Returns only supported payment methods under saved_payment_methods section.
- Lists unsupported payment methods separately if present.
- Supports two authentication methods: API Key (Basic Auth) or Client Authentication Token.
- Accepts optional order_id parameter to retrieve specific payment methods.

Use this tool to display saved payment options during checkout, enable one-click payments, retrieve customer's preferred payment methods, or create a personalized checkout experience. Essential for implementing express checkout and improving payment conversion rates.""",
        model=api_schema.upi.JuspaySavedPaymentMethodsPayload,
        handler=upi.get_saved_payment_methods,
        response_schema=response_schema.saved_payment_methods_response_schema,
    ),
    util.make_api_config(
        name="upi_collect",
        description="Creates a UPI Collect transaction for requesting payment from a customer's UPI ID.",
        model=api_schema.upi.JuspayUpiCollectPayload,
        handler=upi.upi_collect,
        response_schema=response_schema.upi_collect_response_schema,
    ),
    util.make_api_config(
        name="verify_vpa",
        description="Verifies if a UPI Virtual Payment Address (VPA) is valid.",
        model=api_schema.upi.JuspayVerifyVpaPayload,
        handler=upi.verify_vpa,
        response_schema=response_schema.verify_vpa_response_schema,
    ),
    util.make_api_config(
        name="upi_intent",
        description="Creates a UPI Intent transaction for payment using UPI apps.",
        model=api_schema.upi.JuspayUpiIntentPayload,
        handler=upi.upi_intent,
        response_schema=response_schema.upi_intent_response_schema,
    ),
    util.make_api_config(
        name="list_offers_juspay",
        description="""API for listing the ACTIVE offers at a particular point in time based on the configurations in the offers operations dashboard.

Key features:
- Filters through complete set of merchant offers configured in the database.
- Provides offer description and terms for each offer.
- Shows offer eligibility for the current transaction.
- Details offer benefits with calculation rules (Discount/Cashback/EMI Discount Value).
- Returns order amount pre/post discount.
- Lists eligible payment instruments/methods for an offer.
- Includes eligible products along with offer breakup for each product.
- Supports optional coupon code parameter.

Use this tool to display available offers during checkout, validate coupon codes, calculate discount amounts, show offer eligibility based on payment methods, or provide personalized offer recommendations. Essential for implementing promotional campaigns and improving conversion rates.""",
        model=api_schema.offer.JuspayListOffersPayload,
        handler=offer.list_offers_juspay,
        response_schema=response_schema.list_offers_response_schema,
    ),
    util.make_api_config(
        name="get_offer_order_status_juspay",
        description="""Retrieves the complete status of an order along with detailed offer information using the `order_id`.

Key features:
- Returns comprehensive order status and details.
- Includes complete offer information with offer_id, offer_code, and status.
- Provides benefit details including type (DISCOUNT/CASHBACK), calculation rules, and amounts.
- Shows customer information (email, phone, customer_id).
- Includes payment details (payment method, card information, transaction details).
- Returns refund information if applicable.
- Provides payment gateway response details.
- Includes transaction UUID and gateway reference information.

Use this tool to verify order status with applied offers, check offer benefit calculations, retrieve complete transaction details including offers, validate offer application on completed orders, or provide detailed order information for customer support. Essential for offer reconciliation and order verification.""",
        model=api_schema.offer.JuspayOfferOrderStatusPayload,
        handler=offer.get_offer_order_status_juspay,
        response_schema=response_schema.offer_order_status_response_schema,
    ),
    util.make_api_config(
        name="list_wallets",
        description="""List all wallets for a customer using the `customer_id`. This API returns wallets which may or may not be linked.

Key features:
- Returns list of all wallets associated with a customer.
- Shows both linked and unlinked wallets.
- Provides wallet details including wallet name, token, and balance information.
- Includes last_refreshed timestamp indicating when balance was last updated.
- Returns sub_details array with payment method breakdown for each wallet.
- Shows current_balance for linked wallets (may not reflect real-time balance).
- Supports direct debit functionality for linked wallets if enabled by provider.

Use this tool to display available wallet payment options, check wallet balances before payment, retrieve linked wallet information for one-click payments, or show wallet payment methods during checkout. Essential for implementing wallet-based payments and managing customer wallet preferences.""",
        model=api_schema.wallet.ListWalletsPayload,
        handler=wallet.list_wallets,
        response_schema=response_schema.list_wallets_response_schema,
    ),
    util.make_api_config(
        name="create_order_juspay",
        description="Creates a new order in Juspay payment system.",
        model=api_schema.order.JuspayCreateOrderPayload,
        handler=order.create_order_juspay,
        response_schema=response_schema.create_order_response_schema,
    ),
    util.make_api_config(
        name="update_order_juspay",
        description="Updates an existing order in Juspay.",
        model=api_schema.order.JuspayUpdateOrderPayload,
        handler=order.update_order_juspay,
        response_schema=response_schema.update_order_response_schema,
    ),
]

@app.list_tools()
async def list_my_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=tool["name"],
            description=tool["description"],
            inputSchema=tool["schema"],
        )
        for tool in AVAILABLE_TOOLS
    ]

@app.call_tool()
async def handle_tool_calls(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info(f"Calling tool: {name} with args: {arguments}")
    try:
        # Import here to avoid circular imports
        from juspay_mcp.api.utils import set_juspay_credentials
        
        tool_entry = next((t for t in AVAILABLE_TOOLS if t["name"] == name), None)
        if not tool_entry:
            raise ValueError(f"Unknown tool: {name}")

        schema = tool_entry["schema"]
        required = schema.get("required", [])
        missing = [key for key in required if key not in arguments]
        if missing:
            raise ValueError(f"Missing required fields for {name}: {missing}")

        handler = tool_entry["handler"]
        if not handler:
            raise ValueError(f"No handler defined for tool: {name}")

        model_cls = tool_entry.get("model")
        if model_cls:
            try:
                payload = model_cls(**arguments)  
                payload_dict = payload.dict(exclude_none=True) 
            except Exception as e:
                raise ValueError(f"Validation error: {str(e)}")
        else:
            payload_dict = arguments 
        
        juspay_creds = get_juspay_request_credentials()
        if juspay_creds:
            logger.info("Using header credentials for Juspay API calls")
            set_juspay_credentials(juspay_creds)
        else:
            logger.info("No header credentials found, falling back to environment variables")
            set_juspay_credentials(None)

        meta_info = arguments.pop("juspay_meta_info", None)

        sig = inspect.signature(handler)
        param_count = len(sig.parameters)

        if param_count == 0:
            response = await handler()

        elif param_count == 1:
            if arguments or not meta_info:
                response = await handler(arguments)
            else:
                response = await handler(meta_info)

        elif param_count == 2:
            response = await handler(arguments, meta_info)

        else:
            raise ValueError(f"Unsupported number of parameters in tool handler: {param_count}")
        return [types.TextContent(type="text", text=json.dumps(response))]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"ERROR: Tool execution failed: {str(e)}")]
