# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import List, Literal, Union, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, RootModel, Field, ConfigDict, model_validator

#################################
#            Metrics            #
#################################

MetricEnum = Literal[
    "total_amount",
    "success_volume",
    "success_rate",
    "avg_ticket_size",
    "conflict_txn_rate",
    "average_latency",
    "order_with_transactions",
    "order_with_transactions_gmv",
]
Metric = Union[MetricEnum, List[MetricEnum]]

#################################
#            Dimensions          #
#################################


class Granularity(BaseModel):
    unit: Literal["second", "minute", "hour", "day", "week", "month"]
    duration: int = Field(..., ge=1)


class DimensionObject(BaseModel):
    granularity: Granularity
    intervalCol: Literal["order_created_at"]
    timeZone: Literal["Asia/Kolkata"]


DimensionString = Literal[
    "actual_order_status",
    "actual_payment_status",
    "allowed_requeue",
    "auth_type",
    "bank",
    "business_region",
    "card_bin",
    "card_brand",
    "card_exp_month",
    "card_exp_year",
    "card_issuer_country",
    "card_sub_type",
    "card_type",
    "consent_page",
    "currency",
    "emi",
    "emi_bank",
    "emi_tenure",
    "emi_type",
    "error_message",
    "gateway_reference_id",
    "industry",
    "is_business_retry",
    "is_cvv_less_txn",
    "is_offer_txn",
    "is_requeued_order",
    "is_retargeted_order",
    "is_retried_order",
    "is_technical_retry",
    "is_token_bin",
    "is_tokenized",
    "issuer_token_reference",
    "issuer_tokenization_consent_failure_reason",
    "juspay_bank_code",
    "juspay_error_message",
    "juspay_response_code",
    "juspay_response_message",
    "lob",
    "mandate_feature",
    "merchant_id",
    "ord_currency",
    "order_source_object",
    "order_source_object_id",
    "order_status",
    "order_type",
    "order_created_at",
    "original_card_isin",
    "os",
    "payment_flow",
    "payment_gateway",
    "payment_instrument_group",
    "payment_method_subtype",
    "payment_method_type",
    "payment_status",
    "platform",
    "prev_gateway_resp_code",
    "prev_gateway_resp_message",
    "prev_order_status",
    "prev_txn_status",
    "previous_gateway_resp_code",
    "previous_gateway_resp_message",
    "previous_order_status",
    "previous_txn_status",
    "priority_logic_tag",
    "requeue_count",
    "resp_code",
    "resp_message",
    "status_sync_source",
    "stored_card_vault_provider",
    "ticket_size",
    "token_reference",
    "token_repeat",
    "tokenization_consent",
    "tokenization_consent_failure_reason",
    "tokenization_consent_ui_presented",
    "tokenization_eligibility",
    "tokenized_flow",
    "txn_conflict",
    "txn_flow_type",
    "txn_latency_enum",
    "txn_object_type",
    "txn_source_object",
    "txn_type",
    "udf1",
    "udf10",
    "udf2",
    "udf3",
    "udf4",
    "udf5",
    "udf6",
    "udf7",
    "udf8",
    "udf9",
    "unified_response_category",
    "user_opt_in",
    "using_stored_card",
    "using_token",
    "is_upicc",
]

class DimensionList(RootModel[List[Union[DimensionString, DimensionObject]]]):
    pass


#################################
#            Interval            #
#################################


class Interval(BaseModel):
    """Time interval for queries with start and end times

    Both start and end are stored as strings to avoid JSON serialization issues
    """

    start: str  # format: "%Y-%m-%dT%H:%M:%SZ"
    end: str  # format: "%Y-%m-%dT%H:%M:%SZ"

    @classmethod
    def from_datetime(cls, start_dt: datetime, end_dt: datetime) -> "Interval":
        """Create an Interval from datetime objects"""
        return cls(
            start=start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end=end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )


#################################
#            Filters            #
#################################

FilterFieldDimensionEnum = DimensionString

FilterCondition = Literal[
    "In",
    "NotIn",
    "Greater",
    "GreaterThanEqual",
    "LessThanEqual",
    "Less",
]


class SortConfig(BaseModel):
    sortDimension: str
    ordering: Literal["Asc", "Desc"]


class ValObject(BaseModel):
    limit: int
    sortedOn: SortConfig


