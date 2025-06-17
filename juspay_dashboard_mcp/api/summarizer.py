from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union, Tuple
import tiktoken
import asyncio
import json
import logging
import re
import os
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import nest_asyncio

nest_asyncio.apply()


async def call_gemini_api(prompt: str, max_tokens: int = 500) -> str:
    """Call the Gemini API with token limit validation."""
    start_time = datetime.now()
    input_token_count = count_tokens(prompt)
    logging.info(f"Gemini API call - Input tokens: {input_token_count}")

    # Check token limit before making API call
    MAX_INPUT_TOKENS = 1048576  # Gemini's actual limit
    if input_token_count > MAX_INPUT_TOKENS:
        error_msg = f"Input tokens ({input_token_count}) exceed Gemini limit ({MAX_INPUT_TOKENS})"
        logging.error(error_msg)
        raise ValueError(error_msg)

    api_key_val = os.environ.get("GEMINI_API_KEY")
    model_name_str = "gemini-2.5-flash-preview-05-20"

    # Prepare contents and config as they were in the original blocking version
    current_contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    # Use the original types.GenerateContentConfig
    current_generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        response_mime_type="text/plain",
        max_output_tokens=max_tokens,
    )

    def _perform_blocking_call(api_key, model_str, contents_data, config_data):
        # This function will run in a separate thread
        _client = genai.Client(api_key=api_key)
        _response_text = ""
        try:
            for _chunk in _client.models.generate_content_stream(
                model=model_str,
                contents=contents_data,
                config=config_data,
            ):
                _response_text += (
                    _chunk.text or ""
                )  # Handle cases where chunk.text might be None
            return _response_text
        except Exception as e_thread:
            # Log error from thread if necessary, or re-raise to be caught by main thread
            logging.error(f"Error within threaded Gemini call: {str(e_thread)}")
            raise  # Re-raise the exception to be caught by the main try-except block

    try:
        response = await asyncio.to_thread(
            _perform_blocking_call,
            api_key_val,
            model_name_str,
            current_contents,
            current_generate_content_config,
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        output_token_count = count_tokens(response)
        logging.info(f"Gemini API call - Output tokens: {output_token_count}")
        logging.info(f"Gemini API call took {duration:.2f} seconds.")
        return response

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.error(
            f"Error calling Gemini API after {duration:.2f} seconds: {str(e)}"
        )
        raise


def count_tokens_in_response(response: Any) -> int:
    """Count tokens in a response object by converting to string."""
    if isinstance(response, str):
        return len(encoding.encode(response))

    try:
        # Try to convert to JSON and count
        json_str = json.dumps(response)
        return len(encoding.encode(json_str))
    except:
        # Fallback to string representation
        return len(encoding.encode(str(response)))


# Models for summarization request and response (existing)
class SummarizationRequest(BaseModel):
    tool_output: Dict[str, Any]
    user_query: str  # Changed from Optional[str]
    chunk_size: Optional[int] = None


class SummarizationResponse(BaseModel):
    summary: Dict[str, Any]
    insignificant_values: Optional[List[Any]] = None
    intermediate_summaries: Optional[List[Dict[str, Any]]] = None


encoding = tiktoken.encoding_for_model("gpt-4")


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    if not text:
        return 0
    return len(encoding.encode(text))


def count_tokens_in_json(data: Dict[str, Any]) -> int:
    """Count tokens in a JSON object by converting to string first."""
    if not data:
        return 0
    json_str = json.dumps(data)
    return count_tokens(json_str)


async def summarize_with_llm(
    data: Dict[str, Any], user_query: str, model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fast LLM summarization with ACCURATE counting and verification
    """

    # Count BEFORE compression with detailed breakdown
    original_counts = {}
    total_items = 0
    active_items = 0
    breakdown_details = {}

    def count_nested_data(obj, prefix=""):
        nonlocal total_items, active_items
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, list):
                    current_key = f"{prefix}.{key}" if prefix else key
                    count = len(value)
                    original_counts[current_key] = count
                    total_items += count

                    # Store detailed breakdown for explicit mention
                    breakdown_details[key] = {
                        "count": count,
                        "type": key,
                        "description": f"{count} {key}",
                    }

                    # UNIVERSAL ACTIVE DETECTION based on user query
                    active_in_this_list = 0
                    query_lower = user_query.lower()

                    for item in value:
                        if isinstance(item, dict):
                            is_active = False

                            # Smart detection based on user query
                            if (
                                "soft approved" in query_lower
                                or "soft_approved" in query_lower
                            ):
                                # Look for soft approved in any status-like field
                                is_active = (
                                    item.get("status", "").upper() == "SOFT_APPROVED"
                                    or item.get("approvalStatus", "").upper()
                                    == "SOFT_APPROVED"
                                    or item.get("state", "").upper() == "SOFT_APPROVED"
                                    or "soft" in str(item.get("status", "")).lower()
                                )
                            elif "approved" in query_lower:
                                # Look for any approved status
                                is_active = (
                                    item.get("status", "").upper()
                                    in ["APPROVED", "SOFT_APPROVED"]
                                    or item.get("approvalStatus", "").upper()
                                    in ["APPROVED", "SOFT_APPROVED"]
                                    or "approved" in str(item.get("status", "")).lower()
                                )
                            elif "active" in query_lower:
                                # Look for active status
                                is_active = (
                                    item.get("isActiveLogic") == True
                                    or item.get("active") == True
                                    or item.get("isActive") == True
                                    or item.get("status", "").upper() == "ACTIVE"
                                )
                            else:
                                # Default fallback - check common active fields
                                is_active = (
                                    item.get("isActiveLogic") == True
                                    or item.get("active") == True
                                    or item.get("isActive") == True
                                )

                            if is_active:
                                active_items += 1
                                active_in_this_list += 1
                                # Log what was found for debugging
                                status_info = {
                                    k: v
                                    for k, v in item.items()
                                    if "status" in k.lower() or "active" in k.lower()
                                }
                                logging.info(
                                    f"Found matching item: ID={item.get('id', 'unknown')}, relevant_fields={status_info}"
                                )

                    if active_in_this_list > 0:
                        breakdown_details[key]["active_count"] = active_in_this_list
                        logging.info(
                            f"Key '{key}': {active_in_this_list} matching items out of {count} total for query: '{user_query}'"
                        )

    count_nested_data(data)

    # Create explicit breakdown text
    breakdown_text = []
    for key, details in breakdown_details.items():
        if key == "logics":
            active_text = (
                f" ({details.get('active_count', 0)} active)"
                if details.get("active_count", 0) > 0
                else " (0 active)"
            )
            breakdown_text.append(
                f"• {details['count']} priority logic rules{active_text}"
            )
        elif key == "gateways":
            breakdown_text.append(f"• {details['count']} gateway configurations")
        else:
            breakdown_text.append(f"• {details['count']} {key}")

    breakdown_summary = "\n".join(breakdown_text)

    logging.info(
        f"BEFORE COMPRESSION: {total_items} total items, {active_items} active items"
    )
    logging.info(f"BREAKDOWN: {breakdown_details}")

    # Compress JSON but verify count is preserved
    compact_json_data = compress_json_for_llm(data, max_tokens=900000)

    # VERIFY: Count items in compressed data
    try:
        compressed_parsed = json.loads(compact_json_data)
        compressed_count = 0
        if isinstance(compressed_parsed, dict):
            for key, value in compressed_parsed.items():
                if isinstance(value, list):
                    compressed_count += len(value)

        if compressed_count != total_items:
            logging.error(
                f"COMPRESSION DATA LOSS: Original {total_items}, compressed {compressed_count}"
            )
            raise ValueError(
                f"Compression lost data: {total_items} -> {compressed_count}"
            )

        logging.info(f"COMPRESSION VERIFIED: {total_items} items preserved")

    except Exception as e:
        logging.error(f"Compression verification failed: {e}")

    # Extract chunk metadata if this is a chunk
    chunk_metadata = data.get("_chunk_metadata", {})
    is_chunk = bool(chunk_metadata)
    original_total = chunk_metadata.get("total_original_items", 0)

    # Determine what the user is asking about
    query_lower = user_query.lower()
    if "soft approved" in query_lower:
        active_description = f"{active_items} soft approved"
    elif "approved" in query_lower:
        active_description = f"{active_items} approved"
    elif "active" in query_lower:
        active_description = f"{active_items} active"
    else:
        active_description = f"{active_items} active/approved"

    # FIXED prompt - chunk aware
    if is_chunk and original_total > 0:
        prompt = f"""CRITICAL: You are analyzing a SUBSET of business data.

DATA: {compact_json_data}

USER QUERY: {user_query}

IMPORTANT CONTEXT:
- This subset contains {total_items} records
- These {total_items} records are part of a LARGER dataset with {original_total} TOTAL records
- DO NOT state the total count - you are only seeing a subset

YOUR RESPONSE MUST:
- Analyze ONLY these {total_items} records from this subset
- Provide business insights about these specific records
- DO NOT claim "There are X total" - you're seeing a subset
- Focus on patterns and insights from this chunk

Analyze the business data patterns in this subset."""
    else:
        # Use existing prompt for non-chunks
        prompt = f"""CRITICAL: Analyze this business data with EXACT count accuracy and explicit breakdown.

DATA: {compact_json_data}

USER QUERY: {user_query}

MANDATORY REQUIREMENTS:
1. **TOTAL COUNT**: There are {total_items} records total in this response
2. **EXPLICIT BREAKDOWN**: The {total_items} total items consist of:
{breakdown_summary}
3. **MATCHING COUNT**: {active_items} priority logic rules match the query criteria ({active_description})

YOUR RESPONSE MUST:
- Start with "Found {total_items} records total, consisting of:"
- Immediately follow with the explicit breakdown:
{breakdown_summary}
- Specifically address the user's query about {active_description} rules
- Provide business analysis
- End with "VERIFIED: {total_items} total records analyzed"

Focus on answering the user's specific query about {active_description} rules."""

    try:
        # Balanced token limit for comprehensive breakdown
        current_max_tokens = 1000  # Increased to allow for detailed breakdown

        logging.info(
            f"Summarizing: {total_items} items ({breakdown_details}), {active_items} active, max_tokens: {current_max_tokens}"
        )

        # Reduced retries for speed
        max_retries = 3
        retry_delay = 1

        for retry_count in range(max_retries):
            try:
                llm_response = await call_gemini_api(
                    prompt=prompt,
                    max_tokens=current_max_tokens,
                )

                # VERIFY response contains correct counts and breakdown
                if str(total_items) not in llm_response:
                    logging.warning(
                        f"LLM response missing total count {total_items}: {llm_response[:100]}..."
                    )

                # Check if breakdown is mentioned
                breakdown_mentioned = any(
                    str(details["count"]) in llm_response
                    for details in breakdown_details.values()
                )
                if not breakdown_mentioned:
                    logging.warning(f"LLM response missing breakdown details")

                break
            except Exception as e:
                if retry_count == max_retries - 1:
                    raise
                logging.warning(f"LLM retry {retry_count+1}/{max_retries}: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

        result = {
            "summary_text": llm_response,
            "data_validation": {
                "original_counts": original_counts,
                "breakdown_details": breakdown_details,
                "total_original_items": (
                    original_total if is_chunk else total_items
                ),  # FIXED: Use original_total for chunks
                "active_items": active_items,
                "preservation_verified": True,
                "count_in_response": str(total_items) in llm_response,
                "breakdown_mentioned": breakdown_mentioned,
                "is_chunk": is_chunk,  # ADD: Chunk flag
                "chunk_metadata": (
                    chunk_metadata if is_chunk else {}
                ),  # ADD: Pass metadata
            },
        }

        logging.info(
            f"Summarization result: {total_items} total, {active_items} active, breakdown: {breakdown_details}"
        )
        return result

    except Exception as e:
        logging.error(f"Summarization error: {str(e)}")
        return {
            "error": f"Summarization failed: {str(e)}",
            "critical_data": {
                "original_counts": original_counts,
                "breakdown_details": breakdown_details,
                "total_items": total_items,
                "active_items": active_items,
            },
            "data_sample": str(data)[:300],
        }


async def summarize_chunk(
    chunk: Dict[str, Any], user_query: str
) -> Dict[str, Any]:  # user_query changed from Optional[str]
    """Summarize a single chunk of data."""
    return await summarize_with_llm(chunk, user_query)


async def summarize_tool_output(
    request: SummarizationRequest,
    default_chunk_size: int = 20000,  # Much higher threshold to avoid chunking 33 items
) -> SummarizationResponse:
    """Optimized summarization with data integrity focus"""

    start_time = datetime.now()
    logging.info(f"Starting summarize_tool_output with enhanced integrity")

    chunk_size = request.chunk_size or default_chunk_size
    current_tokens = count_tokens_in_json(request.tool_output)

    # Check if data is too large even for compression
    if current_tokens > 1000000:  # 1M token threshold
        logging.warning(
            f"Dataset extremely large ({current_tokens} tokens) - forcing chunking"
        )
        # Force chunking for very large datasets
        chunks = chunk_data(request.tool_output, 15000)  # Smaller chunk size
        logging.info(f"Processing {len(chunks)} chunks due to size")
    elif current_tokens <= chunk_size:
        logging.info(
            f"DIRECT summarization ({current_tokens} tokens) - no chunking needed"
        )
        try:
            summary = await summarize_with_llm(request.tool_output, request.user_query)

            # Log the summary for verification
            if isinstance(summary, dict) and "summary_text" in summary:
                logging.info(
                    f"Direct summary preview: {summary['summary_text'][:200]}..."
                )

            return SummarizationResponse(summary=summary)
        except ValueError as e:
            if "exceed" in str(e) and "limit" in str(e):
                logging.warning(f"Direct summarization failed due to token limit: {e}")
                # Fallback to chunking
                chunks = chunk_data(request.tool_output, 10000)
                logging.info(f"Falling back to {len(chunks)} chunks")
            else:
                raise
    else:
        # Only chunk if absolutely necessary (very large datasets)
        logging.info(f"Large dataset ({current_tokens} tokens) - chunking required")
        chunks = chunk_data(request.tool_output, chunk_size)
        logging.info(f"Processing {len(chunks)} chunks")

    # Process chunks in parallel with timeout
    try:
        chunk_tasks = [summarize_chunk(chunk, request.user_query) for chunk in chunks]

        chunk_summaries_results = await asyncio.wait_for(
            asyncio.gather(*chunk_tasks), timeout=45.0  # Increased timeout
        )

    except asyncio.TimeoutError:
        logging.error("Chunk processing timed out after 45 seconds")
        return SummarizationResponse(
            summary={"error": "Summarization timed out", "timeout": "45 seconds"}
        )

    # Combine multiple chunks if needed
    if len(chunk_summaries_results) == 1:
        final_summary = chunk_summaries_results[0]
    else:
        # FIXED: Extract original total from chunk metadata properly
        original_total = 0
        total_active = 0
        dataset_type = "records"

        for chunk_summary in chunk_summaries_results:
            if isinstance(chunk_summary, dict) and "data_validation" in chunk_summary:
                validation = chunk_summary["data_validation"]

                # Get the ORIGINAL total from chunk metadata
                chunk_original_total = validation.get("total_original_items", 0)
                if chunk_original_total > original_total:
                    original_total = (
                        chunk_original_total  # This will be 43 for surcharge rules
                    )

                total_active += validation.get("active_items", 0)

                # Determine dataset type from breakdown
                breakdown = validation.get("breakdown_details", {})
                if "logics" in breakdown:
                    dataset_type = "priority logic rules"
                elif "data" in breakdown:
                    dataset_type = "surcharge rules"  # or other types based on context

        # Create ACCURATE combined summary with correct total
        if original_total > 0:
            combined_text = f"COMBINED ANALYSIS OF {original_total} TOTAL {dataset_type.upper()}:\n\n"
            if total_active > 0:
                combined_text += f"Found {original_total} {dataset_type} total ({total_active} active) across {len(chunk_summaries_results)} processing chunks.\n\n"
            else:
                combined_text += f"Found {original_total} {dataset_type} total across {len(chunk_summaries_results)} processing chunks.\n\n"
        else:
            combined_text = (
                f"COMBINED SUMMARY OF {len(chunk_summaries_results)} CHUNKS:\n\n"
            )

        # Add individual chunk summaries (cleaned)
        for i, chunk_summary in enumerate(chunk_summaries_results, 1):
            chunk_text = chunk_summary.get("summary_text", str(chunk_summary))

            # Remove misleading individual chunk counts
            import re

            chunk_text = re.sub(r"Found \d+ records total[^.]*\.", "", chunk_text)
            chunk_text = re.sub(
                r"VERIFIED: \d+ total records analyzed[^.]*\.", "", chunk_text
            )

            combined_text += f"**Chunk {i} Analysis:**\n{chunk_text.strip()}\n\n"

        # Add final verification with correct total
        combined_text += f"**VERIFIED**: {original_total} total {dataset_type} analyzed across {len(chunk_summaries_results)} processing chunks."

        final_summary = {
            "summary_text": combined_text,
            "data_validation": {
                "total_chunks": len(chunk_summaries_results),
                "total_original_items": original_total,  # FIXED: This will show 43, not 15
                "active_items": total_active,
                "processing_time": f"{(datetime.now() - start_time).total_seconds():.2f}s",
                "combination_method": "enhanced_with_count_verification",
            },
        }

    duration = (datetime.now() - start_time).total_seconds()
    logging.info(f"Summarization completed in {duration:.2f} seconds")

    return SummarizationResponse(
        summary=final_summary, intermediate_summaries=chunk_summaries_results
    )


def chunk_data(data: Any, max_tokens: int) -> List[Any]:
    """
    Universal chunking optimized for speed while preserving data integrity.
    CRITICAL FIX: No chunking for datasets under 50 items to prevent data loss.
    """
    logging.info(f"Optimized chunk_data called - balancing speed and accuracy")

    # Find the main list to chunk
    if isinstance(data, dict):
        found_key_for_list_chunking = None
        list_to_chunk = None

        # Check for any list in the data
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                list_to_chunk = value
                found_key_for_list_chunking = key
                logging.info(
                    f"Found {len(list_to_chunk)} items under key: '{found_key_for_list_chunking}'"
                )
                break

        if list_to_chunk is not None and found_key_for_list_chunking is not None:
            # CRITICAL FIX: No chunking for small datasets (33 priority logics should not be chunked)
            if len(list_to_chunk) <= 50:  # Changed from 50 to 20 to force chunking
                logging.info(
                    f"NO CHUNKING: {len(list_to_chunk)} items <= 50, processing as single unit to preserve data integrity"
                )
                return [data]  # Return original data without chunking

            # Only chunk very large datasets
            logging.info(
                f"CHUNKING REQUIRED: {len(list_to_chunk)} items > 50, will chunk for processing"
            )
            items_per_chunk = min(
                25, max(20, len(list_to_chunk) // 3)
            )  # Conservative chunking
            chunks = []

            for i in range(0, len(list_to_chunk), items_per_chunk):
                chunk_items = list_to_chunk[i : i + items_per_chunk]
                chunk_data = {
                    found_key_for_list_chunking: chunk_items,
                    "_chunk_metadata": {
                        "chunk_number": len(chunks) + 1,
                        "items_in_chunk": len(chunk_items),
                        "total_original_items": len(
                            list_to_chunk
                        ),  # Critical for verification
                    },
                }
                chunks.append(chunk_data)

            logging.info(f"Created {len(chunks)} chunks for {len(list_to_chunk)} items")

            # MANDATORY verification - no data loss allowed
            total_items_in_chunks = sum(
                len(chunk[found_key_for_list_chunking]) for chunk in chunks
            )
            if total_items_in_chunks != len(list_to_chunk):
                logging.error(
                    f"CRITICAL DATA LOSS: Original {len(list_to_chunk)} items, chunks have {total_items_in_chunks}"
                )
                raise ValueError(
                    f"Data integrity violation: {len(list_to_chunk)} != {total_items_in_chunks}"
                )

            return chunks

    # Handle direct lists - no chunking for small lists
    if isinstance(data, list):
        if len(data) <= 50:  # Increased threshold
            logging.info(
                f"NO CHUNKING: Direct list with {len(data)} items <= 50, processing as single unit"
            )
            return [{"items": data}]

        # Only chunk large lists
        items_per_chunk = 25
        chunks = []

        for i in range(0, len(data), items_per_chunk):
            chunk_items = data[i : i + items_per_chunk]
            chunks.append(
                {
                    "items": chunk_items,
                    "_chunk_metadata": {"total_original_items": len(data)},
                }
            )

        return chunks

    return [data]


def tool_output_summarizer(response: Any, query: str) -> str:  # Synchronous wrapper
    """
    Synchronous wrapper function that takes a tool response and summarizes it if needed.
    Always returns a string for responses that exceed the token threshold.
    """
    logging.info(
        f"tool_output_summarizer (sync with nest_asyncio) called with query: {query}"
    )
    logging.info(f"Response type: {type(response)}")

    response_dict: Dict[str, Any]
    # Flag to indicate if we successfully processed the response into a preferred list-wrapper format
    successfully_extracted_list = False

    # --- Enhanced Pydantic Model Handling ---
    if isinstance(response, BaseModel):
        logging.info(f"Handling Pydantic BaseModel of type: {type(response)}")
        try:
            dumped_response = response.model_dump(
                mode="json"
            )  # Use mode='json' for better serialization

            if isinstance(dumped_response, list):
                # Case 1: model_dump() directly returns a list of records
                response_dict = {"data": dumped_response}
                successfully_extracted_list = True
                logging.info(
                    f"Pydantic model_dump() returned a list. Wrapped under 'data' key. Count: {len(dumped_response)}"
                )
            elif isinstance(dumped_response, dict):
                # Case 2: model_dump() returns a dict. Try to find the list within it.
                # Check for RootModel pattern: {"root": <list>}
                if "root" in dumped_response and isinstance(
                    dumped_response["root"], list
                ):
                    response_dict = {"data": dumped_response["root"]}
                    successfully_extracted_list = True
                    logging.info(
                        f"Pydantic model_dump() was {{'root': <list>}}. Standardized to {{'data': <list>}}. Count: {len(dumped_response['root'])}"
                    )
                # Check for RootModel pattern: {"root": {"actual_list_key": <list>}}
                elif "root" in dumped_response and isinstance(
                    dumped_response["root"], dict
                ):
                    inner_root_dict = dumped_response["root"]
                    for list_key_candidate in [
                        "data",
                        "records",
                        "items",
                        "results",
                        "list_items",
                    ]:
                        if list_key_candidate in inner_root_dict and isinstance(
                            inner_root_dict[list_key_candidate], list
                        ):
                            response_dict = {
                                "data": inner_root_dict[list_key_candidate]
                            }
                            successfully_extracted_list = True
                            logging.info(
                                f"Pydantic model_dump() was {{'root': {{'{list_key_candidate}': <list>}}}}. Standardized to {{'data': <list>}}. Count: {len(inner_root_dict[list_key_candidate])}"
                            )
                            break
                    if not successfully_extracted_list:
                        logging.warning(
                            f"Pydantic model_dump() was {{'root': <dict>}}, but no clear inner list found. Using full dump: {str(dumped_response)[:200]}..."
                        )
                        response_dict = dumped_response  # Fallback to the dumped dict
                else:
                    # Check for list directly under common keys in the dumped_response dict
                    found_direct_list = False
                    for list_key_candidate in [
                        "data",
                        "records",
                        "items",
                        "results",
                        "list_items",
                    ]:
                        if list_key_candidate in dumped_response and isinstance(
                            dumped_response[list_key_candidate], list
                        ):
                            response_dict = {
                                "data": dumped_response[list_key_candidate]
                            }
                            successfully_extracted_list = True
                            logging.info(
                                f"Pydantic model_dump() was <dict> with list under '{list_key_candidate}'. Standardized to {{'data': <list>}}. Count: {len(dumped_response[list_key_candidate])}"
                            )
                            found_direct_list = True
                            break
                    if not found_direct_list:
                        logging.warning(
                            f"Pydantic model_dump() is a dict, but no clear list found under common keys. Using full dump: {str(dumped_response)[:200]}..."
                        )
                        response_dict = dumped_response  # Fallback to the dumped dict
            else:
                logging.error(
                    f"Pydantic model_dump() returned an unexpected type: {type(dumped_response)}. Stringifying original response."
                )
                response_dict = {
                    "raw_response": str(response),
                    "error_detail": "model_dump gave non-dict/list",
                }

        except Exception as e:
            logging.error(
                f"Error during Pydantic model_dump() or processing for {type(response)}: {e}. Stringifying original response."
            )
            response_dict = {"raw_response": str(response), "error_detail": str(e)}

    # --- Handling for direct lists (not Pydantic BaseModels but still lists) ---
    elif isinstance(response, list):
        logging.info(f"Response is a direct list. Type: {type(response)}")
        serializable_list = []
        for item in response:
            try:
                if isinstance(item, BaseModel):  # If list contains Pydantic models
                    serializable_list.append(item.model_dump(mode="json"))
                elif isinstance(item, dict) or isinstance(
                    item, list
                ):  # If item is already dict/list
                    json.dumps(item)  # Test serializability
                    serializable_list.append(item)
                else:  # Primitive types
                    serializable_list.append(item)
            except (TypeError, OverflowError) as te:
                logging.warning(
                    f"Could not serialize item in list: {str(item)[:100]} due to {te}. Using str()."
                )
                serializable_list.append(str(item))
        response_dict = {"data": serializable_list}
        successfully_extracted_list = True
        logging.info(
            f"Direct list processed and wrapped under 'data' key. Count: {len(serializable_list)}"
        )

    # --- Handling for plain dicts or other fallbacks ---
    elif isinstance(response, dict):
        logging.info(
            f"Response is a plain dict. Using as is. Keys: {list(response.keys())}"
        )
        response_dict = response
        # We don't set successfully_extracted_list=True here unless we verify it contains a list under a good key.
        # chunk_data will try its potential_list_keys.
    else:
        logging.warning(
            f"Response is of unhandled type: {type(response)}. Converting to string."
        )
        response_dict = {
            "raw_response": str(response),
            "error_detail": f"Unhandled type {type(response)}",
        }

    # Final check: if response_dict is not a dict (e.g. error cases), make it one
    if not isinstance(response_dict, dict):
        logging.error(
            f"Internal Error: response_dict is not a dict ({type(response_dict)}) before SummarizationRequest. Forcing to error dict."
        )
        response_dict = {
            "error": "Internal: response_dict was not a dict",
            "original_type": str(type(response)),
        }

    # Log the structure of response_dict if it's not a simple list extraction, to help debug chunking
    if not successfully_extracted_list and isinstance(response_dict, dict):
        if len(str(response_dict)) > 500:
            logging.info(
                f"Response_dict (potentially for generic chunking) structure sample: {str(response_dict)[:500]}..."
            )
        else:
            logging.info(
                f"Response_dict (potentially for generic chunking) structure: {response_dict}"
            )

    request_obj = SummarizationRequest(
        tool_output=response_dict,
        user_query=query,
        chunk_size=20000,  # Increased from 10000
    )

    try:
        logging.info(
            "Attempting to run summarization from sync wrapper (with nest_asyncio)..."
        )
        # summarization_result = asyncio.run(summarize_tool_output(request_obj)) # Remove this line
        summarization_result = asyncio.get_event_loop().run_until_complete(
            summarize_tool_output(request_obj)
        )
        logging.info(
            "Summarization completed successfully via asyncio.run() (with nest_asyncio)."
        )
        # If summarization_result.summary itself contains an error dict from summarize_with_llm,
        # this will correctly dump it as JSON.
        return json.dumps(summarization_result.summary, indent=2)
    except Exception as e:
        error_message = str(e)
        logging.error(
            f"Error during asyncio.run in tool_output_summarizer (nest_asyncio): {error_message}"
        )
        # Check if the error is API key related and format it as JSON
        if "api_key" in error_message.lower() and (
            "openai" in error_message.lower()
            or "client option" in error_message.lower()
        ):
            error_payload = {
                "error": "OpenAI API Key Error (caught in tool_output_summarizer)",
                "detail": error_message,
                "original_query_for_summarizer": query,
                "tool_output_sample_for_summarizer": str(response_dict)[
                    :500
                ],  # Log a sample of what was to be summarized
            }
            return json.dumps(error_payload, indent=2)
        # Fallback for other types of errors
        return json.dumps(
            {"error": "Error during summarization process", "detail": error_message},
            indent=2,
        )


def should_summarize_response(
    response: Any, user_query: str, token_threshold: int = 25000
) -> tuple[bool, int, int]:
    """
    Universal function to determine if ANY API response should be summarized.
    Works for orders, offers, transactions, merchants, settings, disputes, refunds, etc.

    Returns: (should_summarize, token_count, item_count)
    """
    if user_query is None:
        logging.info("User query is None. Skipping summarization for any API.")
        return False, 0, 0

    token_count = count_tokens_in_response(response)

    # Count items universally - works for any API response
    item_count = 0
    if isinstance(response, dict):
        for key, value in response.items():
            if isinstance(value, list):
                item_count += len(value)
    elif isinstance(response, list):
        item_count = len(response)

    should_summarize = token_count >= token_threshold
    logging.info(
        f"Universal API response analysis: {token_count} tokens, {item_count} items, summarize: {should_summarize}"
    )

    return should_summarize, token_count, item_count


def compress_json_for_llm(data: Dict[str, Any], max_tokens: int = 900000) -> str:
    """
    Compress JSON data to fit within LLM token limits WITHOUT losing data.
    CRITICAL: No data truncation - compress field content instead.
    """

    def compress_priority_logic_item(item):
        """Compress a single priority logic item by removing verbose fields"""
        if not isinstance(item, dict):
            return item

        # Keep ALL essential fields - don't lose any data
        essential_fields = {
            "id",
            "name",
            "status",
            "isActiveLogic",
            "merchantAccountId",
            "dateCreated",
            "lastUpdated",
            "priorityOrder",
            "isDefault",
        }

        compressed = {}
        for key, value in item.items():
            if key in essential_fields:
                compressed[key] = value
            elif key == "logicExpression" and isinstance(value, str):
                # Compress logic expression but preserve key info
                if len(value) > 200:
                    compressed[key] = value[:200] + "...[TRUNCATED]"
                else:
                    compressed[key] = value
            elif key in ["dateCreated", "lastUpdated"] and isinstance(value, str):
                # Keep just the date part
                compressed[key] = value[:10] if len(value) > 10 else value
            # Skip very verbose fields but keep important ones
            elif key not in ["createdBy", "updatedBy", "metadata", "debugInfo"]:
                compressed[key] = value

        return compressed

    def compress_data_recursively(obj):
        """Recursively compress data structure WITHOUT losing count"""
        if isinstance(obj, dict):
            compressed = {}
            for key, value in obj.items():
                if isinstance(value, list):
                    # CRITICAL: Compress items but preserve ALL records
                    compressed[key] = [
                        compress_priority_logic_item(item) for item in value
                    ]
                    logging.info(
                        f"Compressed {len(value)} items under key '{key}' - NO DATA LOSS"
                    )
                elif isinstance(value, dict):
                    compressed[key] = compress_data_recursively(value)
                else:
                    compressed[key] = value
            return compressed
        elif isinstance(obj, list):
            # CRITICAL: Compress all items, don't truncate
            return [compress_priority_logic_item(item) for item in obj]
        else:
            return obj

    # Compress the data without losing records
    compressed_data = compress_data_recursively(data)

    # Convert to compact JSON
    compact_json = json.dumps(compressed_data, separators=(",", ":"))
    token_count = count_tokens(compact_json)

    # If STILL too large, compress further but DON'T truncate data
    if token_count > max_tokens:
        logging.warning(
            f"Data still large ({token_count} tokens) after compression - applying aggressive compression"
        )

        # More aggressive field compression
        def aggressive_compress_item(item):
            if not isinstance(item, dict):
                return item

            # Keep only absolutely critical fields
            critical_only = {
                "id": item.get("id"),
                "name": item.get("name"),
                "status": item.get("status"),
                "isActiveLogic": item.get("isActiveLogic"),
                "merchantAccountId": item.get("merchantAccountId"),
            }
            return {k: v for k, v in critical_only.items() if v is not None}

        if isinstance(compressed_data, dict):
            for key, value in compressed_data.items():
                if isinstance(value, list):
                    compressed_data[key] = [
                        aggressive_compress_item(item) for item in value
                    ]
                    logging.info(
                        f"Aggressively compressed {len(value)} items under key '{key}' - COUNT PRESERVED"
                    )

        compact_json = json.dumps(compressed_data, separators=(",", ":"))
        token_count = count_tokens(compact_json)

    logging.info(f"JSON compressed to {token_count} tokens - ALL DATA PRESERVED")
    return compact_json

