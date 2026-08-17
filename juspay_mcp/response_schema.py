# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

session_preflight_response_schema = {
    "type": "object",
    "properties": {
        "ready": {
            "type": "boolean",
            "description": "True when nothing is missing and the session can be created."
        },
        "gateway": {
            "type": "string",
            "description": "The gateway whose requirements were applied ('DEFAULT' if the requested one was unknown)."
        },
        "gateway_recognised": {
            "type": "boolean",
            "description": "False when the requested gateway had no configured requirements and DEFAULT was used instead."
        },
        "next_action": {
            "type": "string",
            "description": "Instruction for the calling agent. When params are missing it directs the agent to ask the user for them rather than guessing or using placeholders, and to re-run this check before creating the session."
        },
        "missing": {
            "type": "array",
            "description": "Mandatory params that are absent (or blank) and must be collected from the user before proceeding.",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "description": "Name of the missing param."},
                    "description": {"type": "string", "description": "What the param is, to help collect it."},
                    "source": {
                        "type": "string",
                        "description": "'session_schema' if the session create call itself will fail without it; 'gateway' if the session succeeds but the payment cannot complete.",
                        "enum": ["session_schema", "gateway"]
                    }
                },
                "required": ["field", "source"]
            }
        },
        "satisfied": {
            "type": "array",
            "description": "Mandatory params already supplied.",
            "items": {"type": "string"}
        }
    },
    "required": ["ready", "gateway", "next_action", "missing", "satisfied"]
}

session_response_schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "description": "Status of the session (e.g., 'NEW', 'AUTHENTICATED')."},
        "order_id": {"type": "string", "description": "The unique order identifier provided in the request."},
        "id": {"type": "string", "description": "Unique Juspay identifier for this session (e.g., 'hyp_sess_...')."},
        "payment_links": {
            "type": "object",
            "description": "Contains URLs for different payment integration methods.",
            "properties": {
                "web": {"type": "string", "description": "URL for standard web redirection payment flow."},
                "iframe": {"type": "string", "description": "URL to embed the payment page in an iframe."},
                "mobile": {"type": "string", "description": "Intent URL for invoking mobile SDK/app payments."}
            }
        },
        "sdk_payload": {
            "type": "object",
            "description": "Payload specifically for integration with Juspay Mobile SDKs.",
             "properties": {
                 "requestId": {"type": "string", "description": "Request identifier for SDK."},
                 "service": {"type": "string", "description": "Service identifier for SDK."},
                 "payload": {"type": "object", "description": "Nested payload containing SDK-specific parameters."}
             }
        }
    },
    "required": ["status", "order_id", "id", "payment_links"]
}

order_status_response_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique Juspay identifier for the order (e.g., 'ordeh_...')."},
        "order_id": {"type": "string", "description": "The unique order identifier provided by the merchant."},
        "status": {"type": "string", "description": "Current status of the order (e.g., 'CHARGED', 'PENDING_VBV', 'REFUNDED')."},
        "status_id": {"type": "integer", "description": "Numeric ID corresponding to the order status."},
        "amount": {"type": "number", "format": "double", "description": "The total amount of the order."},
        "currency": {"type": "string", "description": "Currency code (e.g., 'INR')."},
        "customer_id": {"type": "string", "description": "Merchant's identifier for the customer."},
        "customer_email": {"type": "string", "description": "Customer's email address."},
        "customer_phone": {"type": "string", "description": "Customer's phone number."},
        "date_created": {"type": "string", "format": "date-time", "description": "Timestamp when the order was created (UTC)."},
        "amount_refunded": {"type": "number", "format": "double", "description": "Total amount refunded for this order so far."},
        "refunded": {"type": "boolean", "description": "Indicates if the order has been fully refunded."},
        "txn_id": {"type": "string", "description": "Juspay's transaction identifier for the primary payment attempt."},
        "payment_method_type": {"type": "string", "description": "Type of payment method used (e.g., 'CARD', 'NB', 'WALLET')."},
        "payment_method": {"type": "string", "description": "Specific payment method used (e.g., 'VISA', 'HDFC')."},
        "card": {
            "type": "object",
            "description": "Details of the card used for payment (present if payment_method_type is 'CARD').",
            "properties": {
                 "last_four_digits": {"type": "string"},
                 "card_brand": {"type": "string"},
                 "card_type": {"type": "string", "description": "e.g., 'CREDIT', 'DEBIT'"},
                 "card_issuer": {"type": "string", "description": "Issuing bank name."}
            }
        },
        "refunds": {
            "type": "array",
            "description": "List of refund transactions associated with this order.",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Unique Juspay identifier for the refund (e.g., 'rfnd_...')."},
                    "unique_request_id": {"type": "string", "description": "The unique ID provided by the merchant when initiating the refund."},
                    "amount": {"type": "number", "format": "double", "description": "Amount of this specific refund."},
                    "status": {"type": "string", "description": "Status of the refund (e.g., 'COMPLETED', 'PENDING')."},
                    "created": {"type": "string", "format": "date-time", "description": "Timestamp when the refund was created (UTC)."}
                }
            }
        },
        "txn_detail": {"type": "object", "description": "Detailed information about the transaction."},
        "payment_gateway_response": {"type": "object", "description": "Raw response details from the payment gateway."}
    },
    "required": ["id", "order_id", "status", "status_id", "amount", "currency", "date_created"]
}