# ────────────────────────────────────────────────────────────────────────────────
#  1. Dimension‑specific “value literals”
# ────────────────────────────────────────────────────────────────────────────────
PaymentGatewayVal = Literal["PAYTM_V2", "PHONEPE", "RAZORPAY", "PAYU", "GOCASHFREE", "YES_BIZ", "CASH", "AXIS_BIZ", "BILLDESK", "EASEBUZZ", "CRED", "RBL_BIZ", "CYBERSOURCE", "ICICI_UPI", "SODEXO", "SIMPL", "TPSL", "AMAZONPAY", "PAYTM", "HSBC_UPI", "MOBIKWIK", "LAZYPAY", "CCAVENUE_V2", "YESBANK_UPI", "TWID", "MPGS", "HDFC_UPI", "PAYGLOCAL", "HDFC", "GPAY_IMF", "PINELABS", "PINELABS_ONLINE", "HDFCBANK_SMARTGATEWAY", "PAY10", "GYFTR", "WORLDPAY", "AMEX", "IPG", "HYPER_PG", "BOKU", "ZAAKPAY", "ATOM", "BHARATX", "NAVITAIRE", "DUMMY", "PAYFORT", "MERCHANT_CONTAINER", "NOON", "STRIPE", "INDUS_PAYU", "CHECKOUT", "CAMSPAY", "SNAPMINT", "IATAPAY", "TATA_PA", "PAYZAPP", "SHOPSE", "CAPITALFLOAT", "LSP", "HYPERPAY", "TATAPAY", "TATAPAYLATER", "LOTUSPAY", "LOANTAP", "GOOGLEPAY", "AXIS_UPI", "EPAYLATER", "SIKA_SIMPL", "AIRTELMONEY", "PAYPAL", "TWID_V2", "HYPERPG", "BAJAJFINSERV", "CAREEMPAY", "FREECHARGE", "SBI", "DIGIO", "HDFC_CC_EMI", "ICICINB", "ADYEN", "OLAPOSTPAID", "MIGS", "POSTPAY", "MORPHEUS", "ITZCASH", "HSBC", "EBS_V3", "QWIKCILVER", "TWOC_TWOP", "MOBIKWIKZIP", "JIOMONEY", "FAWRYPAY", "AIRWALLEX", "JIOPAY", "LSP_ETB", "FIB", "SBI_UPI", "PAYTM_UPI", "TAP", "AIRPAY", "MIDTRANS", "CITRUS", "CAPILLARY", "INDUS_UPI"]

TicketSizeVal = Literal['101-200', '201-300', '>1L', '1K-2K', '2K-5K', '0-100', '5K-10K', '501-1K', '10K-50K', '301-400', '401-500', '50K-1L']

ActualOrderStatusVal = Literal['COD_INITIATED', 'AUTHORIZED', 'AUTO_REFUNDED', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'CAPTURE_FAILED', 'AUTHORIZING', 'VOIDED', 'NEW', 'SUCCESS', 'PENDING_AUTHENTICATION', 'AUTHORIZATION_FAILED', 'PARTIAL_CHARGED', 'JUSPAY_DECLINED', 'TO_BE_CHARGED']

ActualPaymentStatusVal = Literal['COD_INITIATED', 'PENDING_VBV', 'AUTHORIZED', 'CHARGED', 'FAILURE', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'CAPTURE_FAILED', 'AUTHORIZING', 'VOIDED', 'AUTO_REFUNDED', 'VBV_SUCCESSFUL', 'AUTHORIZATION_FAILED', 'STARTED', 'JUSPAY_DECLINED', 'TO_BE_CHARGED']

AllowedRequeueVal = Literal[0]

AuthTypeVal = Literal['THREE_DS_2', 'THREE_DS', 'MOTO', 'OTP', 'THREE_DS2']

CardBrandVal = Literal['CHINAUNIONPAY', 'UNIONPAY', 'DISCOVER', 'RUPAY', 'MAESTRO', 'JCB', 'DINERS', 'MASTERCARD', 'AMEX', 'VISA', 'SODEXO', 'MADA', 'BAJAJ']

CardTypeVal = Literal['RTP', 'WALLET', 'OTC', 'REWARD', 'DEBIT', 'NB', 'AADHAAR', 'UPI', 'CREDIT', 'VIRTUAL_ACCOUNT']

EmiVal = Literal[False, True]

EmiTenureVal = Literal['12', '48', '36', '24', '6', '0', '3', '18', '9']

EmiTypeVal = Literal['JUSPAY_NO_COST_EMI', 'NO_COST_EMI', 'STANDARD_EMI', 'LOW_COST_EMI', 'JUSPAY_NO_COST_EMI_SPLIT']

IndustryVal = Literal['NBFC', 'Travel', 'Education', 'Food Delivery', 'Others', 'Hyperlocal', 'Billpay', 'EPharma', 'TravelOrStay', 'OTT', 'eCommerce', 'ERetail', 'Ticketing', 'Grocery Delivery', 'Telecom / D2H', 'Fintech', 'Ticket Booking', 'E-pharma', 'Telecom', 'Gaming', 'Classified', 'Investments', 'Insurance']

IsBusinessRetryVal = Literal[False, True]

IsCvvLessTxnVal = Literal[True]

IsOfferTxnVal = Literal[False, True]

IsRequeuedOrderVal = Literal[False, True]

IsRetargetedOrderVal = Literal[False, True]

IsRetriedOrderVal = Literal[False, True]

IsTechnicalRetryVal = Literal[False, True]

IsTokenBinVal = Literal['FALSE', 'TRUE']

IsTokenizedVal = Literal[False, True]

IssuerTokenReferenceVal = Literal[False, True]

MandateFeatureVal = Literal['DISABLED', 'OPTIONAL', 'REQUIRED']

OrderSourceObjectVal = Literal['PAYMENT_LINK', 'PAYMENT_FORM']

OrderSourceObjectIdVal = Literal['pf_e2c79ac0e4', '45ded11c587a4d67b50540ce476a5c7d', 'pf_6dd12b8acf', 'pf_f5fad4b9d2', 'DASHBOARD', 'pf_59866c9894', 'pf_5089b50928', 'pf_a61ccef16d', 'pf_4e821fe74a']

