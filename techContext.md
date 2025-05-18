# Tech Context

## Core Technologies
- **Python:** The primary programming language for the application backend and Pydantic models.
- **Pydantic:** Used for data validation, settings management, and serialization/deserialization, leveraging Python type annotations.
- **JSON Schema:** The standard used for defining the structure of JSON data in `schema_control.json`.

## Key Libraries/Frameworks (Inferred)
- **FastAPI (Likely):** Given the use of Pydantic, FastAPI is a common web framework choice in the Python ecosystem for building APIs. This would be the environment where Pydantic models are most actively used for request/response handling.
- **Other Python libraries:** Standard Python data types and libraries (e.g., `typing.Optional`, `typing.List`, `datetime`) will be used in Pydantic models.

## Schema Definitions
- **`schema_control.json`:**
    - Format: JSON Schema.
    - Location: `juspay_dashboard_mcp/api/schema_control.json`.
    - Role: Designated source of truth for API schemas.
- **Pydantic Models:**
    - Format: Python classes inheriting from `pydantic.BaseModel`.
    - Location: Files within `juspay_dashboard_mcp/api_schema/` (e.g., `alert.py`, `gateway.py`).
    - Role: Used for runtime data validation and serialization in the Python application.

## Tooling
- **Text Editors/IDEs (e.g., VS Code):** For viewing and editing JSON and Python files.
- **Diffing Tools:** Used to generate `schema_comparison_diff.txt` (e.g., custom scripts, `jsondiffpatch`).
- **Python Interpreter & Environment Management (e.g., venv, conda, uv):** For running Python code and managing dependencies.

## Version Control
- **Git (Assumed):** For tracking changes to the codebase, including schema files and Pydantic models.

## Constraints & Considerations
- **Type Mapping:** Careful mapping between JSON Schema types and Python types (Pydantic field types) is required. Some apparent differences might be representational (e.g., JSON `string` vs. Python `str`).
    - `string` -> `str`
    - `integer` -> `int`
    - `number` -> `float` or `Decimal` (depending on precision requirements)
    - `boolean` -> `bool`
    - `array` -> `List[<type>]`
    - `object` -> `Dict[str, <type>]` or a nested Pydantic model.
- **Optionality/Required Fields:**
    - JSON Schema: `required` array lists mandatory properties.
    - Pydantic: Fields without a default value or not explicitly marked `Optional` are required. Fields typed with `Optional[<type>]` or having a default value are optional.
- **Descriptions:** JSON Schema `description` fields should ideally be translated to docstrings or `Field(description="...")` in Pydantic models for better maintainability.
