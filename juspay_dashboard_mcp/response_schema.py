# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

alert_details_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "task_type": {"type": "string"},
            "source_table": {"type": "string"},
            "metrics": {"type": "array", "items": {"type": "string"}},
            "query_duration": {"type": "integer"},
            "timezone_region": {"type": "string"},
            "task_channel": {"type": "array", "items": {"type": "string"}},
            "interval": {"type": "integer"},
            "status": {"type": "string"},
            "user_name": {"type": "string"},
            "task_description": {"type": "string"},
            "email": {"type": "array", "items": {"type": "string"}},
            "alert_mode": {"type": "string"},
            "schedule_time": {"type": "string"},
            "task_name": {"type": "string"},
            "is_password_protected": {"type": "boolean"},
            "dimensions": {"type": "array", "items": {"type": "string"}},
            "task_uid": {"type": "string"},
            "standard_report_type": {"type": "string"},
            "is_subscribed": {"type": "boolean"},
            "schedule_day_date": {"type": "string"},
            "merchant_id": {"type": "string"},
            "filters": {"type": "object"},
            "task_start_date": {"type": "string"},
            "signum": {"type": "array", "items": {"type": "string"}},
            "threshold": {"type": "array", "items": {"type": "string"}}
        },
        "required": [
            "task_type", "source_table", "metrics", "query_duration", "timezone_region",
            "task_channel", "interval", "status", "user_name", "task_description", "email",
            "alert_mode", "schedule_time", "task_name", "is_password_protected", "dimensions",
            "task_uid", "standard_report_type", "is_subscribed", "schedule_day_date",
            "merchant_id", "filters", "task_start_date", "signum", "threshold"
        ]
    }
}

list_alerts_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "task_type": {"type": "string"},
            "source_table": {"type": "string"},
            "metrics": {"type": "array", "items": {"type": "string"}},
            "query_duration": {"type": "integer"},
            "timezone_region": {"type": "string"},
            "task_channel": {"type": "array", "items": {"type": "string"}},
            "interval": {"type": "integer"},
            "status": {"type": "string"},
            "user_name": {"type": "string"},
            "task_description": {"type": "string"},
            "email": {"type": "array", "items": {"type": "string"}},
            "alert_mode": {"type": "string"},
            "schedule_time": {"type": "string"},
            "task_name": {"type": "string"},
            "is_password_protected": {"type": "boolean"},
            "dimensions": {"type": "array", "items": {"type": "string"}},
            "task_uid": {"type": "string"},
            "standard_report_type": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "is_subscribed": {"type": "boolean"},
            "schedule_day_date": {"type": "string"},
            "merchant_id": {"type": "string"},
            "filters": {"type": "object"},
            "task_start_date": {"type": "string"},
            "signum": {"type": "array", "items": {"type": "string"}},
            "threshold": {"type": "array", "items": {"type": "string"}}
        },
        "required": [
            "task_type", "source_table", "metrics", "query_duration", "timezone_region",
            "task_channel", "interval", "status", "user_name", "task_description", "email",
            "alert_mode", "schedule_time", "task_name", "is_password_protected", "dimensions",
            "task_uid", "standard_report_type", "schedule_day_date",
            "merchant_id", "filters", "task_start_date", "signum", "threshold"
        ]
    }
}

list_configured_gateways_response_schema = {
    "type": "object",
    "properties": {
        "list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "merchantId": {"type": "string"},
                    "enforcePaymentMethodAcceptance": {"type": "boolean"},
                    "disabledAt": {"type": "string"},
                    "supportedPaymentFlows": {"type": "string"},
                    "disabled": {"type": "boolean"},
                    "gateway": {"type": "string"},
                    "accountDetails": {"type": "string"},
                    "disabledBy": {"type": "string"},
                    "paymentMethods": {"type": "string"},
                    "supportedCurrencies": {"type": "string"},
                    "version": {"type": "integer"},
                    "testMode": {"type": "boolean"},
                    "id": {"type": "integer"},
                    "lastModified": {"type": "string"},
                    "isJuspayAccount": {"type": "boolean"},
                    "dateCreated": {"type": "string"},
                    "referenceId": {"type": "string"}
                },
                "required": [
                    "merchantId",
                    "enforcePaymentMethodAcceptance",
                    "supportedPaymentFlows",
                    "disabled",
                    "gateway",
                    "accountDetails",
                    "paymentMethods",
                    "version",
                    "testMode",
                    "id",
                    "lastModified"
                ]
            }
        },
        "offset": {"type": "integer"},
        "count": {"type": "integer"},
        "total": {"type": "integer"},
        "object": {"type": "string"}
    },
    "required": ["list", "offset", "count", "total", "object"]
}