refund_creation_response_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique Juspay identifier for the newly created refund transaction (e.g., 'rfnd_...')."},
        "order_id": {"type": "string", "description": "The identifier of the order being refunded."},
        "unique_request_id": {"type": "string", "description": "The unique identifier provided in the refund request."},
        "amount": {"type": "number", "format": "double", "description": "The amount requested for this refund."},
        "currency": {"type": "string", "description": "Currency code (e.g., 'INR')."},
        "status": {"type": "string", "description": "Initial status of the refund upon creation (e.g., 'PENDING', 'INITIATED')."},
        "created": {"type": "string", "format": "date-time", "description": "Timestamp when the refund request was processed (UTC)."}
    },
    "required": ["id", "order_id", "unique_request_id", "amount", "currency", "status", "created"]
}

get_customer_response_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique Juspay identifier for the customer (e.g., 'cst_...')."},
        "object": {"type": "string", "enum": ["customer"], "description": "Object type, always 'customer'."},
        "object_reference_id": {"type": "string", "description": "The unique identifier provided by the merchant when the customer was created."},
        "mobile_number": {"type": "string", "description": "Customer's registered mobile number."},
        "email_address": {"type": "string", "description": "Customer's registered email address."},
        "first_name": {"type": "string", "description": "Customer's first name."},
        "last_name": {"type": "string", "description": "Customer's last name."},
        "mobile_country_code": {"type": "string", "description": "Mobile country code associated with the number."},
        "date_created": {"type": "string", "format": "date-time", "description": "Timestamp when the customer record was created (UTC)."},
        "last_updated": {"type": "string", "format": "date-time", "description": "Timestamp when the customer record was last updated (UTC)."}
    },
    "required": ["id", "object", "object_reference_id", "date_created", "last_updated"]
}

create_customer_response_schema = get_customer_response_schema
update_customer_response_schema = get_customer_response_schema

create_order_response_schema = {
    "type": "object",
    "properties": {
        "status_id": {"type": "integer", "description": "Numeric status identifier (e.g., 10 for NEW)."},
        "status": {"type": "string", "description": "Order status (e.g., 'NEW')."},
        "payment_links": {
            "type": "object",
            "properties": {
                "web": {"type": "string", "description": "URL for web payment."},
                "mobile": {"type": "string", "description": "URL for mobile payment."},
                "iframe": {"type": "string", "description": "URL for iframe payment."}
            }
        },
        "order_id": {"type": "string", "description": "Merchant's order identifier."},
        "merchant_id": {"type": "string", "description": "Merchant identifier."},
        "juspay": {
            "type": "object",
            "properties": {
                "client_auth_token_expiry": {"type": "string", "description": "Expiry time of client auth token."},
                "client_auth_token": {"type": "string", "description": "Client authentication token."}
            }
        },
        "id": {"type": "string", "description": "Juspay's unique identifier for the order."},
        "date_created": {"type": "string", "description": "Order creation timestamp."},
        "customer_phone": {"type": "string", "description": "Customer's phone number."},
        "customer_id": {"type": "string", "description": "Customer identifier."},
        "customer_email": {"type": "string", "description": "Customer's email address."},
        "currency": {"type": "string", "description": "Order currency code (e.g., 'INR')."},
        "amount": {"type": "number", "description": "Order amount."},
        "amount_refunded": {"type": "number", "description": "Refunded amount."},
        "refunded": {"type": "boolean", "description": "Whether the order has been refunded."}
    }
}

