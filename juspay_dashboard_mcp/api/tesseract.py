# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import logging
from typing import List, Dict
from juspay_dashboard_mcp.api.utils import post
from juspay_dashboard_mcp.config import JUSPAY_BASE_URL
import json
import time
import requests
import tiktoken
import os
from typing import Optional, Tuple, Sequence

logger = logging.getLogger(__name__)

tiktokenenc = tiktoken.get_encoding("cl100k_base")

INTEGRATION_TYPE_MAPPING: Dict[str, List[str]] = {
    "PP": ["Hypercheckout"],
    "PL": ["Paymentlink"],
    "EC_API": ["Echeadless"],
    "EC_SDK": ["Echeadless"],
    "PF": ["Paymentforms"],
    "PAY_V3": ["Payv3"],
}


async def get_merchant_products_juspay(payload: dict) -> List[str]:
    """
    Get merchant products list by validating token and mapping integration types to products.
    """
    token = os.environ.get("JUSPAY_WEB_LOGIN_TOKEN")

    if not token:
        raise ValueError("JUSPAY_WEB_LOGIN_TOKEN environment variable is required")

    try:
        api_url = f"{JUSPAY_BASE_URL}/api/ec/v1/validate/token"
        request_payload = {"token": token}

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
        }

        token_response = await post(
            api_url, request_payload, additional_headers=headers
        )

        if not token_response:
            raise ValueError("No response received from token validation API")

        integration_types = token_response.get("integrationType", [])

        if not integration_types or not isinstance(integration_types, list):
            return []

        all_products = []

        for integration_type in integration_types:
            if integration_type in INTEGRATION_TYPE_MAPPING:
                products = INTEGRATION_TYPE_MAPPING[integration_type]
                all_products.extend(products)

        unique_products = list(dict.fromkeys(all_products))
        return unique_products

    except Exception as e:
        raise


