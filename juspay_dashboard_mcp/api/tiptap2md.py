import requests, re, time, os, dotenv, tiktoken
import urllib.parse
from typing import List
import logging
import markdownify  

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dotenv.load_dotenv()


tesseract_endpoint = "https://juspay.io/in/docs"


class MarkdownDocument:
    def __init__(
        self,
        markdown: str,
        metadata: dict[str, str],
        filepath: str,
    ):
        self.markdown = markdown
        self.metadata = metadata
        self.filepath = filepath

    def __str__(self) -> str:
        markdown_preview = self.markdown[:40].replace("\n", "\\n") + "..."
        return f'MarkdownDocument(metadata={str(self.metadata)}, markdown="{markdown_preview}", filepath={self.filepath})'

    def save_to_file(
        self, base_directory_path="", add_metadata_frontmatter=True, file_path_prefix=""
    ) -> None:
        """
        Saves the markdown content of the document to the specified filepath.
        If the filepath is not specified, it will raise a ValueError.
        """
        if not self.filepath:
            raise ValueError("File path not specified.")
        if not self.markdown:
            raise ValueError("No markdown content to save.")

        file_text = self.markdown
        full_path = os.path.join(base_directory_path, file_path_prefix + self.filepath)

        enc = tiktoken.get_encoding("cl100k_base")

        if len(base_directory_path) > 0:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

        base_frontmatter = ""
        if add_metadata_frontmatter:
            metadata_text = [
                f"{metadata_item}: {self.metadata[metadata_item]}"
                for metadata_item in self.metadata
            ]
            base_frontmatter = "---\n" + "\n".join(metadata_text) + "\n---\n"

        file_text = base_frontmatter + file_text
        encoded = enc.encode(file_text)

        if len(encoded) > 8191:
            max_tokens = 8191 - len(enc.encode(base_frontmatter))

            heading_pattern = re.compile(r"^(#{1,4} .*)$", re.MULTILINE)

            headings = [
                (match.start(), match.group())
                for match in heading_pattern.finditer(self.markdown)
            ]

            chunks = []
            current_chunk = ""
            current_tokens = 0

            for i in range(len(headings)):
                start_pos, heading = headings[i]
                end_pos = (
                    headings[i + 1][0] if i + 1 < len(headings) else len(self.markdown)
                )

                section = self.markdown[start_pos:end_pos]
                section_tokens = len(enc.encode(section))

                if current_tokens + section_tokens > max_tokens:
                    chunks.append(current_chunk)
                    current_chunk = section
                    current_tokens = section_tokens
                else:
                    current_chunk += section
                    current_tokens += section_tokens

            if current_chunk:
                chunks.append(current_chunk)

            base_filename, ext = os.path.splitext(self.filepath)
            for i, chunk in enumerate(chunks):
                chunk_filename = f"{base_filename}_part{i+1}{ext}"
                chunk_path = os.path.join(
                    base_directory_path, file_path_prefix + chunk_filename
                )

                modified_metadata = self.metadata.copy()
                if "source" in modified_metadata:
                    modified_metadata["source"] += f"#{i+1}"

                modified_frontmatter = (
                    "---\n"
                    + "\n".join(
                        [f"{key}: {value}" for key, value in modified_metadata.items()]
                    )
                    + "\n---\n"
                )

                with open(chunk_path, "w", encoding="utf-8") as file:
                    file.write(modified_frontmatter + chunk)
                print(f"Chunk {i+1} saved to {chunk_filename}")
        else:
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(file_text)
            print(f"Document saved to {file_path_prefix + self.filepath}")


def tiptap_to_markdown(tiptap_json):
    """
    Converts a Tiptap JSON document to a Markdown string.

    Args:
        tiptap_json (str or dict): The Tiptap JSON document.

    Returns:
        str: The converted Markdown document.
    """
    #logger.info(f"Converting Tiptap JSON to Markdown: {tiptap_json}")
    content = tiptap_json["content"]
    return parse_tiptap_nodes(content)


def parse_tiptap_nodes(nodes, indent_level=0):
    """
    Recursively parses an array of Tiptap nodes and returns the corresponding Markdown.
    """
    markdown = ""
    for node in nodes:
        markdown += parse_tiptap_node(node, indent_level=indent_level)
    return markdown