OrderStatusVal = Literal['FAILURE', 'SUCCESS', 'PENDING']

OrderTypeVal = Literal['MANDATE_PAYMENT', 'ORDER_PAYMENT', 'TPV_MANDATE_REGISTER', 'TPV_PAYMENT', 'MOTO_PAYMENT', 'VAN_PAYMENT', 'MANDATE_REGISTER', 'TPV_MANDATE_PAYMENT']

OsVal = Literal[0]

PaymentGatewayVal = Literal['INDUS_PAYU', 'EPAYLATER', 'GPAY_IMF', 'TWOC_TWOP', 'TATANEU', 'ATOM', 'MPGS', 'YES_BIZ', 'BOKU', 'PAYFORT', 'ADYEN', 'EBS_V3', 'HDFC', 'SODEXO', 'WORLDPAY', 'CITRUS', 'HYPER_PG', 'HYPERPAY', 'SHOPSE', 'MERCHANT_CONTAINER', 'SBI', 'YESBANK_UPI', 'TATAPAY', 'LOANTAP', 'HYPERPG', 'TWID', 'HDFC_UPI', 'PAYGLOCAL', 'RBL_BIZ', 'AXIS_UPI', 'CRED', 'HDFCBANK_SMARTGATEWAY', 'SIKA_SIMPL', 'AIRPAY', 'TABBY', 'BHARATX', 'SNAPMINT', 'LOTUSPAY', 'LINEPAY', 'MOBIKWIK', 'ITZCASH', 'CAPITALFLOAT', 'HDFC_CC_EMI', 'TWID_V2', 'STRIPE', 'DUMMY', 'EASEBUZZ', 'ICICINB', 'CAMSPAY', 'HSBC_UPI', 'PAYTM', 'YPP', 'CCAVENUE_V2', 'PAYZAPP', 'TATAPAYLATER', 'CYBERSOURCE', 'NOON', 'PAYU', 'CASH', 'PINELABS', 'PAY10', 'LAZYPAY', 'GOCASHFREE', 'FREECHARGE', 'AIRTELMONEY', 'XENDIT', 'PAYPAL', 'RAZORPAY', 'IPG', 'FAWRYPAY', 'PHONEPE', 'TPSL', 'GOOGLEPAY', 'ZAAKPAY', 'ICICI_UPI', 'CAREEMPAY', 'AMAZONPAY', 'LSP', 'BAJAJFINSERV', 'NAVITAIRE', 'CHECKOUT', 'KBANK', 'DIGIO', 'MORPHEUS', 'IATAPAY', 'AMEX', 'BILLDESK', 'PAYTM_V2', 'TATA_PA', 'HDFCNB', 'AIRWALLEX', 'AXIS_BIZ', 'SIMPL', 'PINELABS_ONLINE']

PaymentInstrumentGroupVal = Literal['CREDIT CARD', 'RTP', 'WALLET', 'OTC', 'REWARD', 'NET BANKING', 'CASH', 'AADHAAR', 'DEBIT CARD', 'UPI', 'VIRTUAL_ACCOUNT']

PaymentMethodSubtypeVal = Literal['TOKENIZATION_CONSENT_FALLBACK_TO_THREE_DS', 'VAN_NB', 'UPI_INAPP', 'CRED_INTENT', 'PG_FAILURE_FALLBACK_TO_THREE_DS', 'PUSH_PAY', 'AUTH_PROVIDER_FALLBACK_TO_THREE_DS', 'UPI_PAY', 'TXN_SUB_DETAIL', 'DECIDER_FALLBACK_TO_THREE_DS', 'UPI_COLLECT', 'DIRECT_WALLET_DEBIT', 'CUSTOMER_FALLBACK_TO_THREE_DS', 'CRED_COLLECT', 'MANDATE', 'REDIRECT_WALLET_DEBIT', 'PAYMENT_CHANNEL_FALLBACK_TO_THREE_DS', 'UPI_QR']

PaymentMethodTypeVal = Literal['RTP', 'WALLET', 'CARD', 'OTC', 'REWARD', 'NB', 'CASH', 'AADHAAR', 'CONSUMER_FINANCE', 'MERCHANT_CONTAINER', 'UPI', 'VIRTUAL_ACCOUNT']

PaymentStatusVal = Literal['FAILURE', 'SUCCESS', 'PENDING']

PlatformVal = Literal['ANDROID', 'WEB:unknown', 'MOBILE_WEB', 'WEB', 'IOS']

PrevOrderStatusVal = Literal['AUTHORIZED', 'AUTO_REFUNDED', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'SUCCESS', 'AUTHORIZING', 'PENDING_AUTHENTICATION', 'AUTHORIZATION_FAILED', 'JUSPAY_DECLINED']

PrevTxnStatusVal = Literal['PENDING_VBV', 'AUTHORIZED', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'VOID_INITIATED', 'AUTHORIZING', 'VBV_SUCCESSFUL', 'AUTHORIZATION_FAILED', 'STARTED', 'PENDING']

PreviousOrderStatusVal = Literal['AUTHORIZED', 'AUTO_REFUNDED', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'SUCCESS', 'AUTHORIZING', 'PENDING_AUTHENTICATION', 'AUTHORIZATION_FAILED', 'JUSPAY_DECLINED']

