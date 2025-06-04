# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from juspay_dashboard_mcp.api.utils import post, get_juspay_host_from_api

logger = logging.getLogger(__name__)

async def list_emi_plans(payload: dict) -> dict:
    """
    Retrieves a list of EMI plans configured for a merchant.
    Response includes a list of EMI plans with plan details like tenure, payment method, gateway, interest rate, min and max amount (operating range), bank name (bankCode), card type (CREDIT/DEBIT), emi type (Standard_EMI/NO_COST/LOW_COST).
    Filters include: emiType, gateway, bankCode, tenure, cardType, disabled (plan status).
    """
    host = await get_juspay_host_from_api()
    api_url = f"{host}/ec/v1/emiPlans/list"
    
    logger.info(f"Listing EMI plans with payload: {payload} to URL: {api_url}")
    
    # The 'post' utility already handles common headers and converting payload to JSON
    response = await post(api_url, payload)
    return response