def parse_tiptap_node(node, indent_level=0):
    """
    Parses a single Tiptap node and returns the corresponding Markdown.
    """
    if type(node) == str:
        print("IGNORING NODE", node)
        return ""
    node_type = node.get("type")

    if node_type == "doc":
        return parse_tiptap_nodes(node["content"]) if "content" in node else ""

    elif node_type == "paragraph":
        return (
            "\n" + parse_tiptap_nodes(node["content"])
            if "content" in node
            else "" + "\n"
        )

    elif node_type == "heading":
        level = node["attrs"]["level"]
        text = parse_tiptap_nodes(node["content"]) if "content" in node else ""
        return "\n" + "#" * level + " " + text + "\n\n"

    elif node_type in ["bulletList", "orderedList"]:
        items = parse_tiptap_nodes(node["content"]) if "content" in node else ""
        list_marker = "* " if node_type == "bulletList" else "1. "
        return "\n" + (
            "\n".join(
                list_marker + item
                for item in items.splitlines()
                if len(item.strip()) > 0
            )
            + "\n\n"
        )

    elif node_type == "listItem":
        return parse_tiptap_nodes(node["content"]) if "content" in node else "" + "\n"

    elif node_type == "text":
        return handle_marks(node.get("text", ""), node.get("marks", []))

    elif node_type == "hardBreak":
        return "\n"

    elif node_type == "API":
        return handle_api_node(node)

    elif node_type == "faq":
        return handle_faq_node(node)

    elif node_type == "hiddentext":
        return handle_hiddentext_node(node)

    elif node_type == "imageext":
        return handle_image_node(node)

    elif node_type == "note":
        return handle_note_node(node)

    elif node_type in ["videonode", "videoext"]:
        return handle_video_node(node)

    elif node_type == "snippet":
        return handle_snippet_node(node)

    elif node_type == "substep":
        return handle_substep_node(node)

    elif node_type == "tablenode":
        return handle_table_node(node)

    elif node_type == "payload":
        return handle_payload_node(node, indent_level=indent_level)

    elif node_type == "tabpayload":
        return handle_tabpayload_node(node)

    elif node_type == "htmlText":
        return node.get("htmlText", "")

    elif node_type == "image":
        return handle_image_node(node)

    else:
        return ""