get_gateway_scheme_response_schema = {
    "type": "object",
    "properties": {
        "masterAccountDetail": {
            "type": "array",
            "items": {"type": "object"}
        },
        "emandateAndTPVBanks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paymentMethodType": {"type": "string"},
                    "disabled": {"type": "boolean"},
                    "validationType": {"type": "string"},
                    "gatewayCardInfoId": {"type": "string"},
                    "bankName": {"type": "string"},
                    "emandateRegisterMaxAmount": {"type": "number"},
                    "isTokenized": {"type": "boolean"},
                    "gpmfId": {"type": "string"}
                },
                "required": [
                    "paymentMethodType",
                    "disabled",
                    "validationType",
                    "gatewayCardInfoId",
                    "bankName"
                ]
            }
        },
        "dotpEnableFlag": {"type": "boolean"},
        "accessControlAllowed": {"type": "boolean"},
        "paymentMethods": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "supportedCurrencies": {"type": "string"},
                    "juspayBankCodeId": {"type": "integer"},
                    "displayName": {"type": "string"},
                    "id": {"type": "integer"},
                    "nickName": {"type": "string"},
                    "type": {"type": "string"},
                    "dsl": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": [
                    "name", "supportedCurrencies", "displayName", "id", "nickName", "type", "description"
                ]
            }
        },
        "scheme": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "uiType": {"type": "string"},
                    "isEditable": {"type": "boolean"},
                    "lastUpdated": {"type": "string"},
                    "isMandatory": {"type": "boolean"},
                    "gateway": {"type": "string"},
                    "dbType": {"type": "string"},
                    "dateCreated": {"type": "string"},
                    "isMaskable": {"type": "boolean"},
                    "name": {"type": "string"},
                    "scheme": {"type": "string"},
                    "id": {"type": "integer"},
                    "fieldScope": {"type": "string"},
                    "title": {"type": "string"},
                    "defaultValue": {"type": "string"},
                    "instrumentScope": {"type": "string"},
                    "supportedPMT": {"type": "string"},
                    "groupOf": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": [
                    "uiType", "isEditable", "lastUpdated", "isMandatory", "gateway", "dbType",
                    "dateCreated", "isMaskable", "name", "scheme", "id", "fieldScope", "title"
                ]
            }
        },
        "noCostEmiSupported": {"type": "boolean"},
        "gpmfFeatures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paymentFlowId": {"type": "string"},
                    "supportedNetworks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "isTokenized": {"type": "boolean"},
                                "network": {"type": "string"},
                                "gpmfId": {"type": "string"}
                            },
                            "required": ["isTokenized", "network", "gpmfId"]
                        }
                    }
                },
                "required": ["paymentFlowId", "supportedNetworks"]
            }
        },
        "emi_options": {
            "type": "array",
            "items": {"type": "object"}
        }
    },
    "required": [
        "masterAccountDetail",
        "emandateAndTPVBanks",
        "dotpEnableFlag",
        "accessControlAllowed",
        "paymentMethods",
        "scheme",
        "noCostEmiSupported",
        "gpmfFeatures",
        "emi_options"
    ]
}

get_gateway_details_response_schema = {
    "type": "object",
    "properties": {
        "emandateAndTPVBanks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paymentMethodType": {"type": "string"},
                    "disabled": {"type": "boolean"},
                    "validationType": {"type": "string"},
                    "gatewayCardInfoId": {"type": "string"},
                    "bankName": {"type": "string"},
                    "emandateRegisterMaxAmount": {"type": "number"},
                    "isTokenized": {"type": "boolean"},
                    "gpmfId": {"type": "string"}
                }
            }
        },
        "merchantGatewayAccount": {
            "type": "object",
            "properties": {
                "isJuspayAccount": {"type": "boolean"},
                "merchantId": {"type": "string"},
                "enforcePaymentMethodAcceptance": {"type": "boolean"},
                "supportedPaymentFlows": {"type": "string"},
                "disabled": {"type": "boolean"},
                "gateway": {"type": "string"},
                "accountDetails": {"type": "string"},
                "paymentMethods": {"type": "string"},
                "dateCreated": {"type": "string"},
                "version": {"type": "integer"},
                "testMode": {"type": "boolean"},
                "id": {"type": "integer"},
                "lastModified": {"type": "string"}
            },
            "required": [
                "isJuspayAccount", "merchantId", "enforcePaymentMethodAcceptance",
                "supportedPaymentFlows", "disabled", "gateway", "accountDetails",
                "paymentMethods", "dateCreated", "version", "testMode", "id", "lastModified"
            ]
        },
        "gpmfFeatures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "lastUpdated": {"type": "string"},
                    "gatewayPaymentMethodFlowId": {"type": "string"},
                    "disabled": {"type": "boolean"},
                    "dateCreated": {"type": "string"},
                    "id": {"type": "integer"},
                    "merchantGatewayAccountId": {"type": "integer"}
                },
                "required": [
                    "lastUpdated", "gatewayPaymentMethodFlowId", "disabled",
                    "dateCreated", "id", "merchantGatewayAccountId"
                ]
            }
        },
        "emiOptions": {
            "type": "object"
        }
    },
    "required": [
        "emandateAndTPVBanks",
        "merchantGatewayAccount",
        "gpmfFeatures",
        "emiOptions"
    ]
}

list_gateway_scheme_response_schema = {
    "type": "array",
    "items": {
        "type": "string"
    }
}

get_merchant_gateways_pm_details_response_schema = {
    "type": "object",
    "additionalProperties": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "paymentMethodType": {"type": "string"},
                "name": {"type": "string"},
                "bankCode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "description": {"type": "string"}
            },
            "required": ["paymentMethodType", "name", "bankCode", "description"]
        }
    }
}

get_offer_details_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "offer_details_id": {"type": "string"},
            "rows_received": {"type": "integer"},
            "rows_succeeded": {"type": "integer"},
            "rows_failed": {"type": "integer"},
            "status_message": {"type": "string"},
            "completed_at": {"type": "string"},
            "file_name": {"type": "string"},
            "id": {"type": "string"},
            "upload_type": {"type": "string"},
            "status": {"type": "string"},
            "created_at": {"type": "string"}
        },
        "required": [
            "offer_details_id",
            "rows_received",
            "rows_succeeded",
            "rows_failed",
            "status_message",
            "completed_at",
            "file_name",
            "id",
            "upload_type",
            "status",
            "created_at"
        ]
    }
}

list_offers_response_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "total_count": {"type": "integer"},
                "count": {"type": "integer"}
            },
            "required": ["total_count", "count"]
        },
        "list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "offer_id": {"type": "string"},
                    "offer_code": {"type": "string"},
                    "status": {"type": "string"},
                    "has_multi_codes": {"type": "boolean"},
                    "eligibility_mode": {"type": "string"},
                    "offer_description": {
                        "type": "object",
                        "properties": {
                            "sponsored_by": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "tnc": {"type": "string"}
                        },
                        "required": ["sponsored_by", "title", "description", "tnc"]
                    },
                    "ui_configs": {
                        "type": "object",
                        "properties": {
                            "offer_display_priority": {"type": "integer"},
                            "auto_apply": {"type": "string"},
                            "should_validate": {"type": "string"},
                            "is_hidden": {"type": "string"}
                        },
                        "required": [
                            "offer_display_priority",
                            "auto_apply",
                            "should_validate",
                            "is_hidden"
                        ]
                    },
                    "group_id": {"type": "string"},
                    "rule_dsl": {
                        "type": "object"
                    },
                    "created_at": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                },
                "required": [
                    "offer_id",
                    "offer_code",
                    "status",
                    "has_multi_codes",
                    "eligibility_mode",
                    "offer_description",
                    "ui_configs",
                    "group_id",
                    "rule_dsl",
                    "created_at",
                    "start_time",
                    "end_time"
                ]
            }
        }
    },
    "required": ["summary", "list"]
}