PreviousTxnStatusVal = Literal['PENDING_VBV', 'AUTHORIZED', 'AUTHENTICATION_FAILED', 'CAPTURE_INITIATED', 'VOID_INITIATED', 'AUTHORIZING', 'VBV_SUCCESSFUL', 'AUTHORIZATION_FAILED', 'STARTED', 'PENDING']

StatusSyncSourceVal = Literal['TRANSACTION', 'SN_FORCE_SYNC_V1', 'START_PAY', 'CRON_SYNC', 'REDIRECTION', 'PT_SYNC', 'ASN_FORCE_SYNC_V1', 'WEBHOOKS']

StoredCardVaultProviderVal = Literal['ALT_ID', 'ISSUER_CARD', 'ISSUER_TOKEN', 'NETWORK_TOKEN', 'SODEXO']

TicketSizeVal = Literal['101-200', '201-300', '>1L', '1K-2K', '2K-5K', '0-100', '5K-10K', '501-1K', '10K-50K', '301-400', '401-500', '50K-1L']

TokenRepeatVal = Literal['FALSE', 'TRUE']

TokenizationConsentVal = Literal[False, True]

TokenizationConsentUiPresentedVal = Literal[False, True]

TokenizationEligibilityVal = Literal['Eligible', 'NotEligible']

TokenizedFlowVal = Literal[False, True]

TxnConflictVal = Literal['RESOLVED', 'CONFLICTED', 'MATCH']

TxnFlowTypeVal = Literal['QR', 'DIRECT_DEBIT', 'NET_BANKING', 'NATIVE', 'CARD_TRANSACTION', 'INAPP_DEBIT', 'COLLECT', 'AADHAAR_PAY', 'REDIRECT_DEBIT', 'EMI', 'CASH_PAY', 'INTENT']

TxnLatencyEnumVal = Literal['10M-1H', '1H-1D', '5M-6M', '9M-10M', '1M-2M', '1D-3D', '8M-9M', '4M-5M', '7M-8M', '3D-7D', '6M-7M', '3M-4M', '2M-3M', '0M-1M']

TxnObjectTypeVal = Literal['MANDATE_PAYMENT', 'ORDER_PAYMENT', 'TPV_EMANDATE_PAYMENT', 'EMANDATE_REGISTER', 'TPV_PAYMENT', 'VAN_PAYMENT', 'MANDATE_REGISTER', 'EMANDATE_PAYMENT', 'TPV_EMANDATE_REGISTER', 'PARTIAL_CAPTURE']

TxnSourceObjectVal = Literal['TOKENIZATION_CONSENT_FALLBACK_TO_THREE_DS', 'VAN_NB', 'UPI_INAPP', 'CRED_INTENT', 'PG_FAILURE_FALLBACK_TO_THREE_DS', 'PUSH_PAY', 'AUTH_PROVIDER_FALLBACK_TO_THREE_DS', 'UPI_PAY', 'TXN_SUB_DETAIL', 'DECIDER_FALLBACK_TO_THREE_DS', 'UPI_COLLECT', 'DIRECT_WALLET_DEBIT', 'CUSTOMER_FALLBACK_TO_THREE_DS', 'CRED_COLLECT', 'MANDATE', 'REDIRECT_WALLET_DEBIT', 'PAYMENT_CHANNEL_FALLBACK_TO_THREE_DS', 'UPI_QR']

TxnTypeVal = Literal['AUTH_AND_SETTLE', 'PREAUTH_AND_SETTLE', 'AUTH_AND_SPLIT_SETTLE']

UnifiedResponseCategoryVal = Literal['', 'USER_ERROR', 'GENERIC_ERROR', 'GATEWAY_VALIDATION_ERROR', 'BUSINESS_ERROR', 'VALIDATION_ERROR', 'PAYMENT_FAILURE', 'NOT_FOUND', 'TECHNICAL_ERROR', 'USER_DROPPED', 'GATEWAY_ERROR', 'UNKNOWN', 'TXN_PENDING']

UserOptInVal = Literal['Consent Page Not Shown', 'Skipped', 'Approved']

UsingStoredCardVal = Literal[False, True]

UsingTokenVal = Literal['True', 'False']

IsUpiccVal = Literal[False, True]

# ────────────────────────────────────────────────────────────────────────────────
#  2. Enum‑aware filter classes
# ────────────────────────────────────────────────────────────────────────────────
class _EnumFilterBase(BaseModel):
    condition: FilterCondition

    class Config:
        populate_by_name = True  # keeps aliases working


class PaymentGatewayFilter(_EnumFilterBase):
    field: Literal["payment_gateway"]
    val: Union[PaymentGatewayVal, List[PaymentGatewayVal], ValObject]


class TicketSizeFilter(_EnumFilterBase):
    field: Literal["ticket_size"]
    val: Union[TicketSizeVal, List[TicketSizeVal], ValObject]


class ActualOrderStatusFilter(_EnumFilterBase):
    field: Literal["actual_order_status"]
    val: Union[ActualOrderStatusVal, List[ActualOrderStatusVal], ValObject]


class ActualPaymentStatusFilter(_EnumFilterBase):
    field: Literal["actual_payment_status"]
    val: Union[ActualPaymentStatusVal, List[ActualPaymentStatusVal], ValObject]


