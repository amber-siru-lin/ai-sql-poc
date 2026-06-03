"""Runtime settings from environment variables and optional snowflake_config overrides."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_AWS_REGION = "us-east-1"
DEFAULT_BEDROCK_MODEL_ID = "us.amazon.nova-pro-v1:0"
DEFAULT_SCHEMA_MARKDOWN = "schema/tpch_sf1.md"
DEFAULT_DATASET_LABEL = "Snowflake dataset"
DEFAULT_APP_TITLE = "AI SQL Assistant"
DEFAULT_WREN_PROFILE_NAME = "default"


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _snowflake_attr(name: str, default: str = "") -> str:
    try:
        from config import snowflake_config as sf
    except ImportError:
        return default
    value = getattr(sf, name, None)
    if value is None:
        return default
    return str(value).strip()


def aws_region() -> str:
    return _env("AWS_REGION") or _env("AWS_DEFAULT_REGION") or DEFAULT_AWS_REGION


def bedrock_model_id() -> str:
    return _env("BEDROCK_MODEL_ID") or DEFAULT_BEDROCK_MODEL_ID


def bedrock_model_label() -> str:
    """Short label for UI (derived from model id unless overridden)."""
    override = _env("BEDROCK_MODEL_LABEL")
    if override:
        return override
    model = bedrock_model_id()
    if model.startswith("us.amazon."):
        slug = model.removeprefix("us.amazon.").removesuffix("-v1:0")
        return slug.replace("-", " ").title()
    return model.rsplit("/", 1)[-1]


def snowflake_database() -> str:
    return _snowflake_attr("database") or _env("SNOWFLAKE_DATABASE")


def snowflake_schema() -> str:
    return _snowflake_attr("schema") or _env("SNOWFLAKE_SCHEMA")


def schema_markdown_path() -> Path:
    rel = _snowflake_attr("schema_markdown_path") or _env("SCHEMA_MARKDOWN_PATH") or DEFAULT_SCHEMA_MARKDOWN
    return REPO_ROOT / rel


def dataset_label() -> str:
    return _snowflake_attr("dataset_label") or _env("DATASET_LABEL") or DEFAULT_DATASET_LABEL


def app_title() -> str:
    return _env("APP_TITLE") or DEFAULT_APP_TITLE


def wren_profile_name() -> str:
    return _snowflake_attr("wren_profile_name") or _env("WREN_PROFILE_NAME") or DEFAULT_WREN_PROFILE_NAME


def qualified_schema_prefix() -> str:
    db = snowflake_database()
    sch = snowflake_schema()
    if db and sch:
        return f"{db}.{sch}"
    return sch or "schema"


def schema_qualified_name(table: str) -> str:
    sch = snowflake_schema()
    if sch:
        return f"{sch}.{table.upper()}"
    return table.upper()


def create_bedrock_chat():
    from langchain_aws import ChatBedrock

    return ChatBedrock(model_id=bedrock_model_id(), region_name=aws_region())


@lru_cache(maxsize=1)
def wren_physical_sql_pattern() -> re.Pattern[str]:
    """Regex matching raw Snowflake references that Wren-mode SQL must avoid."""
    parts: list[str] = [r"__source", r"wren_src_"]
    db = snowflake_database()
    sch = snowflake_schema()
    if db:
        parts.append(re.escape(db))
    if sch:
        parts.append(rf"\b{re.escape(sch)}\.")

    # Optional TPCH-style column guard when using the sample dataset layout.
    if _env("WREN_STRICT_TPCH_GUARD", "false").lower() in {"1", "true", "yes"}:
        parts.extend(
            [
                r"\bC_CUSTKEY\b",
                r"\bC_NAME\b",
                r"\bC_NATIONKEY\b",
                r"\bC_MKTSEGMENT\b",
                r"\bO_ORDERKEY\b",
                r"\bO_CUSTKEY\b",
                r"\bO_TOTALPRICE\b",
                r"\bN_NATIONKEY\b",
                r"\bN_NAME\b",
            ]
        )

    return re.compile("|".join(parts), re.I)


def clear_settings_cache() -> None:
    wren_physical_sql_pattern.cache_clear()