list_orders_v4_response_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "sum": {"type": "integer"},
                "totalCount": {"type": "integer"}
            },
            "required": ["count", "sum", "totalCount"]
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "amount": {"type": "number"},
                    "merchantId": {"type": "string"},
                    "paymentGateway": {"type": "string"},
                    "paymentMethodType": {"type": "string"},
                    "orderUuid": {"type": "string"},
                    "refundedEntirely": {"type": "boolean"},
                    "amountRefunded": {"type": "number"},
                    "orderType": {"type": "string"},
                    "customerId": {"type": "string"},
                    "dateCreated": {"type": "string"},
                    "currency": {"type": "string"},
                    "mandateFeature": {"type": "string"},
                    "preferredGateway": {"type": "string"},
                    "customerPhone": {"type": "string"},
                    "customerEmail": {"type": "string"},
                    "orderId": {"type": "string"},
                    "lastModified": {"type": "string"},
                    "respCode": {"type": "string"},
                    "respMessage": {"type": "string"},
                    "sourceObject": {"type": "string"},
                    "sourceObjectId": {"type": "string"}
                },
                "required": [
                    "status", "amount", "merchantId", "orderUuid", "refundedEntirely",
                    "amountRefunded", "orderType", "dateCreated", "currency", "mandateFeature",
                    "customerPhone", "customerEmail", "orderId", "lastModified"
                ]
            }
        }
    },
    "required": ["summary", "rows"]
}