class AuthTypeFilter(_EnumFilterBase):
    field: Literal["auth_type"]
    val: Union[AuthTypeVal, List[AuthTypeVal], ValObject]


class CardBrandFilter(_EnumFilterBase):
    field: Literal["card_brand"]
    val: Union[CardBrandVal, List[CardBrandVal], ValObject]


class PaymentMethodTypeFilter(_EnumFilterBase):
    field: Literal["payment_method_type"]
    val: Union[PaymentMethodTypeVal, List[PaymentMethodTypeVal], ValObject]


class PaymentMethodSubtypeFilter(_EnumFilterBase):
    field: Literal["payment_method_subtype"]
    val: Union[PaymentMethodSubtypeVal, List[PaymentMethodSubtypeVal], ValObject]


class PaymentInstrumentGroupFilter(_EnumFilterBase):
    field: Literal["payment_instrument_group"]
    val: Union[PaymentInstrumentGroupVal, List[PaymentInstrumentGroupVal], ValObject]


class IsUpiccFilter(_EnumFilterBase):
    field: Literal["is_upicc"]
    val: Union[IsUpiccVal, List[IsUpiccVal], ValObject]


# ────────────────────────────────────────────────────────────────────────────────
#  3. Generic catch‑all filter for everything else
# ────────────────────────────────────────────────────────────────────────────────
class FieldFilter(BaseModel):
    field: FilterFieldDimensionEnum
    condition: FilterCondition
    val: Union[str, bool, float, None, List[Union[str, None, bool]], ValObject]


# ────────────────────────────────────────────────────────────────────────────────
#  4. Combined / And / Or filters (unchanged from your original code)
# ────────────────────────────────────────────────────────────────────────────────
class CombinedFilter(BaseModel):
    left: "Filter"  # forward ref
    right: "Filter"  # forward ref


class AndFilter(BaseModel):
    and_: CombinedFilter = Field(..., alias="and")

    class Config:
        populate_by_name = True


class OrFilter(BaseModel):
    or_: CombinedFilter = Field(..., alias="or")

    class Config:
        populate_by_name = True


# ────────────────────────────────────────────────────────────────────────────────
#  5. Master union that the rest of the codebase references
# ────────────────────────────────────────────────────────────────────────────────
Filter = Union[
    PaymentGatewayFilter,
    TicketSizeFilter,
    ActualOrderStatusFilter,
    ActualPaymentStatusFilter,
    AuthTypeFilter,
    CardBrandFilter,
    PaymentMethodTypeFilter,
    PaymentMethodSubtypeFilter,
    PaymentInstrumentGroupFilter,
    IsUpiccFilter,
    FieldFilter,
    AndFilter,
    OrFilter,
]

# ────────────────────────────────────────────────────────────────────────────────
#  6. Resolve forward references so Pydantic is happy
# ────────────────────────────────────────────────────────────────────────────────
CombinedFilter.model_rebuild()
AndFilter.model_rebuild()
OrFilter.model_rebuild()

#################################
#            sortedOn           #
#################################


class SortedOn(BaseModel):
    sortDimension: MetricEnum
    ordering: Literal["Asc", "Desc"]


#################################
#         Response Type         #
#################################
# Success row: allows arbitrary keys (metrics/dimensions) with primitive values
class QApiSuccessRow(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "additionalProperties": {"type": ["string", "number", "boolean", "null"]},
            "propertyNames": {
                "enum": list(set(MetricEnum.__args__) | set(DimensionString.__args__))
            },
        },
    )


# Success response = list of rows
class QApiSuccessResponse(RootModel[List[QApiSuccessRow]]):
    pass


# Error response
class QApiErrorResponse(BaseModel):
    error: str
    payload_attempted: Dict[str, Any]


QApiResponse = Union[QApiSuccessResponse, QApiErrorResponse]

#################################
#      QApiCompare Types        #
#################################


class QApiCompareResponse(BaseModel):
    """Response type for the qapi_compare tool"""

    responses: List[QApiResponse]
    payloads: List[Dict[str, Any]]


#################################
#        QApiPayload Type       #
#################################


class QApiPayload(BaseModel):
    """Pydantic model for the Q API payload"""

    domain: Literal["kvorders"] = "kvorders"
    metric: Metric
    interval: Interval
    filters: Optional[Filter] = None
    dimensions: DimensionList = []
    sortedOn: Optional[SortedOn] = None

class ToolQApiPayload(BaseModel):
    """Pydantic model for the Tool Interface Q API payload"""

    metric: Metric
    interval: Interval
    filters: Optional[Filter] = None
    dimensions: DimensionList = []
    sortedOn: Optional[SortedOn] = None



########################################################
#        High cardinality search tool types            #
########################################################

# These are the *only* dimensions considered “high cardinality” for now.
HighCardinalityDimension = Literal["bank", "error_message"]

