# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayGetMerchantDetailsPayload(WithHeaders):
    """Return merchant and user details for the authenticated session.

    Takes no input arguments — Portal derives everything from the bearer
    token presented on the request.
    """
    pass