get_order_details_response_schema = {
    "type": "object",
    "properties": {
        "transactions": {
            "type": "object",
            "properties": {
                "order_metadata": {
                    "type": "object",
                    "properties": {
                        "browser": {"type": "string"},
                        "operating_system": {"type": "string"},
                        "user_agent": {"type": "string"},
                        "partition_key": {"type": "string"},
                        "last_updated": {"type": "string"},
                        "order_reference_id": {"type": "integer"},
                        "device": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "metadata": {"type": "string"},
                        "id": {"type": "integer"},
                        "mobile": {"type": "boolean"},
                        "ip_address": {"type": "string"},
                        "date_created": {"type": "string"},
                        "browser_version": {"type": "string"},
                        "referer": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                    },
                    "required": [
                        "browser", "operating_system", "user_agent", "partition_key", "last_updated",
                        "order_reference_id", "metadata", "id", "mobile", "ip_address", "date_created", "browser_version"
                    ]
                },
                "list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string"},
                            "status": {"type": "string"},
                            "response_category": {"type": "object"},
                            "net_amount": {"type": "number"},
                            "txn_amount_breakup": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "amount": {"type": "number"},
                                        "name": {"type": "string"},
                                        "method": {"type": "string"},
                                        "sno": {"type": "integer"}
                                    },
                                    "required": ["amount", "name", "method", "sno"]
                                }
                            },
                            "is_emi": {"type": "boolean"},
                            "source_object": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "refunded": {"type": "boolean"},
                            "error_code": {"type": "string"},
                            "gateway_id": {"type": "integer"},
                            "refunds": {"type": "array", "items": {}},
                            "surcharge_amount": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                            "is_cvv_less_txn": {"type": "boolean"},
                            "txn_uuid": {"type": "string"},
                            "gateway": {"type": "string"},
                            "created": {"type": "string"},
                            "tax_amount": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                            "effective_amount": {"type": "number"},
                            "payment_gateway_response": {
                                "type": "object",
                                "properties": {
                                    "debit_amount": {"type": "string"},
                                    "auth_id_code": {"type": "string"},
                                    "created": {"type": "string"},
                                    "rrn": {"type": "string"},
                                    "epg_txn_id": {"type": "string"},
                                    "txn_id": {"type": "string"},
                                    "resp_message": {"type": "string"},
                                    "discount_amount": {"type": "number"},
                                    "resp_code": {"type": "string"}
                                },
                                "required": [
                                    "debit_amount", "auth_id_code", "created", "rrn", "epg_txn_id",
                                    "txn_id", "resp_message", "discount_amount", "resp_code"
                                ]
                            },
                            "txn_amount": {"type": "number"},
                            "amount_refunded": {"type": "number"},
                            "remaining_refundable_amount": {"type": "string"},
                            "error_message": {"type": "string"},
                            "payment_flows": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"}
                                    },
                                    "required": ["name", "description"]
                                }
                            },
                            "txn_object_type": {"type": "string"},
                            "currency": {"type": "string"},
                            "is_conflicted": {"type": "boolean"},
                            "redirect": {"type": "boolean"},
                            "source_object_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "express_checkout": {"type": "boolean"},
                            "txn_type": {"type": "string"},
                            "txn_id": {"type": "string"},
                            "emi_bank": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "emi_tenure": {"type": "integer"},
                            "payment_info": {
                                "type": "object",
                                "properties": {
                                    "card": {
                                        "type": "object",
                                        "properties": {
                                            "card_issuer_country": {"type": "string"},
                                            "name_on_card": {"type": "string"},
                                            "last_four_digits": {"type": "string"},
                                            "card_reference": {"type": "string"},
                                            "card_issuer": {"type": "string"},
                                            "card_brand": {"type": "string"},
                                            "card_fingerprint": {"type": "string"},
                                            "card_type": {"type": "string"},
                                            "token": {
                                                "type": "object",
                                                "properties": {
                                                    "tokenization_consent": {"type": "boolean"},
                                                    "tokenization_consent_ui_presented": {"type": "boolean"},
                                                    "tokenization_consent_failure_reason": {"type": "string"},
                                                    "tokenization_failure_reason": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                                                    "using_token": {"type": "boolean"},
                                                    "is_token_created": {"type": "boolean"}
                                                },
                                                "required": [
                                                    "tokenization_consent", "tokenization_consent_ui_presented",
                                                    "tokenization_consent_failure_reason", "tokenization_failure_reason",
                                                    "using_token", "is_token_created"
                                                ]
                                            },
                                            "card_isin": {"type": "string"},
                                            "token_type": {"type": "string"},
                                            "using_saved_card": {"type": "boolean"},
                                            "expiry_year": {"type": "string"},
                                            "saved_to_locker": {"type": "boolean"},
                                            "expiry_month": {"type": "string"}
                                        },
                                        "required": [
                                            "card_issuer_country", "name_on_card", "last_four_digits", "card_reference",
                                            "card_issuer", "card_brand", "card_fingerprint", "card_type", "token",
                                            "card_isin", "token_type", "using_saved_card", "expiry_year", "saved_to_locker", "expiry_month"
                                        ]
                                    },
                                    "auth_type": {"type": "string"},
                                    "payment_method": {"type": "string"},
                                    "payment_method_type": {"type": "string"},
                                    "authentication": {"type": "object"}
                                },
                                "required": [
                                    "card", "auth_type", "payment_method", "payment_method_type", "authentication"
                                ]
                            },
                            "txn_flow_info": {"type": "object"}
                        },
                        "required": [
                            "order_id", "status", "response_category", "net_amount", "txn_amount_breakup", "is_emi",
                            "source_object", "refunded", "error_code", "gateway_id", "refunds", "surcharge_amount",
                            "is_cvv_less_txn", "txn_uuid", "gateway", "created", "tax_amount", "effective_amount",
                            "payment_gateway_response", "txn_amount", "amount_refunded", "remaining_refundable_amount",
                            "error_message", "payment_flows", "txn_object_type", "currency", "is_conflicted", "redirect",
                            "source_object_id", "express_checkout", "txn_type", "txn_id", "emi_bank", "emi_tenure",
                            "payment_info", "txn_flow_info"
                        ]
                    }
                },
                "offset": {"type": "integer"},
                "count": {"type": "integer"},
                "capture_amount": {"type": "number"},
                "total": {"type": "integer"}
            },
            "required": [
                "order_metadata", "list", "offset", "count", "capture_amount", "total"
            ]
        },
        "webhooks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "partitionKey": {"type": "string"},
                    "isWebHookNotified": {"type": "boolean"},
                    "dateCreated": {"type": "string"},
                    "primaryObjectId": {"type": "string"},
                    "id": {"type": "string"},
                    "orderReferenceId": {"type": "string"},
                    "eventName": {"type": "string"},
                    "class": {"type": "string"},
                    "primaryObjectType": {"type": "string"}
                },
                "required": [
                    "partitionKey", "isWebHookNotified", "dateCreated", "primaryObjectId",
                    "id", "orderReferenceId", "eventName", "class", "primaryObjectType"
                ]
            }
        },
        "order": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "amount": {"type": "number"},
                "merchantId": {"type": "string"},
                "partitionKey": {"type": "string"},
                "billingAddressId": {"type": "string"},
                "orderUuid": {"type": "string"},
                "refundedEntirely": {"type": "boolean"},
                "customerName": {"type": "string"},
                "amountRefunded": {"type": "number"},
                "orderType": {"type": "string"},
                "udf1": {"type": "string"},
                "customerId": {"type": "string"},
                "returnUrl": {"type": "string"},
                "dateCreated": {"type": "string"},
                "currency": {"type": "string"},
                "version": {"type": "integer"},
                "mandateFeature": {"type": "string"},
                "internalMetadata": {"type": "string"},
                "metadata": {"type": "string"},
                "preferredGateway": {"type": "string"},
                "id": {"type": "string"},
                "customerPhone": {"type": "string"},
                "customerEmail": {"type": "string"},
                "orderId": {"type": "string"},
                "lastModified": {"type": "string"},
                "description": {"type": "string"},
                "udf6": {"type": "string"}
            },
            "required": [
                "status", "amount", "merchantId", "partitionKey", "billingAddressId", "orderUuid",
                "refundedEntirely", "customerName", "amountRefunded", "orderType", "udf1", "customerId",
                "returnUrl", "dateCreated", "currency", "version", "mandateFeature", "internalMetadata",
                "metadata", "preferredGateway", "id", "customerPhone", "customerEmail", "orderId",
                "lastModified", "description", "udf6"
            ]
        },
        "notifications": {
            "type": "array",
            "items": {}
        }
    },
    "required": ["transactions", "webhooks", "order", "notifications"]
}

list_payment_links_v1_response_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "sum": {"type": "integer"},
                "totalCount": {"type": "integer"}
            },
            "required": ["count", "sum", "totalCount"]
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "linkStatus": {"type": "string"},
                    "amount": {"type": "number"},
                    "merchantId": {"type": "string"},
                    "expiry": {"type": "string"},
                    "orderStatus": {"type": "string"},
                    "isEmailPresent": {"type": "boolean"},
                    "sourceObject": {"type": "string"},
                    "isDeepLink": {"type": "boolean"},
                    "dateCreated": {"type": "string"},
                    "iframe": {"type": "string"},
                    "currency": {"type": "string"},
                    "metadata": {"type": "string"},
                    "id": {"type": "string"},
                    "web": {"type": "string"},
                    "mobile": {"type": "string"},
                    "orderId": {"type": "string"},
                    "lastModified": {"type": "string"},
                    "resend": {"type": "boolean"},
                    "isMobilePresent": {"type": "boolean"}
                },
                "required": [
                    "linkStatus", "amount", "merchantId", "expiry", "orderStatus", "isEmailPresent",
                    "sourceObject", "isDeepLink", "dateCreated", "iframe", "currency", "metadata",
                    "id", "web", "mobile", "orderId", "lastModified", "resend", "isMobilePresent"
                ]
            }
        }
    },
    "required": ["summary", "rows"]
}

