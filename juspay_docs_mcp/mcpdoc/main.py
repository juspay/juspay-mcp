# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import os
import re
from typing import Annotated, Any, Literal, Optional
from pydantic import Field
from urllib.parse import urlparse, urljoin

import httpx
from markdownify import markdownify
from mcp.server.fastmcp import FastMCP
from typing_extensions import NotRequired, TypedDict


class DocSource(TypedDict):
    """A source of documentation for a library or a package."""

    name: NotRequired[str]
    """Name of the documentation source (optional)."""

    llms_txt: str
    """URL to the llms.txt file or documentation source."""

    description: NotRequired[str]
    """Description of the documentation source (optional)."""


def extract_domain(url: str) -> str:
    """Extract domain from URL.

    Args:
        url: Full URL

    Returns:
        Domain with scheme and trailing slash (e.g., https://example.com/)
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _is_http_or_https(url: str) -> bool:
    """Check if the URL is an HTTP or HTTPS URL."""
    return url.startswith(("http:", "https:"))


def _get_fetch_description(has_local_sources: bool) -> str:
    """Get fetch docs tool description."""
    description = [
        "Fetch and parse documentation from a given URL or local file.",
        "",
        "Use this tool after list_doc_sources to:",
        "1. First fetch the llms.txt file from a documentation source",
        "2. Analyze the URLs listed in the llms.txt file",
        "3. Then fetch specific documentation pages relevant to the user's question",
        "",
    ]

    if has_local_sources:
        description.extend(
            [
                "Args:",
                "    url: The URL or file path to fetch documentation from. Can be:",
                "        - URL from an allowed domain",
                "        - A local file path (absolute or relative)",
                "        - A file:// URL (e.g., file:///path/to/llms.txt)",
            ]
        )
    else:
        description.extend(
            [
                "Args:",
                "    url: The URL to fetch documentation from.",
            ]
        )

    description.extend(
        [
            "",
            "Returns:",
            "    The fetched documentation content converted to markdown, or an error message",  # noqa: E501
            "    if the request fails or the URL is not from an allowed domain.",
        ]
    )

    return "\n".join(description)


def _normalize_path(path: str) -> str:
    """Accept paths in file:/// or relative format and map to absolute paths."""
    return (
        os.path.abspath(path[7:])
        if path.startswith("file://")
        else os.path.abspath(path)
    )


def _get_server_instructions(doc_sources: list[DocSource], server_instructions: str | None) -> str:
    """Generate server instructions with available documentation source names."""
    # Extract source names from doc_sources
    source_names = []
    for entry in doc_sources:
        if "name" in entry:
            source_names.append(entry["name"])
        elif _is_http_or_https(entry["llms_txt"]):
            # Use domain name as fallback for HTTP sources
            domain = extract_domain(entry["llms_txt"])
            source_names.append(domain.rstrip("/").split("//")[-1])
        else:
            # Use filename as fallback for local sources
            source_names.append(os.path.basename(entry["llms_txt"]))

    instructions = [
        "Use the list_doc_sources tool to see available documentation sources.",
        "Pass the platform, clientId, merchantId and integrationType to get relevant documentation source URLs or file paths.",
        "It's CRITICAL for you to ask for clientId, merchantId and integrationType to get the most relevant documentation source.",
        "DO NOT PASS ANY PLACEHOLDERS for clientId, merchantId and integrationType, ALWAYS ASK THE USER TO PROVIDE ACTUAL VALUES.",
        "This tool will return a URL for each documentation source.",
    ]

    if source_names:
        if len(source_names) == 1:
            instructions.append(
                f"Documentation URLs are available from this tool "
                f"for {source_names[0]}."
            )
        else:
            names_str = ", ".join(source_names[:-1]) + f", and {source_names[-1]}"
            instructions.append(
                f"Documentation URLs are available from this tool for {names_str}."
            )

    instructions.extend(
        [
            "",
            "Once you have a source documentation URL, use the fetch_docs tool "
            "to get the documentation contents. ",
            "If the documentation contents contains a URL for additional documentation "
            "that is relevant to your task, you can use the fetch_docs tool to "
            "fetch documentation from that URL next.",
        ]
    )

    return "\n".join(instructions) + server_instructions