# These are the "low cardinality" dimensions for now.
LowCardinalityDimension = Literal[
    "actual_order_status",
    "actual_payment_status", 
    "allowed_requeue",
    "auth_type",
    "card_brand",
    "card_type",
    "emi",
    "emi_tenure",
    "emi_type",
    "gateway",
    "industry",
    "is_business_retry",
    "is_cvv_less_txn",
    "is_offer_txn",
    "is_requeued_order",
    "is_retargeted_order",
    "is_retried_order",
    "is_technical_retry",
    "is_token_bin",
    "is_tokenized",
    "issuer_token_reference",
    "mandate_feature",
    "order_source_object",
    "order_source_object_id",
    "order_status",
    "order_type",
    "os",
    "payment_gateway",
    "payment_instrument_group",
    "payment_method_subtype",
    "payment_method_type",
    "payment_status",
    "platform",
    "prev_order_status",
    "prev_txn_status",
    "previous_order_status",
    "previous_txn_status",
    "status_sync_source",
    "stored_card_vault_provider",
    "ticket_size",
    "token_repeat",
    "tokenization_consent",
    "tokenization_consent_ui_presented",
    "tokenization_eligibility",
    "tokenized_flow",
    "txn_conflict",
    "txn_flow_type",
    "txn_latency_enum",
    "txn_object_type",
    "txn_source_object",
    "txn_type",
    "unified_response_category",
    "user_opt_in",
    "using_stored_card",
    "using_token",
    "is_upicc",
]

# Response type returned by the search_high_cardinality_field_values tool
class HighCardinalityValues(RootModel[List[str]]):
    pass

# --- Unified batch field-value discovery tool types ---
class DimensionLookupRequest(BaseModel):
    """
    Request for field-value discovery for a single dimension.
    - dimension: The dimension to look up values for.
    - queries: List of fuzzy search queries. If empty, returns first N values.
    - max_results: Optional override for number of results per query.
    """
    dimension: Union[HighCardinalityDimension, LowCardinalityDimension]
    queries: List[str]
    max_results: Optional[int] = None

class DimensionLookupResult(BaseModel):
    """
    Result for a single dimension lookup.
    - dimension: The dimension name.
    - results: List of lists of strings. Each inner list corresponds to a query in the request.
    """
    dimension: Union[HighCardinalityDimension, LowCardinalityDimension]
    results: List[List[str]]

class FieldLookupBatchResponse(RootModel[List[DimensionLookupResult]]):
    """
    Batch response mapping each dimension to its query results.
    """
    pass


