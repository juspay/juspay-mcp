from typing import List, Optional
from pydantic import BaseModel, Field
from juspay_dashboard_mcp.api_schema.headers import WithHeaders


class JuspayGetMerchantProductsPayload(WithHeaders):
    """Payload for getting merchant products from token validation"""

    token: str = Field(
        ...,
        description="The token to validate (e.g., '007c86261ae450cb428f8940888e55')",
    )


class MerchantProductRequest(WithHeaders):
    """Request for fetching merchant products."""

    merchant_id: str


class MerchantProductResponse(WithHeaders):
    """Response containing merchant products."""

    products: List[str]


class JuspayDiscoverDocsPayload(WithHeaders):
    """Payload for discovering relevant documentation"""

    query: str = Field(
        ...,
        description="User's question about technical documentation or product features",
    )
    products: List[str] = Field(
        ...,
        description="List of product slugs to search (e.g., ['Hypercheckout', 'Echeadless'])",
    )
    k: Optional[int] = Field(
        15, description="Maximum number of documents to return (default: 15, max: 50)"
    )


class JuspayReadDocPayload(WithHeaders):
    """Payload for reading full documentation content"""

    urls: List[str] = Field(
        ...,
        description="List of Juspay documentation URLs to fetch and convert to markdown",
    )


class DocSummary(WithHeaders):
    """Document summary with relevance score and URL."""

    url: str
    summary: str
    score: float


class DocDiscoveryRequest(WithHeaders):
    """Request structure for document discovery."""

    query: str
    products: List[str]
    k: Optional[int] = 15


class DocDiscoveryResponse(WithHeaders):
    """Response structure for document discovery."""

    docs: List[DocSummary]


class ReadDocRequest(WithHeaders):
    """Request for reading documents."""

    urls: List[str]


class ReadDocResponse(WithHeaders):
    """Response containing document contents in markdown."""

    markdown: List[str]