def extract_snippet_block(content, block_id):
    # Use regex to extract the block of code based on blockId
    pattern = re.compile(
        rf"block:start:{block_id}\s*(.+?)block:end:{block_id}", re.DOTALL
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()


bitbucket_token = os.getenv("BITBUCKET_TOKEN")


def fetch_file_from_bitbucket(project_name: str, repo_name: str, file_path: str) -> str:
    headers = {"Authorization": f"Bearer {bitbucket_token}"}

    # Construct the new endpoint URL
    try:
        url = (
            f"https://bitbucket.juspay.net/rest/api/latest/projects/{project_name}/"
            f"repos/{repo_name}/browse/{file_path.split('/', 1)[1]}"
            f"?at=refs%2Fheads%2F{file_path.split('/', 1)[0]}&start=0&limit=20000"
        )
    except IndexError:
        url = (
            f"https://bitbucket.juspay.net/rest/api/latest/projects/{project_name}/"
            f"repos/{repo_name}/browse/{file_path}"
            f"?at=refs%2Fheads%2Fupiinapp&start=0&limit=20000"
        )

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("lines") and len(response_json["lines"]) > 0:
            file_content = "\n".join([line["text"] for line in response_json["lines"]])
            return file_content
    else:
        print(response.text)
        return ""


def parse_bitbucket_url(url: str) -> tuple[str, str]:
    """Parses a Bitbucket URL, extracting repository information and file path.

    Args:
        url: The Bitbucket repository URL.

    Returns:
        A tuple containing: (repository_url, file_path)
    """

    project_regex = r"projects\/([^\/]+)"
    repo_regex = r"repos\/([^\/]+)"

    project_name = re.search(project_regex, url).group(1)
    repo_name = re.search(repo_regex, url).group(1)

    # Extract file path starting after '/src/' (adjust if needed)
    file_path = url.split("/src/", 1)[-1]

    return project_name, repo_name, file_path


def fetch_snippet(url: str, block_id: str | None = None):
    url = url.replace("\n", "")

    if "/bitbucket.juspay.net" in url:
        print(url)
        repository_name, project_name, file_path = parse_bitbucket_url(url)
        file_content = fetch_file_from_bitbucket(
            repository_name, project_name, file_path
        )

        if block_id:
            snippet_block = extract_snippet_block(
                content=file_content, block_id=block_id
            )
            if snippet_block:
                return snippet_block
        return file_content

    if "/blob" in url:
        url = url.replace("/blob", "/raw")
    try:
        response = requests.get(url.strip())
        response.raise_for_status()
        content = response.text
        if block_id:
            snippet_block = extract_snippet_block(content=content, block_id=block_id)
            if snippet_block:
                return snippet_block
        return content
    except requests.exceptions.RequestException as e:
        return str(e)


def handle_snippets(snippets):
    markdown = "## Sample Code Snippets:\n"
    markdown += f"### {snippets['topHeader']}:\n\n"
    for language, snippet_info in snippets["top"].items():
        snippet_url = (
            snippet_info.get("repository").strip() + snippet_info.get("file").strip()
        )
        code_snippet = fetch_snippet(snippet_url, snippet_info.get("blockId"))
        markdown += f"\n#### {language} Code Snippet:\n"
        markdown += f"\n```{language.lower()}\n{code_snippet}\n```\n"
    markdown += f"### {snippets['bottomHeader']}:\n\n"
    for part, snippet_info in snippets["bottom"].items():
        snippet_url = (
            snippet_info.get("repository").strip() + snippet_info.get("file").strip()
        )
        code_snippet = fetch_snippet(snippet_url, snippet_info.get("blockId"))
        markdown += f"\n#### {part}:\n"
        markdown += (
            f"```{snippet_info.get('language', 'plaintext')}\n{code_snippet}\n```\n"
        )
    return markdown


def handle_api_node(node):
    """Handles conversion of the 'API' custom extension, handling nested Tiptap or HTML in description"""
    api_data = node["attrs"]["versions"][next(iter(node["attrs"]["versions"]))]
    description = api_data["description"]
    endpoint = api_data.get("endpoint")
    request_type = api_data.get("requestType")
    content_type = api_data.get("contentType")
    authorization = api_data.get("authorization")
    headers = api_data.get("headers")
    snippets = api_data.get("snippets")
    body = api_data.get("body")
    response = api_data.get("response")

    markdown = ""

    if isinstance(description, dict):  # Assuming nested Tiptap
        markdown += parse_tiptap_nodes(description["content"])
    elif isinstance(description, str):  # Could be HTML
        markdown += description
    else:
        markdown += (
            "[Description Type Handling Needed]\n"  # Handle other potential types
        )
    if endpoint:
        markdown += "## Endpoints:\n"
        if "sandbox" in endpoint and len(endpoint["sandbox"]) > 0:
            markdown += f"- Sandbox: {endpoint.get('sandbox', '')}\n\n"
        if "production" in endpoint and len(endpoint["production"]) > 0:
            markdown += f"- Production: {endpoint.get('production', '')}\n\n"

    if request_type:
        markdown += f"## Request Type: \n{request_type}\n\n"

    if content_type:
        markdown += f"## Content-Type: \n{content_type}\n\n"

    if authorization:
        markdown += "## Authorization:\n"
        for auth_type, auth_info in authorization.items():
            markdown += (
                f"### {auth_type}: {parse_tiptap_node(auth_info.get('description'))}\n"
            )
            markdown += f"- Value: {auth_info.get('value')}\n"
            if "tags" in auth_info:
                markdown += f"- Tags: {', '.join(list(filter(lambda item: item is not None, auth_info['tags'])))}\n"

    if headers:
        markdown += "## Headers:\n"
        for header_name, header_info in headers.items():
            markdown += f"### {header_name}: {parse_tiptap_node(header_info.get('description'))}\n"
            markdown += f"- Value: {header_info.get('value')}\n"
            if "tags" in header_info:
                markdown += f"- Tags: {', '.join(list(filter(lambda item: item is not None, header_info['tags'])))}\n"

    if snippets:
        markdown += handle_snippets(snippets=snippets)

    if body:
        markdown += "## Body Parameters:\n"
        for param_group, params in body.items():
            markdown += f"### {param_group}:\n"
            for param_name, param_info in params.items():
                markdown += f"\n#### {param_name}:\n"
                if isinstance(param_info["description"], dict):
                    markdown += f"- Description: {parse_tiptap_node(param_info['description'])}\n"
                else:
                    markdown += f"- Description: {param_info['description']}\n"
                markdown += f"- Datatype: {param_info.get('datatype')}\n"
                markdown += f"- Value: {parse_tiptap_nodes(param_info.get('value')['content'], indent_level=1) if isinstance(param_info.get('value'), dict) else param_info.get('value')}\n"
                if "tags" in param_info:
                    markdown += f"- Tags: {', '.join(list(filter(lambda item: item is not None, param_info['tags'])))}\n"

    if response:
        markdown += "## API Responses:\n"
        for status_code, response_info in response.items():
            markdown += f"### Response Status {status_code}:\n"
            for response_name, info in response_info.items():
                markdown += f"\n#### {response_name}:\n"
                if isinstance(info["description"], dict):
                    markdown += f"- Description: {parse_tiptap_node(info['description'], indent_level=1)}\n"
                else:
                    markdown += f"- Description: {info['description']}\n"
                markdown += f"- Datatype: {info.get('datatype')}\n"
                markdown += f"- Value: {parse_tiptap_node(info.get('value'), indent_level=1) if isinstance(info.get('value'), dict) else info.get('value')}\n"
                if "tags" in info:
                    markdown += f"- Tags: {', '.join(list(filter(lambda item: item is not None, info['tags'])))}\n"

    return markdown


def handle_faq_node(node):
    """Handles conversion of the 'FAQ' custom extension."""
    markdown = "\n## FAQs\n"
    for idx, item in enumerate(node["attrs"]["faq"]["items"]):
        markdown += f"{str(idx+1)}. {item['question']}\n"
        markdown += (
            parse_tiptap_nodes(item["answer"]["content"])
            if isinstance(item["answer"], dict)
            else item["answer"]
        ).replace("\n", "\n\t") + "\n"
    return markdown


def handle_hiddentext_node(node):
    """Handles conversion of the 'HiddenText' custom extension."""
    content = node["attrs"].get("text", "")
    if content:
        return f"### Additional context: -\n {content}"
    else:
        return ""


def handle_image_node(node):
    """Handles conversion of the 'Image' (or 'ImageExtension') custom extension."""
    return f"\n\n![{node['attrs']['alt'] if 'alt' in node['attrs'] else 'Image'}]({urllib.parse.quote(node['attrs']['src'])})\n".replace(
        "%3A", ":"
    )


def handle_note_node(node):
    """Handles conversion of the 'Note' custom extension."""
    markdown = ""
    note_type = "Note"  # Default
    if node["attrs"]["warning"]:
        note_type = "Warning"
    elif node["attrs"]["error"]:
        note_type = "Error"

    markdown += f"\n> **{note_type}:**\n"

    description = node["attrs"]["text"]
    if isinstance(description, dict):  # Assuming nested Tiptap
        markdown += "> " + parse_tiptap_nodes(description["content"]).replace(
            "\n", "\n> "
        )
    elif isinstance(description, str):  # Could be HTML
        markdown += "> " + description.replace("\n", "\n> ")
    else:
        markdown += (
            "[Description Type Handling Needed]\n"  # Handle other potential types
        )

    return f"{markdown}\n"


def handle_snippet_node(node):
    """Handles conversion of the 'Snippet' custom extension for any language."""
    for language_key, snippet_info in node["attrs"]["code"].items():
        repository = snippet_info.get("repository", "")
        file_path = snippet_info.get("file", "")
        block_id = snippet_info.get("blockId")
        language = language_key.lower()

        code_snippet = fetch_snippet(
            url=(repository.strip() + file_path.strip()), block_id=block_id
        )

        return f"\n{language}\n```{language.lower()}\n{code_snippet}\n```\n"
    return "Unable to find code snippet.\n"


def handle_substep_node(node):
    """Handles conversion of the 'Substep' custom extension."""
    header = node["attrs"]["header"]
    label = node["attrs"].get("label", "")
    description = node["attrs"]["description"]
    code_blocks = node["attrs"]["code"] if "code" in node["attrs"] else None

    if label:
        header = f"{label} {header}"
    markdown = f"\n\n### {header}\n\n"

    if isinstance(description, dict):  # Assuming nested Tiptap
        markdown += parse_tiptap_nodes(description["content"])
    elif isinstance(description, str):  # Could be HTML
        markdown += description + "\n"
    else:
        markdown += "[Description Type Handling Needed]\n"

    if code_blocks:
        markdown += "\n\n#### Code Snippets: -\n"
        for language, code_info in code_blocks.items():
            repository = code_info.get("repository", "")
            file_path = code_info.get("file", "")
            block_id = code_info.get("blockId")
            code_snippet = fetch_snippet(
                url=(repository.strip() + file_path.strip()), block_id=block_id
            )
            markdown += f"\n{language}\n```{language.lower()}\n{code_snippet}\n```\n"

    return markdown


def process_payload(payload_data, level=0):
    markdown_output = ""
    indent = "    " * level

    for key, value in payload_data.items():
        if key == "description" and isinstance(value, dict):
            try:
                if "type" in value:
                    markdown_output += (
                        f"{indent}- **{key.capitalize()}**:"
                        + parse_tiptap_node(value).replace("\n", f"\n{indent}    ")
                        + "\n"
                    )
                else:
                    markdown_output += (
                        f"{indent}- **{key.capitalize()}**:"
                        + process_payload(value).replace("\n", f"\n{indent}    ")
                        + "\n"
                    )

            except Exception as e:
                print("Exception", value)
                raise (e)
        elif isinstance(value, list):
            markdown_output += f"{indent}- **{key.capitalize()}**: {', '.join(value)}\n"
        elif isinstance(value, dict):
            if value.get("type", "") != "doc":
                markdown_output += f"{indent}- **{key.capitalize()}**:\n{process_payload(value, level + 1)}"
            else:
                markdown_output += f"{indent}- **Value**:\n"
                markdown_output += (
                    indent
                    + "    "
                    + parse_tiptap_node(value)
                    .replace("\n", "\n" + indent + "    ")
                    .replace("#", "")
                )
        else:
            markdown_output += f"{indent}- **{key.capitalize()}**: {value}\n"

    return markdown_output


def handle_payload_node(node, level=0, heading="", indent_level=0):
    """Handles conversion of the 'Payload' custom extension, including nested payloads to markdown."""

    return (
        f"\n### {'#' * level}{heading}Payload\n"
        if indent_level == 0
        else "\n\n"
        + process_payload(node["attrs"]["payload"], indent_level).replace(
            "\n", "\n" + "    " * (indent_level)
        )
    )


def handle_tabpayload_node(node):
    """Handles conversion of the 'TabbedPayload' custom extension."""
    tabs = node["attrs"]["payload"]["items"]
    markdown_text = ""
    for tab in tabs:
        markdown_text += (
            f"\n ## {tab['tabName']} Payload\n"
            + process_payload(tab["tabContent"], 0)
            + "\n"
        )
    return markdown_text


def handle_table_node(node):
    """Handles conversion of the 'Table' (or 'TableExtension') custom extension."""
    markdown = "\n"
    raw_data = node["attrs"]["rawData"]

    show_column_headers = raw_data.get("showColumnHeaders", False)
    show_row_headers = raw_data.get("showRowHeaders", False)
    column_set = raw_data.get("columnSet", [])
    row_set = raw_data.get("rowSet", [])
    data = raw_data.get("data", [])
    pivot_cell_value = raw_data.get("pivotCellValue", "")

    # Construct header row
    if show_column_headers or show_row_headers:
        header_row = []
        if show_row_headers:
            header_row.append(pivot_cell_value)
        header_row.extend(column_set)
        markdown += "| " + " | ".join(header_row) + " |\n"
        markdown += "|---" * len(header_row) + "|\n"

    # Construct table body
    for row_index, row_name in enumerate(row_set):
        row_data = data[row_index]["content"]
        body_row = []
        if show_row_headers:
            body_row.append(row_name)
        body_row.extend(row_data)
        body_row = ["" if item is None else item for item in body_row]
        markdown += "| " + " | ".join(body_row) + " |\n"

    return markdown


def handle_video_node(node):
    """Handles conversion of the 'Video' and/or 'VideoS3' extensions."""
    return f"[Video]({node['attrs']['src']})\n"


def handle_marks(text, marks):
    """Handles text marks like bold, italic, etc."""
    for mark in marks:
        if mark["type"] == "bold":
            text = "**" + text.strip() + "** "
        elif mark["type"] == "italic":
            text = "_" + text.strip() + "_ "
        # ... Add cases for other marks ...
    return f"{text}"


def generate_ref_map(ref_list: List[str], original_file_paths: dict) -> dict:
    ref_map = {}
    for ref in ref_list:
        split_ref = ref.split("/")
        ref_map[split_ref[1]] = {}
    for ref in ref_list:
        split_ref = ref.split("/")
        ref_map[split_ref[1]][split_ref[2]] = {}
    for ref in ref_list:
        split_ref = ref.split("/")
        ref_map[split_ref[1]][split_ref[2]][split_ref[3]] = {}

    for ref in ref_list:
        split_ref = ref.split("/")
        for platform_id in original_file_paths[ref]:
            ref_map[split_ref[1]][split_ref[2]][split_ref[3]].setdefault(
                split_ref[4], []
            ).append(original_file_paths[ref][platform_id])
    return ref_map


def fetch_refs(ref_map: dict) -> List[MarkdownDocument]:
    # TODO: Add handling of ref variables in Tesseract
    converted_ref_docs: List[MarkdownDocument] = []
    for product in ref_map.keys():
        product_doc_path = requests.get(
            url=f"{tesseract_endpoint}/getLatestDoc?product={product}"
        ).json()["docPath"]
        for platform in ref_map[product].keys():
            platform_json_path = product_doc_path + platform + ".json"
            platform_json = requests.get(platform_json_path).json()
            sections = platform_json["sections"]
            for section in sections:
                section_id = section["sectionId"]
                if section_id in ref_map[product][platform]:
                    for step in section["steps"]:
                        step_id = step["stepId"]
                        if "markup" not in step and "$ref" not in step:
                            step = requests.get(
                                url=f"{product_doc_path}{platform}/{section_id}/{step_id}.json"
                            ).json()
                        if step_id in ref_map[product][platform][section_id]:
                            output_file_names: list[str] = ref_map[product][platform][
                                section_id
                            ][step_id]
                            if "markup" in step:
                                markdown_text = tiptap_to_markdown(step["markup"])
                                for file_name in output_file_names:
                                    destination_product_metadata = (
                                        file_name.removesuffix(".md").split("_")
                                    )
                                    document = MarkdownDocument(
                                        markdown=markdown_text,
                                        metadata={
                                            "source": f"{tesseract_endpoint}/"
                                            + f"{destination_product_metadata[0]}/{destination_product_metadata[1]}/{destination_product_metadata[2]}/{destination_product_metadata[3]}",
                                            "product": destination_product_metadata[0],
                                            "platform": destination_product_metadata[1],
                                            "section": destination_product_metadata[2],
                                            "step": destination_product_metadata[3],
                                        },
                                        filepath=file_name,
                                    )
                                    converted_ref_docs.append(document)
    return converted_ref_docs


def convert_tiptap_to_markdown(
    product: str,
    platform: str = None,
    section: str = None,
    step: str = None,
) -> List[MarkdownDocument]:
    """
    Optimized function to fetch documentation with support for specific platform/section/step.
    
    Args:
        product: Product name (required)
        platform: Specific platform to fetch (optional)
        section: Specific section to fetch (optional) 
        step: Specific step to fetch (optional)
    
    Returns:
        List of MarkdownDocument objects
    """
    start_time = time.time()
    
    # Get latest doc info
    latest_doc_resp = requests.get(f"{tesseract_endpoint}/getLatestDoc?product={product}")
    if latest_doc_resp.status_code != 200:
        logger.error(f"Failed to get latest doc for {product}")
        return []
    
    latest_doc_json = latest_doc_resp.json()
    product_doc_path = latest_doc_json["docPath"]
    
    converted_documents: List[MarkdownDocument] = []

    # If specific step requested, fetch only that platform
    if platform and section and step:
        return fetch_specific_step(product, product_doc_path, platform, section, step, start_time)
    
    # If specific section requested, fetch that platform and section
    if platform and section:
        return fetch_specific_section(product, product_doc_path, platform, section, start_time)
    
    # If specific platform requested, fetch only that platform
    if platform:
        return fetch_specific_platform(product, product_doc_path, platform, start_time)
    
    # Otherwise, fetch all platforms (original behavior)
    return fetch_all_platforms(product, latest_doc_json, start_time)

def fetch_specific_step(product: str, doc_path: str, platform: str, section: str, step: str, start_time: float) -> List[MarkdownDocument]:
    """Fetch a specific step only"""
    platform_resp = requests.get(f"{doc_path}{platform}.json")
    if platform_resp.status_code != 200:
        logger.error(f"Failed to fetch platform {platform} for {product}")
        return []
    
    platform_json = platform_resp.json()
    doc = extract_step_from_platform(platform_json, product, platform, section, step)
    
    end_time = time.time()
    #logger.info(f"Specific step fetch completed in {end_time - start_time:.2f} seconds")
    
    return [doc] if doc else []

def fetch_specific_section(product: str, doc_path: str, platform: str, section: str, start_time: float) -> List[MarkdownDocument]:
    """Fetch all steps in a specific section"""
    platform_resp = requests.get(f"{doc_path}{platform}.json")
    if platform_resp.status_code != 200:
        logger.error(f"Failed to fetch platform {platform} for {product}")
        return []
    
    platform_json = platform_resp.json()
    docs = []
    
    # Handle both new and old structures
    sections = platform_json.get("sections", [])
    for sec in sections:
        if sec.get("sectionId") == section:
            #logger.info(f"Found section '{section}', processing {len(sec.get('steps', []))} steps")
            for step in sec.get("steps", []):
                step_id = step.get("stepId")
                #logger.info(f"Processing step '{step_id}' in section '{section}'")
                doc = extract_step_from_platform(platform_json, product, platform, section, step_id)
                if doc:
                    docs.append(doc)
                    #logger.info(f"Successfully processed step '{step_id}'")
                else:
                    logger.warning(f"Failed to process step '{step_id}'")
    
    # Also check new structure (documentation > overview > steps) if section is "overview"
    if section == "overview":
        documentation = platform_json.get("documentation", {})
        overview = documentation.get("overview", {})
        for step in overview.get("steps", []):
            step_id = step.get("stepId")
            #logger.info(f"Processing overview step '{step_id}'")
            doc = extract_step_from_platform(platform_json, product, platform, section, step_id)
            if doc:
                docs.append(doc)
                #logger.info(f"Successfully processed overview step '{step_id}'")
    
    end_time = time.time()
    #logger.info(f"Specific section fetch completed in {end_time - start_time:.2f} seconds, found {len(docs)} documents")
    return docs

def fetch_specific_platform(product: str, doc_path: str, platform: str, start_time: float) -> List[MarkdownDocument]:
    """Fetch all sections/steps for a specific platform"""
    platform_resp = requests.get(f"{doc_path}{platform}.json")
    if platform_resp.status_code != 200:
        logger.error(f"Failed to fetch platform {platform} for {product}")
        return []
    
    platform_json = platform_resp.json()
    docs = []
    
    # Handle new structure (documentation > overview > steps)
    documentation = platform_json.get("documentation", {})
    overview = documentation.get("overview", {})  # Fixed: was missing this line
    if overview and "steps" in overview:
        #logger.info(f"Processing overview section with {len(overview.get('steps', []))} steps")
        for step in overview.get("steps", []):
            step_id = step.get("stepId")
            #logger.info(f"Processing overview step '{step_id}'")
            doc = extract_step_from_platform(platform_json, product, platform, "overview", step_id)
            if doc:
                docs.append(doc)
                #logger.info(f"Successfully processed overview step '{step_id}'")
    
    # Handle old structure (sections > steps)
    sections = platform_json.get("sections", [])
    #logger.info(f"Processing {len(sections)} sections for platform '{platform}'")
    
    for section in sections:
        section_id = section.get("sectionId")
        #logger.info(f"Processing section '{section_id}'")
        
        # Skip excluded sections
        if section_id in ["ec-sdk-integration", "payv3-offers-integration", "api-integration"]:
            #logger.info(f"Skipping excluded section '{section_id}'")
            continue
        
        steps = section.get("steps", [])
        #logger.info(f"Section '{section_id}' has {len(steps)} steps")
        
        for step in steps:
            step_id = step.get("stepId")
            #logger.info(f"Processing step '{step_id}' in section '{section_id}'")
            doc = extract_step_from_platform(platform_json, product, platform, section_id, step_id)
            if doc:
                docs.append(doc)
                #logger.info(f"Successfully processed step '{step_id}' in section '{section_id}'")
            else:
                logger.warning(f"Failed to process step '{step_id}' in section '{section_id}'")
    
    end_time = time.time()
    #logger.info(f"Specific platform fetch completed in {end_time - start_time:.2f} seconds, found {len(docs)} documents")
    return docs

def extract_step_from_platform(platform_json: dict, product: str, platform: str, section: str, step: str) -> MarkdownDocument:
    """Extract and convert a specific step from platform JSON"""
    
    #logger.info(f"Looking for step '{step}' in section '{section}'")
    
    # Try new structure first (documentation > overview > steps)
    documentation = platform_json.get("documentation")
    if documentation and "overview" in documentation:
        available_steps = [st.get("stepId") for st in documentation["overview"].get("steps", [])]
        #logger.info(f"Available steps in overview: {available_steps}")
        
        for st in documentation["overview"].get("steps", []):
            if st.get("stepId") == step:
                content = st.get("content", [])
                if content:
                    markdowns = []
                    for content_item in content:
                        html = content_item.get("htmlText")
                        if html:
                            markdown = markdownify.markdownify(html, heading_style="ATX")
                            markdowns.append(markdown)
                    
                    if markdowns:
                        #logger.info(f"Found step '{step}' in overview section with HTML content")
                        return MarkdownDocument(
                            markdown="\n\n".join(markdowns),
                            metadata={
                                "source": f"{tesseract_endpoint}/{product}/{platform}/{section}/{step}",
                                "product": product,
                                "platform": platform,
                                "section": section,
                                "step": step,
                            },
                            filepath=f"{product}_{platform}_{section}_{step}.md",
                        )
    
    # Check old Tiptap structure (sections > steps > markup)
    for sec in platform_json.get("sections", []):
        section_id = sec.get("sectionId")
        #logger.info(f"Checking section: {section_id}")
        
        if section_id == section:  # Found the matching section
            available_steps = [st.get("stepId") for st in sec.get("steps", [])]
            #logger.info(f"Available steps in section '{section}': {available_steps}")
            
            for st in sec.get("steps", []):
                if st.get("stepId") == step:  # Found the matching step
                    #logger.info(f"Found step '{step}' in section '{section}'")
                    
                    # Check if step has markup
                    if "markup" in st:
                        #logger.info(f"Step '{step}' has markup, converting...")
                        markdown = tiptap_to_markdown(st["markup"])
                        return MarkdownDocument(
                            markdown=markdown,
                            metadata={
                                "source": f"{tesseract_endpoint}/{product}/{platform}/{section}/{step}",
                                "product": product,
                                "platform": platform,
                                "section": section,
                                "step": step,
                            },
                            filepath=f"{product}_{platform}_{section}_{step}.md",
                        )
                    
                    # Handle $ref steps - FIXED VERSION
                    elif "$ref" in st:
                        #logger.info(f"Step '{step}' has $ref: {st['$ref']}, resolving reference...")
                        ref_path = st["$ref"]
                        
                        # Parse the reference path (e.g., "#/hyper-checkout/android/base-sdk-integration/session")
                        if ref_path.startswith("#/"):
                            ref_parts = ref_path[2:].split("/")  # Remove "#/" and split
                            if len(ref_parts) >= 4:
                                ref_product, ref_platform, ref_section, ref_step = ref_parts[:4]
                                
                                # Fetch the referenced step
                                try:
                                    # Try to get from current platform JSON first
                                    ref_doc = find_ref_step_in_platform(platform_json, ref_section, ref_step)
                                    
                                    if not ref_doc:
                                        # If not found in current platform, fetch from referenced platform
                                        #logger.info(f"Fetching referenced step from {ref_platform}/{ref_section}/{ref_step}")
                                        
                                        # Get doc path (you need to pass this to the function)
                                        latest_doc_resp = requests.get(f"{tesseract_endpoint}/getLatestDoc?product={ref_product}")
                                        if latest_doc_resp.status_code == 200:
                                            doc_path = latest_doc_resp.json()["docPath"]
                                            
                                            # Try fetching the step JSON directly
                                            step_url = f"{doc_path}{ref_platform}/{ref_section}/{ref_step}.json"
                                            step_resp = requests.get(step_url)
                                            
                                            if step_resp.status_code == 200:
                                                step_json = step_resp.json()
                                                if "markup" in step_json:
                                                    #logger.info(f"Found markup in referenced step JSON for '{step}'")
                                                    markdown = tiptap_to_markdown(step_json["markup"])
                                                    return MarkdownDocument(
                                                        markdown=markdown,
                                                        metadata={
                                                            "source": f"{tesseract_endpoint}/{product}/{platform}/{section}/{step}",
                                                            "product": product,
                                                            "platform": platform,
                                                            "section": section,
                                                            "step": step,
                                                        },
                                                        filepath=f"{product}_{platform}_{section}_{step}.md",
                                                    )
                                            else:
                                                logger.warning(f"Could not fetch referenced step JSON: {step_resp.status_code}")
                                    else:
                                        return ref_doc
                                        
                                except Exception as e:
                                    logger.error(f"Error resolving $ref for step '{step}': {e}")
                    
                    # If no markup and no $ref, try to fetch step JSON
                    else:
                        #logger.info(f"Step '{step}' has no markup or $ref, trying to fetch step JSON...")
                        try:
                            # Get the doc path from latest_doc_json (you need to pass this)
                            latest_doc_resp = requests.get(f"{tesseract_endpoint}/getLatestDoc?product={product}")
                            if latest_doc_resp.status_code == 200:
                                doc_path = latest_doc_resp.json()["docPath"]
                                step_url = f"{doc_path}{platform}/{section}/{step}.json"
                                step_resp = requests.get(step_url)
                                if step_resp.status_code == 200:
                                    step_json = step_resp.json()
                                    if "markup" in step_json:
                                        #logger.info(f"Found markup in step JSON for '{step}'")
                                        markdown = tiptap_to_markdown(step_json["markup"])
                                        return MarkdownDocument(
                                            markdown=markdown,
                                            metadata={
                                                "source": f"{tesseract_endpoint}/{product}/{platform}/{section}/{step}",
                                                "product": product,
                                                "platform": platform,
                                                "section": section,
                                                "step": step,
                                            },
                                            filepath=f"{product}_{platform}_{section}_{step}.md",
                                        )
                                    else:
                                        logger.warning(f"Step JSON for '{step}' exists but has no markup")
                                else:
                                    logger.warning(f"Could not fetch step JSON for {step}: {step_resp.status_code}")
                        except Exception as e:
                            logger.warning(f"Error fetching step JSON for {step}: {e}")
                    
                    # If we reach here, step was found but couldn't be processed
                    logger.warning(f"Step '{step}' found but could not be converted to markdown")
                    return None
            
            # If we reach here, step was not found in the matching section
            logger.warning(f"Step '{step}' not found in section '{section}'")
            return None
    
    # If we reach here, section was not found
    logger.warning(f"Section '{section}' not found")
    return None

def find_ref_step_in_platform(platform_json: dict, section: str, step: str) -> MarkdownDocument:
    """Helper function to find a referenced step within the same platform JSON"""
    for sec in platform_json.get("sections", []):
        if sec.get("sectionId") == section:
            for st in sec.get("steps", []):
                if st.get("stepId") == step and "markup" in st:
                    markdown = tiptap_to_markdown(st["markup"])
                    return MarkdownDocument(
                        markdown=markdown,
                        metadata={},
                        filepath="",
                    )
    return None

def fetch_all_platforms(product: str, latest_doc_json: dict, start_time: float) -> List[MarkdownDocument]:
    """Original logic for fetching all platforms (backward compatibility)"""
    product_doc_path = latest_doc_json["docPath"]
    product_skeleton_doc_path = latest_doc_json["url"]
    product_skeleton_json = requests.get(url=product_skeleton_doc_path).json()

    platform_ids = []
    refs = []
    refs_with_filepath = {}
    scraped_files = []
    converted_documents: List[MarkdownDocument] = []

    for platform_skeleton_json in product_skeleton_json["documentation"]["platforms"]:
        platform_ids.append(platform_skeleton_json["platformId"])

    for platform_id in platform_ids:
        tiptap_platform_doc = requests.get(
            url=product_doc_path + platform_id + ".json"
        ).json()
        sections = tiptap_platform_doc["sections"]
        for section in sections:
            section_id = section["sectionId"]
            if section_id in ["ec-sdk-integration", "payv3-offers-integration", "api-integration"]:
                continue
            for step in section["steps"]:
                step_id = step["stepId"]
                print("Scraping", product, platform_id, section_id, step_id)
                if "markup" not in step and "$ref" not in step:
                    step = requests.get(
                        url=f"{product_doc_path}{platform_id}/{section_id}/{step_id}.json"
                    ).json()
                if "markup" in step:
                    markdown_text = tiptap_to_markdown(step["markup"])
                    document = MarkdownDocument(
                        metadata={
                            "source": f"{tesseract_endpoint}/{product}/{platform_id}/{section_id}/{step_id}",
                            "product": product,
                            "platform": platform_id,
                            "section": section_id,
                            "step": step_id,
                        },
                        markdown=markdown_text,
                        filepath=f"{product}_{platform_id}_{section_id}_{step_id}.md",
                    )
                    converted_documents.append(document)
                    scraped_files.append(
                        f"#/{product}/{platform_id}/{section_id}/{step_id}"
                    )
                else:
                    if "$ref" in step:
                        ref_string = step["$ref"]
                        refs_with_filepath[step["$ref"]] = (
                            refs_with_filepath[step["$ref"]]
                            if step["$ref"] in refs_with_filepath
                            else {}
                        )
                        refs_with_filepath[step["$ref"]][
                            platform_id
                        ] = f"{product}_{platform_id}_{section_id}_{step_id}.md"
                        if ref_string not in refs:
                            refs.append(step["$ref"])
                    else:
                        import sys
                        print("Unhandled Step Content", step, file=sys.stderr)
    
    # Fetch refs if necessary
    refs = [ref for ref in refs if ref not in scraped_files]
    ref_map = generate_ref_map(refs, original_file_paths=refs_with_filepath)
    converted_documents.extend(fetch_refs(ref_map))
    
    end_time = time.time()
    #logger.info(f"Full product fetch completed in {end_time - start_time:.2f} seconds")
    return converted_documents