api_description = """
    Calls an internal /q analytics API with the provided analytics payload. 
    REMEMBER! try to apply all required the filters, dimensions, etc. in least amount of function tool calls.
    CAN do more calls if all the filters, dimensions, etc. in the query's context are not possible in a single call.

    USEFUL SYNONYMS:
      Revenue = Processed amount = GMV = total_amount (successful orders only)
      Netbanking, NB
      BNPL, Pay Later
      EMI, Instalments
      THREE_DS , 3DS
      THREE_DS_2, 3DS
      UPI QR, QR , Scan n Pay
      UPI COLLECT , COLLECT
      Wallets, Prepaid Instrument , PPI
      Network, Card Brand, Brand, Card network
      UPI INTENT , INTENT , PAY, Pay using App, UPI_PAY
      Payment Gateway, Gateway , Aggregator, PG
      Auto Pay, Mandate, subscriptions, recurring payment
      Payment Instrument, Payment Instrument Group, Payment Containers
      Success rate, Conversion rate , SR, S.R , Payment SR , Order SR , Order Success Rate
    
    Args:
        filters: A dict representing the 'filters' section with valid field values from the schema.
                IMPORTANT NOTES:
                  - Using "limit" in Filters:
                    -> If query asks to *list* or *give* or *show* the possible values/enums of a "dimension", then **always** apply a limit = 10 for limiting the number of rows.
                    -> Add `limit` in the filter when the query requests to limit the number of rows by otuput, i.e., "top 'n'..." in the user query means apply limit as 'n'. However if user is just asking for top, then assume limit as 1 (VERY IMPORTANT) 
                    -> For example, the query: _"Give me a breakdown of the transaction volume by payment method for the top error message"_ or _"Give me the top error message yesterday"_ requires filtering for the top error message while providing the breakdown by payment method. In such cases:
                    -> if anywhere in the query "top 3", "top 2", "top", etc are present, ALWAYS APPLY `limit` in "filter". 
                    -> Use `limit` to restrict the filter to the top error message, e.g.,:
                  ```json
                     # Example filter for top error message 
                        {
                            "filters": {
                            "and": {
                                "left": {
                                "condition": "In",
                                "field": "error_message",
                                "val": {
                                    "sortedOn": {
                                    "sortDimension": "order_with_transactions",
                                    "ordering": "Desc"
                                    },
                                    "limit": Int
                                }
                                },
                                "right": {
                                "condition": "NotIn",
                                "field": "error_message",          
                                "val": [null]
                                }
                            }
                            }
                        }                     
                  ```
                 - ALWAYS add a filter to exclude null values when querying for top values of any dimension/field. This ensures that null values don't appear in the top results. For example, when asked for "top payment gateways", always include a filter like `"condition": "NotIn", "field": "payment_gateway", "val": [null]` in combination with the limit filter. _MAKE SURE TO ALWAYS FILTER OUT NULL VALUES NOT EMPTY STRING ""_
                 - Consider Conversational Context: Carefully examine if the current user query is a continuation or refinement of a previous query within the ongoing conversation. If the current query lacks specific filter details but appears to build upon earlier messages, actively infer the necessary filters from the established conversational context. For example, if the user first asks "What is the SR for Razorpay?" and then follows up with "Break it down by card type", the second query implicitly requires the `payment_gateway` filter for "RAZORPAY" from the first query.
                 - Use payment_instrument_group, payment_method_subtype, payment_method_type to find out type of payment instrument used For eg. credit card, debit card, upi, etc..
                 - You are not allowed to use any field apart from the provided possible enum values in the JSON schema.
                 - Never use `run_day_ist` and `run_hour_ist` in `sortDimension`.
                 - Do not return an empty filter object.
                 - After generating the filter, check each key and match it with the allowed JSON schema. Do not return filters outside of the JSON schema.
                 - Return only the JSON filter in the output; do not return any other text apart from the generated filter.
                 - If the query asks details about a specific merchant, add the filter for merchant_id. (Note: merchant_id should be lowercase and without spaces)
                 - If the query specifies EMI transactions, always set filter for emi_bank to be not null!
                 - To filter transactions for a specific card type (Credit Card/Debit Card) filter on "payment_instrument_group"!
                 - NOTE: For handling queries regarding payments through UPI apps, set payment_method_subtype filter on UPI_PAY. UPI App name is stored in the "bank" field/dimension. 
                 - When asked about payments through UPI handle/VPA/UPI ID/UPI Address (eg. @icici, @okicici, @okhdfcbank, @ptyes), set payment_method_subtype filter on UPI_COLLECT. UPI handle is stored in "bank" field. (example - 'paytm handle' in the query refers to "Paytm" in the "bank" fieldDimensionEnum and set payment_method_subtype filter on UPI_COLLECT)
                 - When asked about transactions going through a specific wallet, set payment_method_type filter on WALLET and the wallet name is stored in "bank" field.
                 - NOTE: When asked to filter on order success/failure, always use "payment_status" in dimensions or filter fields. If the user wants more fine grained filtering then use actual_payment_status otherwise always default to "payment_status". Supported values for payment_status: ["SUCCESS", "FAILURE", "PENDING"]
                 - NOTE: When asked for upi credit card transactions, NEVER `payment_instrument_group` = `CREDIT CARD`, always use `is_upicc` = `true`!!!
                 - You should not generate filters for time intervals! Time intervals are handled by interval section of the payload, not filters! NEVER FILTER ON `run_day_ist`, `run_week_ist`, `run_hour_ist`, etc. THIS IS THE MOST IMPORTANT INSTRUCTION
                 - When calculating the success rate, do not apply a filter for payment_status: SUCCESS. The success rate is a metric that should be handled by another component of the system. Avoid adding any filters specifically for success rate calculations. However, you may apply filters for other parts of the query as needed. For example, for a query like "Can you provide the success rate for Visa cards segmented by payment gateway?", the filter should include only "card_brand" in ["VISA"] and not "payment_status" in ["SUCCESS"]. Remember this important instruction!
                 - When asked about payment failure reason, refer to the error_message field.
        metric: A string or list of strings representing metric(s) to be queried. 
            [
              "total_amount", // total amount (in amount value) of success orders ONLY, ALSO KNOWN AS GMV or Processed Amount (Successful orders only)
              "success_volume", // total number of success orders (Total number of orders against which a transaction has been attempted by the customer and any one of the transactions was successful)
              "success_rate", // total number of success orders / total number of orders
              // Use "total_amount" only for successful transactions. If the query doesn't specify success explicitly, still assume success and choose "total_amount".
              "avg_ticket_size", // total ticket amount of success orders / total number of success orders
              "conflict_txn_rate", // total number of conflict orders / total number of orders (Dont use it unless explicitly asked about conflicted orders/transactions, NEVER use it to identify failed transactions/error message filter)
              "average_latency", // total latency of success orders / total number of success orders
              "order_with_transactions", // total number of orders against which at least one transaction has been attempted by the customer (includes 'success + pending + failure').
              "order_with_transactions_gmv" // equivalent to total amount of ALL orders (success+failed+pending+created+others). Use this explicitly ONLY if the user clearly asks for "all orders", "total value of orders", or similar phrases.
            ]
               IMPORTANT NOTES:
                 - Important distinctions regarding "total amount"
                   -> `total_amount` represents the 'total amount of successful orders only' (also known as 'GMV' or 'Processed Amount').
                   -> `order_with_transactions_gmv` represents 'the total amount across ALL orders' (including 'failed, pending, and created' orders). Do not use this for GMV calculations.
                 - Consider Conversational Context: Carefully examine if the current user query is a continuation or refinement of a previous query within the ongoing conversation. If the current query lacks specific details about metrics, dimensions, or sorting, but appears to build upon earlier messages, actively infer these details from the established conversational context. For example, if the user first asks "What is the SR and volume for Razorpay?" and then follows up with "Show me the daily trend", the second query implicitly requires the `metric` for "SR and volume" from the first query, while adding the time dimension for the daily trend.
        dimensions: A list of dimension strings or dimension objects, default empty list
            [
              "actual_order_status",
              "actual_payment_status",
              "allowed_requeue",
              "auth_type",
              "bank",
              "business_region",
              "card_bin",
              "card_brand",
              "card_exp_month",
              "card_exp_year",
              "card_issuer_country",
              "card_sub_type",
              "card_type",
              "consent_page",
              "currency",
              "emi",
              "emi_bank",
              "emi_tenure",
              "emi_type",
              "error_message",
              "gateway",
              "gateway_reference_id",
              "industry",
              "is_business_retry",
              "is_cvv_less_txn",
              "is_offer_txn",
              "is_requeued_order",
              "is_retargeted_order",
              "is_retried_order",
              "is_technical_retry",
              "is_token_bin",
              "is_tokenized",
              "issuer_token_reference",
              "issuer_tokenization_consent_failure_reason",
              "juspay_bank_code",
              "juspay_error_message",
              "juspay_response_code",
              "juspay_response_message",
              "lob",
              "mandate_feature",
              "merchant_id",
              "ord_currency",
              "order_source_object",
              "order_source_object_id",
              "order_status",
              "order_type",
              "order_created_at",
              "original_card_isin",
              "os",
              "payment_flow",
              "payment_gateway",
              "payment_instrument_group",
              "payment_method_subtype",
              "payment_method_type",
              "payment_status",
              "platform",
              "prev_gateway_resp_code",
              "prev_gateway_resp_message",
              "prev_order_status",
              "prev_txn_status",
              "previous_gateway_resp_code",
              "previous_gateway_resp_message",
              "previous_order_status",
              "previous_txn_status",
              "priority_logic_tag",
              "requeue_count",
              "resp_code",
              "resp_message",
              "status_sync_source",
              "stored_card_vault_provider",
              "ticket_size",
              "token_reference",
              "token_repeat",
              "tokenization_consent",
              "tokenization_consent_failure_reason",
              "tokenization_consent_ui_presented",
              "tokenization_eligibility",
              "tokenized_flow",
              "txn_conflict",
              "txn_flow_type",
              "txn_latency_enum",
              "txn_object_type",
              "txn_source_object",
              "txn_type",
              "udf1",
              "udf10",
              "udf2",
              "udf3",
              "udf4",
              "udf5",
              "udf6",
              "udf7",
              "udf8",
              "udf9",
              "unified_response_category",
              "user_opt_in",
              "using_stored_card",
              "using_token",
              "is_upicc",
            ]
                    IMPORTANT NOTES:
                      - Critical Instruction: When the query asks for 'absolute values' (e.g., "How many?", "Number of?", "Total Number?", "What is?", "Top X?"), do not include `granularity`, `intervalCol`, or `timeZone` in the `dimensions`. Only include these when the query asks for a 'trend over time' (e.g., "Show me the daily trend of...", "How has X changed over time", "Trend of...", "Over time", "Per day", "Per hour"). **If the user explicitly asks for a "graph" or "chart", always treat it as a trend query and include granularity.** **This is the most important instruction.**

                      - Default Time Range: If no time range is specified in the query, use the default time range, which is '12:00 AM of the current day to the current timestamp'. In such cases, use a 'granularity' of `"hour"` instead of `"day"`. This ensures trends are broken down into hourly intervals when no specific time range is given.
                      - Time-Based Columns: Only use `order_created_at` as a value for `intervalCol`.
                      - Using Limit for Top Values: Add `"limit": 1` only when the query explicitly asks for the **single top value** of a dimension or metric, and the expected output from the analytics API is just 'one row'.
                        -> For example, in the query: _"What is the top error message yesterday based on transaction volume?"_, the response should include `"limit": 1` because only the single top error message is requested, also you have to use sortedOn to make sure you're getting the top error message.

                      - Specific Dimensions:
                        -> To view specific card types (Credit Card/Debit Card) for transactions, use `"payment_instrument_group"` as a dimension.
                        -> To get payment volume, use `"order_with_transactions"` instead of `total_volume`.
                        -> UPI apps are stored in the `"bank"` dimension.
        interval: A dict with 'start' and 'end' keys (ISO format: YYYY-MM-DDTHH:MM:SSZ).
                 IMPORTANT NOTES:
                   - If user doesn't explicitly mention the interval, assume interval to be 12am of the same day to current time. INTERVAL IS MANDATORY.
        sortedOn: (Optional) A dict specifying how to sort the results, if needed.
                 IMPORTANT NOTES:
                   - **For any query that will return more than one row** (i.e. whenever `dimensions` is non-empty and you’re not explicitly limiting to a single result), you **must** include a top-level `sortedOn` object _outside_ of `filters`:
                       ```json
                       "sortedOn": {
                         "sortDimension": "<primary_metric>",
                         "ordering": "Desc"
                       }
                       ```
                       -> Use the first metric in your `metric` list as the `sortDimension` (or choose the metric most relevant to the user’s request, e.g. `success_rate` if present).  
                       -> Always set `"ordering": "Desc"`.  
                   - If you also use a `"limit"` inside `filters` (for a top-N within a breakdown), **still** keep the top-level `sortedOn` outside `filters`.
                  

    Returns:
        A dictionary containing the API response from /q endpoint.
    
    Example:
        Basic success rate query:
        {
            "filters": {
            "field": "payment_gateway",
            "condition": "In",
            "val": ["RAZORPAY"]
            },
            "metric": "success_rate",
            "dimensions": ["payment_method_type"],
            "interval": {
            "start": "2024-03-01T00:00:00Z",
            "end": "2024-03-21T23:59:59Z"
            }
        }
    """