update_order_response_schema = {
    "type": "object",
    "properties": {
        "customer_email": {"type": "string", "description": "Customer's email address."},
        "customer_phone": {"type": "string", "description": "Customer's phone number."},
        "customer_id": {"type": "string", "description": "Customer identifier."},
        "status_id": {"type": "integer", "description": "Numeric status identifier."},
        "status": {"type": "string", "description": "Order status (e.g., 'NEW')."},
        "id": {"type": "string", "description": "Juspay's unique identifier for the order."},
        "merchant_id": {"type": "string", "description": "Merchant identifier."},
        "amount": {"type": "number", "description": "Updated order amount."},
        "currency": {"type": "string", "description": "Order currency code."},
        "order_id": {"type": "string", "description": "Merchant's order identifier."},
        "date_created": {"type": "string", "description": "Order creation timestamp."},
        "return_url": {"type": "string", "description": "URL to redirect after payment."},
        "payment_links": {
            "type": "object",
            "properties": {
                "iframe": {"type": "string", "description": "URL for iframe payment."},
                "web": {"type": "string", "description": "URL for web payment."},
                "mobile": {"type": "string", "description": "URL for mobile payment."}
            }
        },
        "refunded": {"type": "boolean", "description": "Whether the order has been refunded."},
        "amount_refunded": {"type": "number", "description": "Refunded amount."},
        "effective_amount": {"type": "number", "description": "Effective amount after discounts."}
    }
}

order_fulfillment_response_schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "description": "Status of the fulfillment operation (e.g., 'SUCCESS')."},
        "merchant_id": {"type": "string", "description": "Merchant identifier."},
        "order_id": {"type": "string", "description": "Order identifier for which fulfillment was updated."},
        "commands": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Status of the command execution."},
                    "metadata": {"type": "string", "description": "Any metadata provided with the fulfillment."},
                    "date_created": {"type": "string", "description": "When the command was executed."},
                    "command": {"type": "string", "description": "The executed command (e.g., 'NO_ACTION')."}
                }
            }
        }
    }
}

txn_refund_response_schema = {
    "type": "object",
    "properties": {
        "unique_request_id": {"type": "string", "description": "Unique identifier for this refund request."},
        "txn_id": {"type": "string", "description": "Transaction ID that was refunded."},
        "status": {"type": "string", "description": "Status of the refund (e.g., 'PENDING')."},
        "sent_to_gateway": {"type": "boolean", "description": "Whether the refund was sent to the payment gateway."},
        "response_code": {"type": "string", "description": "Response code from the payment gateway, if any."},
        "refund_type": {"type": "string", "description": "Type of refund (e.g., 'STANDARD')."},
        "refund_source": {"type": "string", "description": "Source of the refund (e.g., 'RAZORPAY')."},
        "order_id": {"type": "string", "description": "ID of the order that was refunded."},
        "initiated_by": {"type": "string", "description": "Who initiated the refund (e.g., 'API')."},
        "created": {"type": "string", "description": "Timestamp when the refund was created."},
        "amount": {"type": "number", "description": "Amount that was refunded."}
    }
}