def create_server(
    doc_sources: list[DocSource],
    *,
    follow_redirects: bool = False,
    timeout: float = 10,
    settings: dict | None = None,
    allowed_domains: list[str] | None = None,
    server_instructions: str = "",
    transcripts_map: dict | None = None,
) -> FastMCP:
    """Create the server and generate documentation retrieval tools.

    Args:
        doc_sources: List of documentation sources to make available
        follow_redirects: Whether to follow HTTP redirects when fetching docs
        timeout: HTTP request timeout in seconds
        settings: Additional settings to pass to FastMCP
        allowed_domains: Additional domains to allow fetching from.
            Use ['*'] to allow all domains
            The domain hosting the llms.txt file is always appended to the list
            of allowed domains.

    Returns:
        A FastMCP server instance configured with documentation tools
    """
    settings = settings or {}
    server = FastMCP(
        name="llms-txt",
        instructions=_get_server_instructions(doc_sources, server_instructions),
        **settings,
    )
    httpx_client = httpx.AsyncClient(follow_redirects=follow_redirects, timeout=timeout)

    local_sources = []
    remote_sources = []

    for entry in doc_sources:
        url = entry["llms_txt"]
        if _is_http_or_https(url):
            remote_sources.append(entry)
        else:
            local_sources.append(entry)

    # Let's verify that all local sources exist
    for entry in local_sources:
        path = entry["llms_txt"]
        abs_path = _normalize_path(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Local file not found: {abs_path}")

    # Parse the domain names in the llms.txt URLs and identify local file paths
    domains = set(extract_domain(entry["llms_txt"]) for entry in remote_sources)

    # Add additional allowed domains if specified, or set to '*' if we have local files
    if allowed_domains:
        if "*" in allowed_domains:
            domains = {"*"}  # Special marker for allowing all domains
        else:
            domains.update(allowed_domains)

    allowed_local_files = set(
        _normalize_path(entry["llms_txt"]) for entry in local_sources
    )

    @server.tool()
    def list_doc_sources(
        platform: Annotated[
            Literal["android", "ios", "react_native", "flutter", "web"],
            Field(description="The platform for which documentation is requested, e.g., android, ios, react_native, web, this can be platform where Juspay SDKs are being integrated"),
        ],
        client_id: Annotated[
            str,
            Field(description="The client identifier for the merchant, merchants can get this from their Juspay dashboard"),
        ],
        merchant_id: Annotated[
            str,
            Field(description="The merchant identifier for the merchant, merchants can get this from their Juspay dashboard"),
        ],
        integration_type: Annotated[
            Literal["payment-page-cat", "payment-page-signature", "express-checkout", "api"],
            Field(description="The type of integration being used, options: payment-page-cat: Juspay Payment Page with Client Auth Token (CAT) based authentication, payment-page-signature: Juspay Payment Page with Signature based authentication, express-checkout: Juspay Express Checkout (Headless SDK), api: Juspay Server-to-Server API integration, only for backend"),
        ],
        ec_flow: Annotated[
            Optional[
                Literal["payment-options", "cards", "upi", "wallets", "netbanking", "native-otp", "juspay-safe", "cred-checkout", "consumer-finance", "enach"]
            ],
            Field(description="Required only for express-checkout flows or if integrationType is express-checkout, specify the express checkout flow for which documentation is requested, options: payment-options, cards, upi, wallets, netbanking, native-otp, juspay-safe, cred-checkout, consumer-finance, enach"),
        ] = None
    ) -> str:
        """
        List all available documentation sources.
        Important: Always ask the user to provide actual values for clientId, merchantId, and integrationType, DO NOT PASS ANY PLACEHOLDERS.
        You can ask user which screen they want to integrate Juspay SDKs on, and also which screen they want to initiate juspay SDK and which screen they want to process payment on. Try to be as explicit as possible to get the correct context.
        Ask questions step by step, don't assume anything. Do not ask all questions in a single message.

        If you need any auth token or signature generation details, ALWAYS ask the user to provide those details. And ASK them if they want a mock data, if they want, you can put anything in that field. 
        Make sure payloads are complete with all required fields, even if some fields have mock data.

        This is the first tool you should call in the Juspay documentation workflow.
        It provides URLs to llms.txt files or local file paths for each of juspay integrations like payment page, express checkout (ec), Global API reference etc.

        For subsequent calls to fetch_docs, use the URLs or file paths returned by this tool. DO NOT assume any URLs, always use the URLs provided by this tool or llms.txt.

        Always ask for ecFlow if integrationType is express-checkout, to get the most relevant documentation source. This is critical step as it helps determine which instrument they want to integrate. DO NOT proceed if no ecFlow is provided in case of integrationType is express-checkout.

        Guidelines:
        - Always ask for platform, clientId, merchantId and integrationType to get the most relevant documentation source.
        - DO NOT PASS ANY PLACEHOLDERS for clientId, merchantId and integrationType, ALWAYS ASK THE USER TO PROVIDE ACTUAL VALUES.
        - If integrationType is express-checkout, ALWAYS ask for ecFlow to get the most relevant documentation source.
        - It's important to note that while mocking also, you can never mock client id and merchant id. These are unique identifiers assigned to each merchant by Juspay and are essential for processing payments and identifying the merchant's account within the Juspay system.
        - You can only mock data in payloads like amount, order id, customer details, payment method details etc. But client id and merchant id must always be valid and correspond to an actual merchant account in Juspay's system.
        
        Args:
            platform: The platform for which documentation is requested (android, ios, react_native, web)
            clientId: The client identifier for the merchant
            merchantId: The merchant identifier
            integrationType: The type of integration (payment-page-cat, payment-page-signature, express-checkout, api)
                payment-page-cat: Juspay Payment Page with Client Auth Token (CAT) based authentication
                payment-page-signature: Juspay Payment Page with Signature based authentication
                express-checkout: Juspay Express Checkout (Headless SDK)
                api: Juspay Server-to-Server API integration, only for backend
            ecFlow: (Optional) Required only for express-checkout flows, specify the express checkout flow for which documentation is requested
        Returns:
            A string containing a formatted list of documentation sources with their URLs or file paths
        """

        content = f"""
        Use below for replacing placeholders:
        clientId: {client_id}
        merchantId: {merchant_id}
        Try finding the most relevant documentation source based on the platform (e.g., Android, iOS, Web), integration type (e.g., payment-page, express-checkout, api), and merchantId provided.
        Integration type provided: {integration_type}
        EC Flow provided: {ec_flow}
        """
        for entry_ in doc_sources:
            url_or_path = entry_["llms_txt"]

            if _is_http_or_https(url_or_path):
                name = entry_.get("name", extract_domain(url_or_path))
                content += f"{name}\nURL: {url_or_path}\n\n"
            else:
                path = _normalize_path(url_or_path)
                name = entry_.get("name", path)
                content += f"{name}\nPath: {path}\n\n"
        return content

    fetch_docs_description = _get_fetch_description(
        has_local_sources=bool(local_sources)
    )

    validate_integration_tool_description = """
        Validate your Juspay integration with this tool.
        This tool helps ensure that your integration is set up correctly and follows best practices.
        It checks for common issues and provides guidance on how to resolve them.
        Do not assume anything, always look for documentation to validate each step of the integration.
        Do not say that "it should be correct" without validating from documentation.
    """

    @server.tool(description=validate_integration_tool_description)
    async def validate_integration(
        platform: Annotated[
            Literal["android", "ios", "react_native", "flutter", "web", "backend"],
            Field(description="The platform for which validation is requested, e.g., android, ios, react_native, web, this can be platform where Juspay SDKs are being integrated"),
        ],
        clientId: Annotated[
            str,
            Field(description="The client identifier for the merchant, merchants can get this from their Juspay dashboard"),
        ],
        merchantId: Annotated[
            str,
            Field(description="The merchant identifier for the merchant, merchants can get this from their Juspay dashboard"),
        ],
        integrationType: Annotated[
            Literal["payment-page-cat", "payment-page-signature", "express-checkout", "api"],
            Field(description="The type of integration being used, options: payment-page-cat: Juspay Payment Page with Client Auth Token (CAT) based authentication, payment-page-signature: Juspay Payment Page with Signature based authentication, express-checkout: Juspay Express Checkout (Headless SDK), api: Juspay Server-to-Server API integration, only for backend"),
        ],
    ) -> Any:
        """
        Validate your Juspay integration setup.

        Args:
            platform: The platform for which validation is requested (android, ios, react_native, web)
            clientId: The client identifier for the merchant
            merchantId: The merchant identifier
            integrationType: The type of integration (payment-page-cat, payment-page-signature, express-checkout, api)
        Returns:
            A string indicating the validation result and any issues found
        """

        response = f"""
        Validation for {integrationType} integration on {platform} platform:
        - Client ID: {clientId}
        - Merchant ID: {merchantId}

        CRITICAL: The steps given below are only guidelines, you MUST validate each step from the official Juspay documentation to ensure correctness. Do not assume anything without validating from documentation using the `list_doc_sources` and `fetch_docs` tools.
        Do not write any code snippets until you see the documentation using the `list_doc_sources` and `fetch_docs` tools.
        """
        
        payment_page_common_steps = [
            "Ensure that the Juspay SDK is correctly initialized with the clientId and merchantId, refer to documentation for exact code.",
            "Verify that the action in the process payload is set to \"paymentPage\", refer to documentation for exact code.",
            "Check the initiate and process payloads' service is \"in.juspay.hyperpay\", refer to documentation for exact code.",
            "Ensure that the callbacks are implemented to handle SDK responses, refer to documentation for exact code.",
            "Check that the payment page is loading without errors and that the callbacks are functioning as expected, refer to documentation for exact code.",
        ]

        payment_page_cat_common_steps = payment_page_common_steps + [
            "Ensure that the Client Auth Token (clientAuthToken) is generated correctly and included in the process payload, refer to documentation for exact code.",
            "Verify that the CAT generation logic follows Juspay's security guidelines, refer to documentation for exact code.",
        ]

        payment_page_signature_common_steps = payment_page_common_steps + [
            "Ensure that the signature is generated correctly using the merchant's private key and included in the process payload, refer to documentation for exact code.",
            "Verify that the signature generation logic follows Juspay's security guidelines, refer to documentation for exact code.",
        ]

        android_sdk_steps = [
            "Ensure juspay maven in allprojects -> repositories in project build.gradle, refer to documentation for exact code.",
            "Ensure that the Juspay Gradle Plugin is added in build.gradle, refer to documentation for exact code.",
        ]

        ios_sdk_steps = [
            "Verify whether Podfile has the Juspay specific code added from the documentation, refer to documentation for exact code.",
            "Ensure MerchantConfig.txt file is present with clientId in it in root project folder.",
        ]

        react_native_sdk_steps = [
            "Ensure that the Juspay React Native SDK is installed and linked correctly, refer to documentation for exact code.",
        ] + [android_sdk_steps[0]] + ios_sdk_steps

        flutter_sdk_steps = [
            "Ensure that the Juspay Flutter SDK is added in pubspec.yaml, refer to documentation for exact code.",
        ] + [android_sdk_steps[0]] + ios_sdk_steps

        match integrationType:
            case "payment-page-cat" | "payment-page-signature":
                match platform:
                    case "android":
                        for idx, step in enumerate(android_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                        for idx, step in enumerate(
                            payment_page_cat_common_steps if integrationType == "payment-page-cat" else payment_page_signature_common_steps,
                            start=3
                        ):
                            response += f"{idx}. {step}\n"
                    case "react_native":
                        for idx, step in enumerate(react_native_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                        for idx, step in enumerate(
                            payment_page_cat_common_steps if integrationType == "payment-page-cat" else payment_page_signature_common_steps,
                            start=4
                        ):
                            response += f"{idx}. {step}\n"
                    case "ios":
                        for idx, step in enumerate(ios_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                        for idx, step in enumerate(
                            payment_page_cat_common_steps if integrationType == "payment-page-cat" else payment_page_signature_common_steps,
                            start=3
                        ):
                            response += f"{idx}. {step}\n"
                    case "flutter":
                        for idx, step in enumerate(flutter_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                        for idx, step in enumerate(
                            payment_page_cat_common_steps if integrationType == "payment-page-cat" else payment_page_signature_common_steps,
                            start=4
                        ):
                            response += f"{idx}. {step}\n"
                    case "web":
                        response += f"""
                        1. Ensure that the Juspay Web SDK script is included in your HTML, refer to documentation for exact code.
                        2. Verify that the SDK is initialized with the correct clientId and merchantId, refer to documentation for exact code.
                        3. Check that the payment page is loading without errors and that the callbacks are functioning as expected, refer to documentation for exact code.
                        """
                    case _:
                        return "Error: payment page integration is only valid for frontend platforms (android, ios, react_native, flutter, web)."
                pass
            case "express-checkout":
                match platform:
                    case "android":
                        for idx, step in enumerate(android_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                    case "react_native":
                        for idx, step in enumerate(react_native_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                    case "ios":
                        for idx, step in enumerate(ios_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                    case "flutter":
                        for idx, step in enumerate(flutter_sdk_steps, start=1):
                            response += f"{idx}. {step}\n"
                    case "web":
                        response += f"""
                        1. Ensure that the Juspay Web SDK script is included in your HTML, refer to documentation for exact code.
                        2. Verify that the SDK is initialized with the correct clientId and merchantId, refer to documentation for exact code.
                        3. Check that the payment options are loading without errors and that the callbacks are functioning as expected, refer to documentation for exact code.
                        """
                    case _:
                        return "Error: express-checkout integration is only valid for frontend platforms (android, ios, react_native, flutter, web)."
                response += "\n- Check for the service identifier in the initiate and process payloads is set to `in.juspay.hyperapi`, refer to documentation for exact code.\n"
                response += "\n- Refer to the docs of each ecFlow to validate specific steps for the chosen express checkout flow, refer to documentation for exact code.\n"
                pass
            case "api":
                response += """
                1. Ensure that the Juspay Server-to-Server API integration is set up correctly, refer to documentation for exact code.
                2. Verify that the API requests include the correct headers eg., x-merchantid, refer to documentation for exact code.
                3. Following APIs need to be there:
                - Customer Creation API
                - Session Creation API
                - Order Creation API
                - Payment Method APIs (Cards, UPI, Wallets, Netbanking etc. based on merchant requirement)
                - Payment Processing API
                4. For customer creation, ensure that customer_object_id is user identifier in your system, refer to documentation for exact code.
                5. Check that the API responses are handled correctly and that error handling is implemented as per documentation, refer to documentation for exact code.
                6. Ensure that the integration follows Juspay's security guidelines, refer to documentation for exact code.
                7. Webhooks:
                - Ensure that webhooks are set up to receive payment status updates, refer to documentation for exact code.
                - Verify that the webhook endpoints are secure and can handle incoming requests from Juspay, refer to documentation for exact code.
                - Do not assume webhook as source of truth without validating by calling the order status API, refer to documentation for exact code.
                8. Testing:
                - Test the integration in a sandbox environment before going live, refer to documentation for exact code.
                - Use test cards and payment methods provided by Juspay for testing purposes, refer to documentation for exact code.
                9. Finally, ensure that all required fields in the API requests are populated correctly and that the payloads conform to the specifications outlined in the documentation, refer to documentation for exact code.
                10. Always refer to the official Juspay API documentation for the most up-to-date information and best practices, refer to documentation for exact code.
                """
                pass
            case _:
                return "Error: Unknown integration type."
            
        response += "\n"
        response += """
        To see the documentation, use the list_doc_sources tool to get the relevant documentation source URL.
        Then find the relevant documentation page using the fetch_docs tool.

        CRITICAL: After fixing everything, run this `validate_integration` tool again to ensure everything is working as expected, if not reiterate.
        """

        response += """
        
        """

        return [
            {
                "type": "text",
                "text": response  # your long validation response string
            },
            {
                "type": "tool",
                "name": "list_doc_sources",
                "arguments": {}
            }
        ]

    @server.tool(description=fetch_docs_description)
    async def fetch_docs(url: str) -> str:
        nonlocal domains, follow_redirects
        url = url.strip()
        # Handle local file paths (either as file:// URLs or direct filesystem paths)
        if not _is_http_or_https(url):
            abs_path = _normalize_path(url)
            if abs_path not in allowed_local_files:
                raise ValueError(
                    f"Local file not allowed: {abs_path}. Allowed files: {allowed_local_files}"
                )
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return markdownify(content)
            except Exception as e:
                return f"Error reading local file: {str(e)}"
        else:
            # Otherwise treat as URL
            if "*" not in domains and not any(
                url.startswith(domain) for domain in domains
            ):
                return (
                    "Error: URL not allowed. Must start with one of the following domains: "
                    + ", ".join(domains)
                )

            try:
                response = await httpx_client.get(url, timeout=timeout)
                response.raise_for_status()
                content = response.text

                if follow_redirects:
                    # Check for meta refresh tag which indicates a client-side redirect
                    match = re.search(
                        r'<meta http-equiv="refresh" content="[^;]+;\s*url=([^"]+)"',
                        content,
                        re.IGNORECASE,
                    )

                    if match:
                        redirect_url = match.group(1)
                        new_url = urljoin(str(response.url), redirect_url)

                        if "*" not in domains and not any(
                            new_url.startswith(domain) for domain in domains
                        ):
                            return (
                                "Error: Redirect URL not allowed. Must start with one of the following domains: "
                                + ", ".join(domains)
                            )

                        response = await httpx_client.get(new_url, timeout=timeout)
                        response.raise_for_status()
                        content = response.text
                        
                if transcripts_map and url in transcripts_map:
                    content += "\n\n---\n\n" + transcripts_map[url]
                return markdownify(content)
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                return f"Encountered an HTTP error: {str(e)}"

    return server