report_details_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "task_type": {"type": "string"},
            "source_table": {"type": "string"},
            "metrics": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}]},
            "query_duration": {"type": "integer"},
            "timezone_region": {"type": "string"},
            "task_channel": {"type": "array", "items": {"type": "string"}},
            "interval": {"type": "integer"},
            "status": {"type": "string"},
            "report_links": {"type": "array", "items": {}},
            "user_name": {"type": "string"},
            "task_description": {"type": "string"},
            "email": {"type": "array", "items": {"type": "string"}},
            "alert_mode": {"type": "string"},
            "schedule_time": {"type": "string"},
            "task_name": {"type": "string"},
            "is_password_protected": {"type": "boolean"},
            "dimensions": {"type": "array", "items": {"type": "string"}},
            "task_uid": {"type": "string"},
            "standard_report_type": {"type": "string"},
            "is_subscribed": {"type": "boolean"},
            "schedule_day_date": {"type": "string"},
            "merchant_id": {"type": "string"},
            "filters": {"type": "object"},
            "task_start_date": {"type": "string"},
            "signum": {"type": "array", "items": {"type": "string"}},
            "threshold": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}]}
        },
        "required": [
            "task_type", "source_table", "metrics", "query_duration", "timezone_region",
            "task_channel", "interval", "status", "report_links", "user_name", "task_description",
            "email", "alert_mode", "schedule_time", "task_name", "is_password_protected",
            "dimensions", "task_uid", "standard_report_type", "is_subscribed", "schedule_day_date",
            "merchant_id", "filters", "task_start_date", "signum", "threshold"
        ]
    }
}

list_report_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "task_type": {"type": "string"},
            "source_table": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "metrics": {"anyOf": [{"type": "array", "items": {}}, {"type": "null"}]},
            "query_duration": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "timezone_region": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "task_channel": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}]},
            "interval": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "user_name": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "task_description": {"type": "string"},
            "email": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}]},
            "alert_mode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "schedule_time": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "task_name": {"type": "string"},
            "is_password_protected": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
            "is_pi_report": {"type": "boolean"},
            "dimensions": {"anyOf": [{"type": "array", "items": {}}, {"type": "null"}]},
            "task_uid": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "standard_report_type": {"type": "string"},
            "schedule_day_date": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "merchant_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "filters": {"anyOf": [{"type": "object"}, {"type": "null"}]},
            "task_start_date": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "signum": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}]},
            "threshold": {"anyOf": [{"type": "array", "items": {}}, {"type": "null"}]},
            "report_links": {"anyOf": [{"type": "array", "items": {}}, {"type": "null"}]}
        },
        "required": [
            "task_type", "source_table", "metrics", "query_duration", "timezone_region",
            "task_channel", "interval", "status", "user_name", "task_description",
            "email", "alert_mode", "schedule_time", "task_name", "is_password_protected",
            "is_pi_report", "dimensions", "task_uid", "standard_report_type", "schedule_day_date",
            "merchant_id", "filters", "task_start_date", "signum", "threshold"
        ]
    }
}

get_conflict_settings_response_schema = {
    "type": "object",
    "properties": {
        "merchantId": {"type": "string"},
        "autoRefundMultipleChargedTransactions": {"type": "boolean"},
        "autoRefundFailureToSuccessTransactions": {"type": "boolean"},
        "pmtWiseConflictThresholdTimeForMandateRegister": {
            "type": "object",
            "properties": {
                "walletEmandateConflictThresholdTime": {"type": "integer"},
                "aadhaarEmandateConflictThresholdTime": {"type": "integer"},
                "paperNachEmandateConflictThresholdTime": {"type": "integer"},
                "nbEmandateConflictThresholdTime": {"type": "integer"},
                "cardEmandateConflictThresholdTime": {"type": "integer"},
                "upiEmandateConflictThresholdTime": {"type": "integer"},
                "cardMandateConflictThresholdTime": {"type": "integer"}
            },
            "required": [
                "walletEmandateConflictThresholdTime",
                "aadhaarEmandateConflictThresholdTime",
                "paperNachEmandateConflictThresholdTime",
                "nbEmandateConflictThresholdTime",
                "cardEmandateConflictThresholdTime",
                "upiEmandateConflictThresholdTime",
                "cardMandateConflictThresholdTime"
            ]
        },
        "autoRefundConflictMandateRegisterTransactions": {"type": "boolean"},
        "autoRefundConflictTransactions": {"type": "boolean"},
        "conflictStatusEmail": {"type": "string"},
        "enableConflictStatusNotification": {"type": "boolean"},
        "autoRefundConflictThresholdInMins": {"type": "integer"}
    },
    "required": [
        "merchantId",
        "autoRefundMultipleChargedTransactions",
        "autoRefundFailureToSuccessTransactions",
        "pmtWiseConflictThresholdTimeForMandateRegister",
        "autoRefundConflictMandateRegisterTransactions",
        "autoRefundConflictTransactions",
        "conflictStatusEmail",
        "enableConflictStatusNotification",
        "autoRefundConflictThresholdInMins"
    ]
}