create_txn_response_schema = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string", "description": "Order identifier."},
        "status": {"type": "string", "description": "Status of the transaction (e.g., 'PENDING_VBV', 'AUTHORIZED')."},
        "payment": {
            "type": "object",
            "properties": {
                "authentication": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL for any required authentication steps."},
                        "method": {"type": "string", "description": "HTTP method to use for authentication."}
                    }
                }
            }
        },
        "txn_uuid": {"type": "string", "description": "Unique transaction identifier."},
        "offer_details": {
            "type": "object",
            "properties": {
                "offers": {"type": "array", "description": "List of applicable offers."}
            }
        },
        "txn_id": {"type": "string", "description": "Transaction identifier."},
        "merchant_return_url": {"type": "string", "description": "URL where the customer will be redirected after payment."}
    }
}

create_moto_txn_response_schema = create_txn_response_schema

add_card_response_schema = {
    "type": "object",
    "properties": {
        "card_token": {"type": "string", "description": "Unique token for the saved card."},
        "card_reference": {"type": "string", "description": "Card reference string for future use."},
        "card_fingerprint": {"type": "string", "description": "Unique fingerprint of the card."}
    },
    "required": ["card_token", "card_reference", "card_fingerprint"]
}

list_cards_response_schema = {
    "type": "object",
    "properties": {
        "customer_id": {"type": "string", "description": "Customer identifier."},
        "merchantId": {"type": "string", "description": "Merchant identifier."},
        "cards": {
            "type": "array",
            "description": "List of saved cards.",
            "items": {
                "type": "object",
                "properties": {
                    "expired": {"type": "boolean", "description": "Whether the card has expired."},
                    "card_issuer_country": {"type": "string", "description": "Country that issued the card."},
                    "name_on_card": {"type": "string", "description": "Name as printed on the card."},
                    "card_reference": {"type": "string", "description": "Card reference string."},
                    "card_token": {"type": "string", "description": "Unique token for the saved card."},
                    "card_issuer": {"type": "string", "description": "Bank that issued the card."},
                    "card_brand": {"type": "string", "description": "Card brand (e.g., 'VISA', 'MASTERCARD')."},
                    "card_number": {"type": "string", "description": "Masked card number."},
                    "card_fingerprint": {"type": "string", "description": "Unique fingerprint of the card."},
                    "card_type": {"type": "string", "description": "Card type (e.g., 'CREDIT', 'DEBIT')."},
                    "token": {"type": "object", "description": "Token-related details including tokenization status."},
                    "nickname": {"type": "string", "description": "User-assigned nickname for the card."},
                    "card_exp_year": {"type": "string", "description": "Card expiry year."},
                    "card_exp_month": {"type": "string", "description": "Card expiry month."}
                }
            }
        }
    },
    "required": ["customer_id", "cards"]
}

delete_card_response_schema = {
    "type": "object",
    "properties": {
        "card_token": {"type": "string", "description": "Token of the card that was deleted."},
        "card_reference": {"type": "string", "description": "Reference of the card that was deleted."},
        "deleted": {"type": "boolean", "description": "Whether the card was successfully deleted."}
    },
    "required": ["card_token", "deleted"]
}

update_card_response_schema = {
    "type": "object",
    "properties": {
        "card_token": {"type": "string", "description": "Token of the card that was updated."},
        "user_message": {"type": "string", "description": "Message describing the result of the operation."},
        "status": {"type": "string", "description": "Status of the update operation."}
    },
    "required": ["card_token", "status"]
}

card_info_response_schema = {
    "type": "object",
    "properties": {
        "country": {"type": "string", "description": "Country that issued the card."},
        "extended_card_type": {"type": "string", "description": "Extended card type information."},
        "brand": {"type": "string", "description": "Card brand (e.g., 'VISA', 'MASTERCARD')."},
        "juspay_bank_code": {"type": "string", "description": "Juspay's internal code for the bank."},
        "object": {"type": "string", "description": "Object type, typically 'cardbin'."},
        "id": {"type": "string", "description": "BIN number."},
        "card_sub_type": {"type": "string", "description": "Card subtype (e.g., 'PLATINUM', 'GOLD')."},
        "type": {"type": "string", "description": "Card type (e.g., 'CREDIT', 'DEBIT')."},
        "bank": {"type": "string", "description": "Bank that issued the card."}
    },
    "required": ["id", "brand", "type", "bank"]
}

