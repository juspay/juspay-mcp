# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

from typing import Dict, Any
import time
import logging
import os
import json
from google.oauth2.credentials import Credentials

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


async def rag_tool_juspay(payload: dict, meta_info: dict = None) -> dict:
    """
    Query the RAG (Retrieval Augmented Generation) system using Vertex AI.

    This function provides intelligent document retrieval and question answering
    capabilities using Google's Vertex AI RAG system.

    Expected payload structure:
    {
        "query": "The question to ask the RAG system",
        "similarity_top_k": 20  # Optional: Number of similar documents to retrieve
    }

    Args:
        payload: Dictionary containing the query and optional parameters
        meta_info: Optional metadata information

    Returns:
        dict: The parsed response containing:
            - response: The generated answer
            - query: The original query
            - model: The model used
            - sources: List of source URLs
            - metrics: Performance metrics (optional)

    Raises:
        Exception: If the RAG query fails or required parameters are missing.
    """

    query = payload.get("query")
    if not query:
        raise ValueError("Query parameter is required in payload")

    similarity_top_k = payload.get("similarity_top_k", 20)
    include_metrics = payload.get("include_metrics", True)

    model = "gemini-2.5-flash-lite-preview-06-17"
    total_start_time = time.time()

    try:
        client_start_time = time.time()

        credentials = None
        adc_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if adc_json:
            cred_info = json.loads(adc_json)
            credentials = Credentials(
                token=None,
                refresh_token=cred_info["refresh_token"],
                id_token=None,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=cred_info["client_id"],
                client_secret=cred_info["client_secret"],
                quota_project_id=cred_info["quota_project_id"],
            )

        client = genai.Client(
            vertexai=True,
            project="genius-dev-393512",
            location="global",
            credentials=credentials,
        )
        client_init_time = time.time() - client_start_time
        logger.debug(f"Client initialization took {client_init_time:.3f} seconds")

        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=query)]),
        ]

        tools = [
            types.Tool(
                retrieval=types.Retrieval(
                    vertex_rag_store=types.VertexRagStore(
                        rag_resources=[
                            types.VertexRagStoreRagResource(
                                rag_corpus="projects/genius-dev-393512/locations/us-central1/ragCorpora/2305843009213693952"
                            )
                        ],
                        similarity_top_k=similarity_top_k,
                    )
                )
            )
        ]

        generate_content_config = types.GenerateContentConfig(tools=tools)

        generation_start_time = time.time()
        first_chunk_time = None
        chunk_count = 0
        response_text = ""
        grounding_metadata = None

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if first_chunk_time is None:
                first_chunk_time = time.time() - generation_start_time

            chunk_count += 1

            if chunk.candidates and chunk.candidates[0].grounding_metadata:
                grounding_metadata = chunk.candidates[0].grounding_metadata

            if (
                not chunk.candidates
                or not chunk.candidates[0].content
                or not chunk.candidates[0].content.parts
            ):
                continue

            chunk_text = chunk.text
            response_text += chunk_text

        total_generation_time = time.time() - generation_start_time
        total_execution_time = time.time() - total_start_time

        metrics = {
            "client_init_time": client_init_time,
            "time_to_first_chunk": first_chunk_time,
            "total_generation_time": total_generation_time,
            "total_execution_time": total_execution_time,
            "chunk_count": chunk_count,
            "response_length": len(response_text),
            "avg_chunks_per_second": (
                chunk_count / total_generation_time if total_generation_time > 0 else 0
            ),
            "avg_chars_per_second": (
                len(response_text) / total_generation_time
                if total_generation_time > 0
                else 0
            ),
        }

        logger.info(
            f"RAG query completed in {total_execution_time:.3f}s, {chunk_count} chunks, {len(response_text)} chars"
        )

        source_urls = []
        if grounding_metadata and hasattr(grounding_metadata, "grounding_chunks"):
            for chunk in grounding_metadata.grounding_chunks:
                if hasattr(chunk, "retrieved_context") and hasattr(
                    chunk.retrieved_context, "uri"
                ):
                    uri = chunk.retrieved_context.uri
                    if uri and uri not in source_urls:
                        source_urls.append(uri)

        result = {
            "response": response_text,
            "query": query,
            "model": model,
            "sources": source_urls,
        }

        if include_metrics:
            result["metrics"] = metrics
        
        return result

    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}")
        raise Exception(f"Failed to execute RAG query: {str(e)}")