get_general_settings_response_schema = {
    "type": "object",
    "properties": {
        "iframePref": {
            "type": "object",
            "properties": {
                "deleteCardOnExpiry": {"type": "boolean"},
                "returnUrl": {"type": "string"},
                "defaultCurrency": {"type": "string"},
                "version": {"type": "integer"},
                "merchantLogoUrl": {"type": "string"},
                "id": {"type": "integer"},
                "redirectModeOnly": {"type": "boolean"},
                "walletTopupReturnUrl": {"type": "string"},
                "orderSessionTimeout": {"type": "integer"}
            },
            "required": [
                "deleteCardOnExpiry", "returnUrl", "defaultCurrency", "version", "merchantLogoUrl",
                "id", "redirectModeOnly", "walletTopupReturnUrl", "orderSessionTimeout"
            ]
        },
        "ruleConfigured": {"type": "boolean"},
        "merchantAccount": {
            "type": "object",
            "properties": {
                "paymentResponseHashKey": {"type": "string"},
                "webHookCustomHeaders": {"type": "string"},
                "webHookPassword": {"type": "string"},
                "merchantId": {"type": "string"},
                "internalHashKey": {"type": "string"},
                "enableSaveCardBeforeAuth": {"type": "boolean"},
                "webHookUsername": {"type": "string"},
                "merchantName": {"type": "string"},
                "tenantAccountId": {"type": "string"},
                "autoRefundMultipleChargedTransactions": {"type": "boolean"},
                "merchantTier": {"type": "string"},
                "webHookurl": {"type": "string"},
                "enabledInstantRefund": {"type": "boolean"},
                "adminContactEmail": {"type": "string"},
                "showSurchargeBreakupScreen": {"type": "boolean"},
                "shouldAddSurcharge": {"type": "boolean"},
                "payoutMid": {"type": "string"},
                "returnUrl": {"type": "string"},
                "dateCreated": {"type": "string"},
                "userId": {"type": "integer"},
                "mandateConfig": {"type": "string"},
                "internalMetadata": {"type": "string"},
                "webhookConfigs": {"type": "string"},
                "enablePaymentResponseHash": {"type": "boolean"},
                "id": {"type": "integer"},
                "autoRefundConflictTransactions": {"type": "boolean"},
                "externalMetadata": {"type": "string"},
                "cardEncodingKey": {"type": "string"},
                "includeSurchargeAmountForRefund": {"type": "boolean"},
                "lastModified": {"type": "string"},
                "clientConfig": {"type": "string"},
                "enableTxnFilter": {"type": "boolean"},
                "conflictStatusEmail": {"type": "string"},
                "enableConflictStatusNotification": {"type": "boolean"},
                "autoRefundConflictThresholdInMins": {"type": "integer"},
                "webHookapiversion": {"type": "string"},
                "redirectToMerchantWithHttpPost": {"type": "boolean"}
            },
            "required": [
                "paymentResponseHashKey", "webHookCustomHeaders", "webHookPassword", "merchantId",
                "internalHashKey", "enableSaveCardBeforeAuth", "webHookUsername", "merchantName",
                "tenantAccountId", "autoRefundMultipleChargedTransactions", "merchantTier", "webHookurl",
                "enabledInstantRefund", "adminContactEmail", "showSurchargeBreakupScreen", "shouldAddSurcharge",
                "payoutMid", "returnUrl", "dateCreated", "userId", "mandateConfig", "internalMetadata",
                "webhookConfigs", "enablePaymentResponseHash", "id", "autoRefundConflictTransactions",
                "externalMetadata", "cardEncodingKey", "includeSurchargeAmountForRefund", "lastModified",
                "clientConfig", "enableTxnFilter", "conflictStatusEmail", "enableConflictStatusNotification",
                "autoRefundConflictThresholdInMins", "webHookapiversion", "redirectToMerchantWithHttpPost"
            ]
        }
    },
    "required": ["iframePref", "ruleConfigured", "merchantAccount"]
}

get_mandate_settings_response_schema = {
    "type": "object",
    "properties": {
        "merchantId": {"type": "string"},
        "executeMandateAutoRetryEnabled": {"type": "boolean"},
        "mandateAutoRevokeEnabled": {"type": "boolean"},
        "mandateRetryConfig": {"type": "string"},
        "enableMandateWorkFlow": {"type": "boolean"}
    },
    "required": [
        "merchantId",
        "executeMandateAutoRetryEnabled",
        "mandateAutoRevokeEnabled",
        "mandateRetryConfig",
        "enableMandateWorkFlow"
    ]
}

get_priority_logic_settings_response_schema = {
    "type": "object",
    "properties": {
        "gatewayPriority": {"type": "string"},
        "logics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "lastUpdated": {"type": "string"},
                    "dateCreated": {"type": "string"},
                    "priorityLogic": {"type": "string"},
                    "version": {"type": "integer"},
                    "id": {"type": "string"},
                    "isActiveLogic": {"type": "boolean"},
                    "merchantAccountId": {"type": "integer"}
                },
                "required": [
                    "status", "lastUpdated", "dateCreated", "priorityLogic",
                    "version", "id", "isActiveLogic", "merchantAccountId"
                ]
            }
        },
        "useCode": {"type": "boolean"},
        "gatewayPriorityLogic": {"type": "string"},
        "enableGatewayReferenceIdBasedRouting": {"type": "boolean"},
        "gateways": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "disabled": {"type": "boolean"},
                    "gateway": {"type": "string"},
                    "paymentMethods": {"type": "string"},
                    "testMode": {"type": "boolean"},
                    "referenceId": {"type": "string"}
                },
                "required": [
                    "disabled", "gateway", "paymentMethods", "testMode"
                ]
            }
        }
    },
    "required": [
        "gatewayPriority",
        "logics",
        "useCode",
        "gatewayPriorityLogic",
        "enableGatewayReferenceIdBasedRouting",
        "gateways"
    ]
}

get_routing_settings_response_schema = {
    "type": "object",
    "properties": {
        "merchantId": {"type": "string"},
        "gatewaySuccessRateBasedOutageInput": {
            "type": "object",
            "properties": {
                "merchantOutagePaymentMethodWiseInputs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "downMaxCountThreshold": {"type": "integer"},
                            "fluctuateThreshold": {"type": "number"},
                            "paymentMethodType": {"type": "string"},
                            "downThreshold": {"type": "number"},
                            "fluctuateMaxCountThreshold": {"type": "integer"},
                            "paymentMethod": {"type": "string"}
                        },
                        "required": [
                            "downMaxCountThreshold",
                            "fluctuateThreshold",
                            "paymentMethodType",
                            "downThreshold",
                            "fluctuateMaxCountThreshold"
                        ]
                    }
                },
                "defaultMerchantOutageDownMaxCountThreshold": {"type": "integer"},
                "defaultMerchantOutageFluctuateThreshold": {"type": "number"},
                "defaultMerchantOutageFluctuateMaxCountThreshold": {"type": "integer"},
                "defaultMerchantOutageDownThreshold": {"type": "number"}
            },
            "required": [
                "merchantOutagePaymentMethodWiseInputs",
                "defaultMerchantOutageDownMaxCountThreshold",
                "defaultMerchantOutageFluctuateThreshold",
                "defaultMerchantOutageFluctuateMaxCountThreshold",
                "defaultMerchantOutageDownThreshold"
            ]
        },
        "gatewaySuccessRateBasedDeciderInput": {
            "type": "object",
            "properties": {
                "defaultGlobalEliminationMaxCountThreshold": {"type": "integer"},
                "defaultEliminationThreshold": {"type": "number"},
                "defaultEliminationLevel": {"type": "string"},
                "defaultGlobalEliminationThreshold": {"type": "number"}
            },
            "required": [
                "defaultGlobalEliminationMaxCountThreshold",
                "defaultEliminationThreshold",
                "defaultEliminationLevel",
                "defaultGlobalEliminationThreshold"
            ]
        },
        "enableGatewayReferenceIdBasedRouting": {"type": "boolean"},
        "enableSuccessRateBasedGatewayElimination": {"type": "boolean"}
    },
    "required": [
        "merchantId",
        "gatewaySuccessRateBasedOutageInput",
        "gatewaySuccessRateBasedDeciderInput",
        "enableGatewayReferenceIdBasedRouting",
        "enableSuccessRateBasedGatewayElimination"
    ]
}

