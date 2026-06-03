from config.settings import (
    app_title,
    aws_region,
    bedrock_model_id,
    clear_settings_cache,
    dataset_label,
    snowflake_schema,
)


def test_defaults_without_snowflake_config(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)
    monkeypatch.setattr("config.settings._snowflake_attr", lambda name, default="": default)
    clear_settings_cache()
    assert aws_region() == "us-east-1"
    assert bedrock_model_id() == "us.amazon.nova-pro-v1:0"
    assert dataset_label() == "Snowflake dataset"
    assert app_title() == "AI SQL Assistant"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    monkeypatch.setenv("DATASET_LABEL", "Client Analytics")
    monkeypatch.setenv("APP_TITLE", "Analytics Copilot")
    monkeypatch.setattr("config.settings._snowflake_attr", lambda name, default="": default)
    clear_settings_cache()
    assert aws_region() == "eu-west-1"
    assert bedrock_model_id().startswith("anthropic.claude")
    assert dataset_label() == "Client Analytics"
    assert app_title() == "Analytics Copilot"


def test_snowflake_schema_from_config(monkeypatch):
    monkeypatch.setattr(
        "config.settings._snowflake_attr",
        lambda name, default="": {"schema": "ANALYTICS", "database": "PROD"}.get(name, default),
    )
    clear_settings_cache()
    assert snowflake_schema() == "ANALYTICS"