def generate_v3_embeddings(text: str) -> Tuple[Sequence, int]:
    """Generate embeddings using Azure OpenAI text-embedding-3-large"""
    tokens = tiktokenenc.encode(text)

    if len(tokens) > 8191:
        raise Exception("Error: Text exceeds maximum token limit (8191 tokens).")

    endpoint_url = os.environ.get("AZURE_OPENAI_EMBEDDINGS_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_EMBEDDINGS_KEY")

    if not endpoint_url:
        raise Exception(
            "AZURE_OPENAI_EMBEDDINGS_ENDPOINT environment variable is required"
        )

    if not api_key:
        raise Exception("AZURE_OPENAI_EMBEDDINGS_KEY environment variable is required")

    headers = {"Content-Type": "application/json", "api-key": api_key}
    payload = {"input": [text]}

    try:
        response = requests.post(endpoint_url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        embeddings = data["data"][0]["embedding"]
        usage = data["usage"]["total_tokens"]

        return embeddings, usage

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to generate embeddings: {e}")
    except KeyError as e:
        raise Exception(f"Invalid response format: {e}")


def get_weaviate_client():
    """Initialize and return Weaviate client"""
    try:
        import weaviate

        weaviate_url = os.environ.get("WEAVIATE_ENDPOINT", "http://localhost:8080")
        api_key = os.environ.get("AZURE_OPENAI_EMBEDDINGS_KEY")

        client = weaviate.Client(
            url=weaviate_url,
            additional_headers=(
                {
                    "X-OpenAI-Api-Key": api_key,
                    "X-Azure-Api-Key": api_key,
                }
                if api_key
                else {}
            ),
        )

        if client.is_ready():
            try:
                schema = client.schema.get()
                return client
            except Exception as e:
                return None
        else:
            return None

    except ImportError as e:
        return None
    except Exception as e:
        return None


class WeaviateDocRetriever:
    """Weaviate-based document retriever"""

    def __init__(self, weaviate_client, product: str, k_value: int = 15):
        self.weaviate_client = weaviate_client
        self.product = product.replace("-", "").capitalize()
        self.k_value = k_value
        self.generate_query_vector = True
        self.only_chunks = False
        self.detected_platform = ["none"]

    def _get_docs(self, query: str, detected_platforms: List[str] = None) -> List[Dict]:
        """Retrieve documents from Weaviate"""
        from weaviate.gql.get import HybridFusion

        if detected_platforms:
            self.detected_platform = detected_platforms
        else:
            self.detected_platform = ["none"]

        query_vector = None
        if self.generate_query_vector:
            try:
                query_vector, _ = generate_v3_embeddings(query)
            except Exception as e:
                raise Exception(f"Failed to generate embeddings: {e}")

        if not query_vector:
            raise Exception("No query vector available for hybrid search")

        if self.detected_platform != ["none"]:
            response = (
                self.weaviate_client.query.get(
                    f"{self.product}_chunks",
                    ["text", "platform", "source", "parent_id"],
                )
                .with_where(
                    {
                        "operator": "Or",
                        "operands": [
                            {
                                "path": ["platform"],
                                "operator": "Equal",
                                "valueText": str(platform),
                            }
                            for platform in self.detected_platform
                        ],
                    }
                )
                .with_hybrid(
                    query=query,
                    alpha=0.75,
                    properties=["text", "processed_text"],
                    fusion_type=HybridFusion.RELATIVE_SCORE,
                    vector=query_vector,
                )
                .with_additional(["score"])
                .with_limit(self.k_value)
                .do()
            )
        else:
            response = (
                self.weaviate_client.query.get(
                    f"{self.product}_chunks" if not self.only_chunks else self.product,
                    (
                        ["text", "platform", "source", "parent_id"]
                        if not self.only_chunks
                        else ["text", "platform", "source"]
                    ),
                )
                .with_hybrid(
                    query=query,
                    alpha=0.75,
                    properties=["text", "processed_text"],
                    fusion_type=HybridFusion.RELATIVE_SCORE,
                    vector=query_vector,
                )
                .with_additional(["score"])
                .with_limit(self.k_value)
                .do()
            )

        if "data" in response:
            doc_chunks = (
                response["data"]["Get"][f"{self.product}_chunks"]
                if not self.only_chunks
                else response["data"]["Get"][self.product]
            )

            if not doc_chunks:
                return []

            parent_ids = []
            parent_objects = []

            if not self.only_chunks:
                for chunk in doc_chunks:
                    if chunk.get("parent_id") and chunk["parent_id"] not in parent_ids:
                        try:
                            parent_object = self.weaviate_client.data_object.get_by_id(
                                chunk["parent_id"], class_name=self.product
                            )
                            if parent_object is not None:
                                parent_objects.append(
                                    {
                                        **parent_object["properties"],
                                        "id": chunk["parent_id"],
                                        "chunk_score": chunk.get("_additional", {}).get(
                                            "score", 0.0
                                        ),
                                        "chunk_text": chunk.get("text", ""),
                                        "chunk_platform": chunk.get("platform", ""),
                                        "chunk_source": chunk.get("source", ""),
                                    }
                                )
                                parent_ids.append(chunk["parent_id"])
                        except Exception as e:
                            continue

                return parent_objects
            else:
                processed_chunks = [
                    {**chunk, "score": chunk.get("_additional", {}).get("score", 0.0)}
                    for chunk in doc_chunks
                ]
                return processed_chunks
        else:
            return []


def detect_platforms_from_query(query: str) -> List[str]:
    """
    Intelligently detect platforms from query content.
    """
    if not query:
        return ["android", "ios", "web"]

    query_lower = query.lower()
    detected_platforms = []

    platform_keywords = {
        "android": ["android", "kotlin", "java", "gradle", "apk", "sdk android"],
        "ios": [
            "ios",
            "swift",
            "objective-c",
            "xcode",
            "cocoapods",
            "sdk ios",
            "iphone",
            "ipad",
        ],
        "web": [
            "web",
            "javascript",
            "html",
            "css",
            "browser",
            "dom",
            "react",
            "vue",
            "angular",
            "sdk web",
        ],
    }

    for platform, keywords in platform_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            detected_platforms.append(platform)

    if not detected_platforms:
        detected_platforms = ["android", "ios", "web"]

    return detected_platforms


async def discover_docs_juspay(payload: dict) -> dict:
    """
    Search and retrieve relevant technical documentation for Juspay products.
    """
    query = payload.get("query")
    products = payload.get("products", [])
    k = payload.get("k", 15)

    if not query or not query.strip():
        return {"docs": [], "total_docs": 0, "error": "Query is required"}

    if not products or len(products) == 0:
        return {
            "docs": [],
            "total_docs": 0,
            "error": "At least one product is required",
        }

    try:
        weaviate_client = get_weaviate_client()
        if not weaviate_client:
            return {
                "docs": [],
                "total_docs": 0,
                "error": "Vector search service is unavailable. Please ensure Weaviate is running.",
            }

        k = int(k)
        k = min(max(k, 1), 50)

        all_docs = []
        detected_platforms = detect_platforms_from_query(query)

        for product in products:
            try:
                normalized_product = product.replace("-", "").capitalize()

                retriever = WeaviateDocRetriever(
                    weaviate_client=weaviate_client,
                    product=normalized_product,
                    k_value=k,
                )

                doc_results = retriever._get_docs(query, detected_platforms)

                for doc in doc_results:
                    try:
                        url = doc.get("source", "")
                        if not url or url == "None":
                            url = f"https://juspay.io/in/docs/{product.lower()}/android"

                        summary = doc.get(
                            "text", doc.get("chunk_text", "No summary available")
                        )
                        if len(summary) > 300:
                            summary = summary[:297] + "..."

                        score = float(doc.get("chunk_score", doc.get("score", 0.0)))

                        doc_summary = {
                            "url": url,
                            "summary": summary,
                            "score": score,
                            "product": product,
                            "platform": doc.get(
                                "chunk_platform", doc.get("platform", "")
                            ),
                        }

                        all_docs.append(doc_summary)

                    except Exception as e:
                        continue

            except Exception as e:
                continue

        all_docs.sort(key=lambda x: x["score"], reverse=True)
        all_docs = all_docs[:k]

        result = {
            "docs": all_docs,
            "total_docs": len(all_docs),
            "platforms_detected": detected_platforms,
            "products_searched": products,
            "query": query,
        }

        return result

    except Exception as e:
        return {
            "docs": [],
            "total_docs": 0,
            "error": f"Document discovery failed: {str(e)}",
        }


async def read_doc_juspay(payload: dict) -> dict:
    """
    Fetch and convert full documentation content from Juspay documentation URLs into readable markdown format.
    """
    urls = payload.get("urls", [])

    if not urls:
        return {
            "markdown": [],
            "total_docs": 0,
            "urls_processed": [],
            "errors": ["No URLs provided"],
        }

    markdown_contents = []
    urls_processed = []
    errors = []

    for url in urls:
        try:
            segments = url.split("/")
            product = segments[5] if len(segments) > 5 else None
            platform = segments[6] if len(segments) > 6 else None
            section = segments[7] if len(segments) > 7 else None
            step = segments[8] if len(segments) > 8 else None

            if product:
                try:
                    from juspay_dashboard_mcp.api.tiptap2md import (
                        convert_tiptap_to_markdown,
                    )

                    converted_docs = convert_tiptap_to_markdown(
                        product=product, platform=platform, section=section, step=step
                    )

                    if converted_docs:
                        doc_markdowns = [
                            doc.markdown
                            for doc in converted_docs
                            if hasattr(doc, "markdown")
                        ]

                        if doc_markdowns:
                            markdown = "\n\n---\n\n".join(doc_markdowns)
                            urls_processed.append(url)
                        else:
                            markdown = f"No valid markdown content found for {product}/{platform}/{section}/{step if step else ''}"
                            errors.append(f"No valid markdown content for URL: {url}")
                    else:
                        if step:
                            markdown = f"No documentation found for step '{step}' in {product}/{platform}/{section}."
                        elif section:
                            markdown = f"No documentation found for section '{section}' in {product}/{platform}."
                        elif platform:
                            markdown = f"No documentation found for platform '{platform}' in product '{product}'."
                        else:
                            markdown = (
                                f"No documentation found for product '{product}'."
                            )

                        errors.append(f"No content found for URL: {url}")

                except ImportError as e:
                    markdown = (
                        f"TipTap conversion module not available. Cannot process: {url}"
                    )
                    errors.append(f"TipTap module not found for URL: {url}")
                except Exception as e:
                    if step:
                        markdown = f"Error fetching documentation for {product}/{platform}/{section}/{step}: {str(e)}"
                    elif section:
                        markdown = f"Error fetching documentation for {product}/{platform}/{section}: {str(e)}"
                    elif platform:
                        markdown = f"Error fetching documentation for {product}/{platform}: {str(e)}"
                    else:
                        markdown = f"Error fetching documentation for product {product}: {str(e)}"

                    errors.append(f"Error processing {url}: {str(e)}")
            else:
                markdown = f"Could not extract product from URL: {url}"
                errors.append(f"Invalid URL format: {url}")

            markdown_contents.append(markdown)

        except Exception as e:
            error_msg = f"Failed to process URL {url}: {str(e)}"
            markdown_contents.append(error_msg)
            errors.append(error_msg)

    result = {
        "markdown": markdown_contents,
        "total_docs": len(markdown_contents),
        "urls_processed": urls_processed,
        "errors": errors,
        "success_count": len(urls_processed),
        "error_count": len(errors),
    }

    return result