get_webhook_settings_response_schema = {
    "type": "object",
    "properties": {
        "webHookCustomHeaders": {"type": "string"},
        "webHookPassword": {"type": "string"},
        "merchantId": {"type": "string"},
        "webhookSslCaCert": {"type": "string"},
        "webHookUsername": {"type": "string"},
        "webHookurl": {"type": "string"},
        "webhookConfigs": {"type": "string"},
        "webHookapiversion": {"type": "string"}
    },
    "required": [
        "webHookCustomHeaders",
        "webHookPassword",
        "merchantId",
        "webhookSslCaCert",
        "webHookUsername",
        "webHookurl",
        "webhookConfigs",
        "webHookapiversion"
    ]
}

get_user_response_schema = {
    "type": "object",
    "properties": {
        "isAdminAccount": {"type": "boolean"},
        "fullName": {"type": "string"},
        "email": {"type": "string"},
        "status": {"type": "string"},
        "context": {"type": "string"},
        "enabled": {"type": "boolean"},
        "tenantAccountId": {"type": "string"},
        "passwordExpired": {"type": "boolean"},
        "lastPasswordUpdated": {"type": "string"},
        "accountLocked": {"type": "boolean"},
        "username": {"type": "string"},
        "accountExpired": {"type": "boolean"},
        "migratedToEmailLogin": {"type": "boolean"},
        "mandatory2FA": {"type": "boolean"},
        "isPasswordSetByUser": {"type": "boolean"},
        "id": {"type": "integer"},
        "acl": {"type": "string"}
    },
    "required": [
        "isAdminAccount",
        "fullName",
        "email",
        "status",
        "context",
        "enabled",
        "tenantAccountId",
        "passwordExpired",
        "lastPasswordUpdated",
        "accountLocked",
        "username",
        "accountExpired",
        "migratedToEmailLogin",
        "mandatory2FA",
        "isPasswordSetByUser",
        "id",
        "acl"
    ]
}

list_users_v2_response_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "totalCount": {"type": "integer"}
            },
            "required": ["count", "totalCount"]
        },
        "adminInfo": {
            "type": "object",
            "properties": {
                "fullName": {"type": "string"},
                "email": {"type": "string"},
                "lastLoginTime": {"type": "string"},
                "status": {"type": "string"},
                "context": {"type": "string"},
                "enabled": {"type": "boolean"},
                "tenantAccountId": {"type": "string"},
                "passwordExpired": {"type": "boolean"},
                "lastPasswordUpdated": {"type": "string"},
                "accountLocked": {"type": "boolean"},
                "username": {"type": "string"},
                "employeeRole": {"type": "string"},
                "accountExpired": {"type": "boolean"},
                "mandatory2FA": {"type": "boolean"},
                "isPasswordSetByUser": {"type": "boolean"},
                "id": {"type": "integer"},
                "employeeDetails": {
                    "type": "object",
                    "properties": {
                        "supervisorCode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "branchName": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "employeeRole": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "branchCode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "employeeCode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "employeeName": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "supervisorPhoneNo": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "departmentName": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "departmentCode": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                    },
                    "required": [
                        "supervisorCode", "branchName", "employeeRole", "branchCode",
                        "employeeCode", "employeeName", "supervisorPhoneNo",
                        "departmentName", "departmentCode"
                    ]
                },
                "externalMetadata": {"type": "string"},
                "acl": {"type": "string"}
            },
            "required": [
                "fullName", "email", "lastLoginTime", "status", "context", "enabled",
                "tenantAccountId", "passwordExpired", "lastPasswordUpdated", "accountLocked",
                "username", "employeeRole", "accountExpired", "mandatory2FA", "isPasswordSetByUser",
                "id", "employeeDetails", "externalMetadata", "acl"
            ]
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fullName": {"type": "string"},
                    "email": {"type": "string"},
                    "lastLoginTime": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "status": {"type": "string"},
                    "context": {"type": "string"},
                    "emailLoginId": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "enabled": {"type": "boolean"},
                    "tenantAccountId": {"type": "string"},
                    "passwordExpired": {"type": "boolean"},
                    "lastPasswordUpdated": {"type": "string"},
                    "accountLocked": {"type": "boolean"},
                    "username": {"type": "string"},
                    "employeeRole": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "accountExpired": {"type": "boolean"},
                    "migratedToEmailLogin": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
                    "mandatory2FA": {"type": "boolean"},
                    "isPasswordSetByUser": {"type": "boolean"},
                    "id": {"type": "integer"},
                    "employeeDetails": {
                        "type": "object",
                        "properties": {
                            "supervisorCode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "branchName": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "employeeRole": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "branchCode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "employeeCode": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "employeeName": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "supervisorPhoneNo": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "departmentName": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "departmentCode": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                        },
                        "required": [
                            "supervisorCode", "branchName", "employeeRole", "branchCode",
                            "employeeCode", "employeeName", "supervisorPhoneNo",
                            "departmentName", "departmentCode"
                        ]
                    },
                    "acl": {"type": "string"}
                },
                "required": [
                    "fullName", "email", "status", "context", "enabled", "tenantAccountId",
                    "passwordExpired", "lastPasswordUpdated", "accountLocked", "username",
                    "accountExpired", "mandatory2FA", "isPasswordSetByUser", "id", "acl"
                ]
            }
        }
    },
    "required": ["summary", "adminInfo", "rows"]
}