bin_list_response_schema = {
    "type": "object",
    "properties": {
        "bins": {
            "type": "array",
            "description": "List of BIN numbers that are eligible.",
            "items": {"type": "string"}
        }
    },
    "required": ["bins"]
}

saved_payment_methods_response_schema = {
    "type": "object",
    "properties": {
        "saved_payment_methods": {
            "type": "object",
            "properties": {
                "payment_method_details": {
                    "type": "object",
                    "properties": {
                        "UPI_COLLECT": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "count": {"type": "integer", "description": "Number of times this VPA was used."},
                                    "last_used": {"type": "string", "format": "date-time", "description": "When the VPA was last used."},
                                    "vpa": {"type": "string", "description": "UPI Virtual Payment Address."}
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "required": ["saved_payment_methods"]
}

upi_collect_response_schema = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string", "description": "Order identifier."},
        "txn_id": {"type": "string", "description": "Transaction identifier."},
        "status": {"type": "string", "description": "Status of the transaction (e.g., 'PENDING_VBV')."},
        "payment": {
            "type": "object",
            "properties": {
                "authentication": {
                    "type": "object",
                    "properties": {
                        "method": {"type": "string", "description": "HTTP method to use for payment page."},
                        "url": {"type": "string", "description": "URL to redirect for payment."}
                    }
                }
            }
        }
    },
    "required": ["order_id", "txn_id", "status", "payment"]
}

verify_vpa_response_schema = {
    "type": "object",
    "properties": {
        "vpa": {"type": "string", "description": "UPI Virtual Payment Address that was verified."},
        "status": {"type": "string", "description": "Status of the VPA (e.g., 'VALID', 'INVALID')."},
        "mandate_details": {
            "type": "object",
            "properties": {
                "is_handle_supported": {"type": "boolean", "description": "Whether mandate is supported on this VPA."}
            }
        },
        "customer_name": {"type": "string", "description": "Name of the customer associated with the VPA."}
    },
    "required": ["vpa", "status"]
}

upi_intent_response_schema = {
    "type": "object",
    "properties": {
        "txn_uuid": {"type": "string", "description": "Unique transaction identifier."},
        "txn_id": {"type": "string", "description": "Transaction identifier."},
        "status": {"type": "string", "description": "Status of the transaction (e.g., 'PENDING_VBV')."},
        "payment": {
            "type": "object",
            "properties": {
                "sdk_params": {
                    "type": "object",
                    "properties": {
                        "tr": {"type": "string", "description": "Transaction reference."},
                        "tid": {"type": "string", "description": "Transaction ID."},
                        "merchant_vpa": {"type": "string", "description": "Merchant's UPI VPA."},
                        "merchant_name": {"type": "string", "description": "Merchant name."},
                        "mcc": {"type": "string", "description": "Merchant category code."},
                        "amount": {"type": "string", "description": "Amount of the transaction."}
                    }
                },
                "authentication": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to redirect for payment."},
                        "method": {"type": "string", "description": "HTTP method to use for payment page."}
                    }
                }
            }
        },
        "order_id": {"type": "string", "description": "Order identifier."}
    },
    "required": ["txn_id", "status", "payment", "order_id"]
}

list_offers_response_schema = {
    "type": "object",
    "properties": {
        "offers": {
            "type": "array",
            "description": "List of available offers.",
            "items": {
                "type": "object",
                "properties": {
                    "offer_rules": {"type": "object", "description": "Rules defining when the offer applies."},
                    "order_breakup": {
                        "type": "object",
                        "description": "Breakdown of order amount after offer application.",
                        "properties": {
                            "final_order_amount": {"type": "string", "description": "Final amount after offer application."},
                            "offer_amount": {"type": "string", "description": "Total offer amount."},
                            "order_amount": {"type": "string", "description": "Original order amount."},
                            "applicable_order_amount": {"type": "string", "description": "Amount eligible for offer."},
                            "discount_amount": {"type": "string", "description": "Discount amount."},
                            "benefits": {"type": "array", "description": "Details of benefits provided by the offer."}
                        }
                    },
                    "offer_id": {"type": "string", "description": "Unique identifier for the offer."},
                    "status": {"type": "string", "description": "Offer eligibility status (e.g., 'ELIGIBLE')."},
                    "offer_code": {"type": "string", "description": "Offer code."},
                    "eligible_saved_payment_methods": {"type": "array", "description": "Payment methods eligible for this offer."}
                }
            }
        },
        "best_offer_combinations": {
            "type": "array",
            "description": "Best combinations of offers that can be applied together."
        }
    }
}

offer_order_status_response_schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "description": "Order status (e.g., 'CHARGED')."},
        "id": {"type": "string", "description": "Juspay's unique identifier for the order."},
        "order_id": {"type": "string", "description": "Merchant's order identifier."},
        "amount": {"type": "number", "description": "Order amount."},
        "offers": {
            "type": "array",
            "description": "Applied offers for this order.",
            "items": {
                "type": "object",
                "properties": {
                    "offer_id": {"type": "string", "description": "Unique identifier for the offer."},
                    "offer_code": {"type": "string", "description": "Offer code."},
                    "status": {"type": "string", "description": "Offer application status (e.g., 'AVAILED')."},
                    "benefits": {"type": "array", "description": "Benefits provided by this offer."}
                }
            }
        },
        "effective_amount": {"type": "number", "description": "Effective amount after offers."}
    }
}