list_surcharge_rules_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "markdown": {"type": "string"},
            "createdAt": {"type": "string"},
            "rule": {"type": "string"},
            "active": {"type": "boolean"},
            "ruleBased": {"type": "string"},
            "id": {"type": "string"},
            "updatedAt": {"type": "string"},
            "ruleType": {"type": "string"},
            "merchantAccountId": {"type": "string"}
        },
        "required": [
            "status",
            "markdown",
            "createdAt",
            "rule",
            "active",
            "ruleBased",
            "id",
            "updatedAt",
            "ruleType",
            "merchantAccountId"
        ]
    }
}

list_outages_response_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "issuerName": {"type": "string"},
            "status": {"type": "string"},
            "juspayBankCode": {"type": "string"},
            "merchantId": {"type": "string"},
            "paymentMethodType": {"type": "string"},
            "paymentMethod": {"type": "string"},
            "stage": {"type": "string"},
            "outagePeriods": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "startTime": {"type": "string"},
                        "endTime": {"type": "string"},
                        "duration": {"type": "integer"}
                    },
                    "required": [
                        "startTime",
                        "endTime", 
                        "duration"
                    ]
                }
            }
        },
        "required": [
            "issuerName",
            "status",
            "juspayBankCode",
            "merchantId",
            "paymentMethodType",
            "paymentMethod",
            "outagePeriods"
        ]
    }
}
rag_query_response_schema = {
    "type": "object",
    "properties": {
        "response": {
            "type": "string",
            "description": "The generated answer from the RAG system",
        },
        "query": {"type": "string", "description": "The original query that was asked"},
        "model": {
            "type": "string",
            "description": "The model used for generation (e.g., gemini-2.5-flash-lite-preview-06-17)",
        },
        "sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of source URLs from the retrieved documents",
        },
        "metrics": {
            "type": "object",
            "properties": {
                "client_init_time": {
                    "type": "number",
                    "description": "Time taken to initialize the client (seconds)",
                },
                "time_to_first_chunk": {
                    "type": "number",
                    "description": "Time to receive first response chunk (seconds)",
                },
                "total_generation_time": {
                    "type": "number",
                    "description": "Total time for response generation (seconds)",
                },
                "total_execution_time": {
                    "type": "number",
                    "description": "Total execution time (seconds)",
                },
                "chunk_count": {
                    "type": "integer",
                    "description": "Number of response chunks received",
                },
                "response_length": {
                    "type": "integer",
                    "description": "Length of the response in characters",
                },
                "avg_chunks_per_second": {
                    "type": "number",
                    "description": "Average chunks processed per second",
                },
                "avg_chars_per_second": {
                    "type": "number",
                    "description": "Average characters generated per second",
                },
            },
            "description": "Performance metrics (optional, included when include_metrics=true)",
        },
        "grounding_metadata": {
            "type": "object",
            "properties": {
                "groundingChunks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "retrievedContext": {
                                "type": "object",
                                "properties": {
                                    "ragChunk": {
                                        "type": "object",
                                        "properties": {
                                            "pageSpan": {"anyOf": [{"type": "object"}, {"type": "null"}]},
                                            "text": {"type": "string"},
                                            "title": {"type": "string"},
                                            "uri": {"type": "string"}
                                        }
                                    },
                                    "text": {"type": "string"},
                                    "title": {"type": "string"},
                                    "uri": {"type": "string"}
                                }
                            },
                            "web": {"anyOf": [{"type": "object"}, {"type": "null"}]}
                        }
                    },
                    "description": "Retrieved chunks used for grounding"
                },
                "groundingSupports": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "confidenceScores": {
                                "type": "array",
                                "items": {"type": "number"}
                            },
                            "groundingChunkIndices": {
                                "type": "array",
                                "items": {"type": "integer"}
                            },
                            "segment": {
                                "type": "object",
                                "properties": {
                                    "endIndex": {"type": "integer"},
                                    "partIndex": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                                    "startIndex": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                                    "text": {"type": "string"}
                                }
                            }
                        }
                    },
                    "description": "Support information for grounding"
                },
                "retrievalMetadata": {"anyOf": [{"type": "object"}, {"type": "null"}]},
                "retrievalQueries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Queries used for retrieval"
                },
                "searchEntryPoint": {"anyOf": [{"type": "object"}, {"type": "null"}]},
                "webSearchQueries": {"anyOf": [{"type": "array"}, {"type": "null"}]}
            },
            "description": "Metadata about grounding and retrieval process"
        }
    },
    "required": ["response", "query", "model", "sources"],
    "additionalProperties": True,
}

list_unified_alerts_response_schema = {
    "type": "array",
    "items": {
        "type": "object",

        '''name, expected_metric, current_metric, order_id, dimensions, merchant_id, category, metadata_alerts_detati, 
        start_time
        metadata_info, category'''

        "properties": {
            
            "name": {"type": "string", "description": "name of alerts"},
            "dimensions": {"type": "string", "description": "JSON string containing alert dimensions"},
            "merchant_id": {"type": "string", "description": "Merchant identifier"},
            "current_metric": {"type": "string", "description": "Current metric value"},
            "expected_metric": {"type": "string", "description": "Expected metric value"},
            "start_time": {"type": "string", "description": "Alert start time"},
            "metadata_alert_details": {"type": "string", "description": "Alert details metadata"},
            "metadata_info": {"type": "string", "description": "Metadata information"}, 
            "recovered_ts": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Recovery timestamp"},
        },
        "required": [
            "name",
            "dimensions",
            "merchant_id",
            "current_metric",
            "expected_metric",
            "start_time",
            "metadata_alert_details",
            "metadata_info",
            "recovered_ts"
        ]
    }
}