list_wallets_response_schema = {
    "type": "object",
    "properties": {
      "list": {
        "type": "array",
        "description": "List of wallet accounts associated with the customer.",
        "items": {
          "type": "object",
          "properties": {
            "wallet": {
              "type": "string",
              "description": "Name of the wallet provider (e.g., 'MOBIKWIK', 'PAYTM')."
            },
            "token": {
              "type": "string",
              "description": "Token associated with the wallet account."
            },
            "last_refreshed": {
              "type": "string",
              "format": "date-time",
              "description": "Timestamp when the wallet information was last refreshed."
            },
            "juspay_bank_code": {
              "type": "string",
              "description": "Juspay's internal bank code for the wallet."
            },
            "object": {
              "type": "string",
              "description": "Type of the object, typically 'wallet_account'."
            },
            "id": {
              "type": "string",
              "description": "Unique identifier for the wallet account."
            },
            "current_balance": {
              "type": "number",
              "description": "Current balance available in the wallet."
            },
            "sub_details": {
              "type": "array",
              "description": "Detailed information about sub-accounts or payment methods within the wallet.",
              "items": {
                "type": "object",
                "properties": {
                  "payment_method": {
                    "type": "string",
                    "description": "Type of the payment method (e.g., 'PAYTM_POSTPAID')."
                  },
                  "payment_method_type": {
                    "type": "string",
                    "description": "Category of the payment method, typically 'WALLET'."
                  },
                  "last_refreshed": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Timestamp when the sub-account information was last refreshed."
                  },
                  "current_balance": {
                    "type": "number",
                    "description": "Current balance available in the sub-account."
                  }
                },
                "required": ["payment_method", "payment_method_type", "last_refreshed", "current_balance"]
              }
            },
            "linked": {
              "type": "boolean",
              "description": "Indicates whether the wallet is linked to the customer's account."
            }
          },
          "required": ["wallet", "token", "last_refreshed", "juspay_bank_code", "object", "id", "current_balance", "sub_details", "linked"]
        }
      },
      "offset": {
        "type": "integer",
        "description": "Offset used for pagination."
      },
      "count": {
        "type": "integer",
        "description": "Number of wallet accounts returned in the response."
      },
      "total": {
        "type": "integer",
        "description": "Total number of wallet accounts available."
      },
      "object": {
        "type": "string",
        "description": "Type of the response object, typically 'list'."
      }
    },
    "required": ["list", "offset", "count", "total"]
}
