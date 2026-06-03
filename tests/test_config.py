import os
from pathlib import Path

from alphasift.config import Config


def test_config_reads_daily_stock_analysis_litellm_env(monkeypatch):
    monkeypatch.setenv("LITELLM_MODEL", "openai/deepseek-ai/DeepSeek-V3")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setenv("LITELLM_FALLBACK_MODELS", "openai/gpt-4o-mini,anthropic/claude-3-5-sonnet")
    monkeypatch.setenv("LLM_TIMEOUT_SEC", "42")

    config = Config.from_env()

    assert config.llm_model == "openai/deepseek-ai/DeepSeek-V3"
    assert config.llm_api_key == "sk-test"
    assert config.llm_base_url == "https://api.siliconflow.cn/v1"
    assert config.llm_fallback_models == ["openai/gpt-4o-mini", "anthropic/claude-3-5-sonnet"]
    assert config.llm_timeout_sec == 42
    assert config.has_llm_config() is True


def test_config_reads_llm_channels_env(monkeypatch):
    monkeypatch.setenv("LLM_CHANNELS", "deepseek")
    monkeypatch.setenv("LLM_DEEPSEEK_PROTOCOL", "openai")
    monkeypatch.setenv("LLM_DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    monkeypatch.setenv("LLM_DEEPSEEK_API_KEYS", "key1,key2")
    monkeypatch.setenv("LLM_DEEPSEEK_MODELS", "deepseek-chat,deepseek-reasoner")

    config = Config.from_env()

    assert config.llm_model == "openai/deepseek-chat"
    assert config.llm_channels[0]["api_keys"] == ["key1", "key2"]
    assert config.llm_channels[0]["base_url"] == "https://api.deepseek.com/v1"
    assert config.has_llm_config() is True


def test_config_can_disable_default_post_analyzer(monkeypatch):
    monkeypatch.setenv("POST_ANALYZERS", "none")

    config = Config.from_env()

    assert config.post_analyzers == []


def test_config_reads_portfolio_diversity_env(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_DIVERSITY_ENABLED", "true")
    monkeypatch.setenv("PORTFOLIO_MAX_SAME_LLM_SECTOR", "2")
    monkeypatch.setenv("PORTFOLIO_CONCENTRATION_PENALTY", "6.5")

    config = Config.from_env()

    assert config.portfolio_diversity_enabled is True
    assert config.portfolio_max_same_llm_sector == 2
    assert config.portfolio_concentration_penalty == 6.5


def test_config_reads_daily_fetch_retries(monkeypatch):
    monkeypatch.setenv("DAILY_FETCH_RETRIES", "4")

    config = Config.from_env()

    assert config.daily_fetch_retries == 4


def test_config_uses_resilient_snapshot_source_first_with_tushare_token(monkeypatch):
    monkeypatch.delenv("SNAPSHOT_SOURCE_PRIORITY", raising=False)
    monkeypatch.setenv("TUSHARE_TOKEN", "token")

    config = Config.from_env()

    assert config.snapshot_source_priority == [
        "em_datacenter",
        "tushare",
        "efinance",
        "akshare_em",
    ]


def test_config_omits_tushare_from_default_priority_without_token(monkeypatch):
    monkeypatch.delenv("SNAPSHOT_SOURCE_PRIORITY", raising=False)
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    monkeypatch.delenv("TUSHARE_API_TOKEN", raising=False)

    config = Config.from_env()

    assert config.snapshot_source_priority == [
        "em_datacenter",
        "efinance",
        "akshare_em",
    ]


def test_config_respects_explicit_snapshot_priority_with_tushare_token(monkeypatch):
    monkeypatch.setenv("TUSHARE_TOKEN", "token")
    monkeypatch.setenv("SNAPSHOT_SOURCE_PRIORITY", "efinance,em_datacenter")

    config = Config.from_env()

    assert config.snapshot_source_priority == ["efinance", "em_datacenter"]


def test_config_reads_industry_and_candidate_context_env(monkeypatch):
    monkeypatch.setenv("INDUSTRY_MAP_FILES", "/tmp/industry.csv,/tmp/concepts.json")
    monkeypatch.setenv("INDUSTRY_PROVIDER", "akshare")
    monkeypatch.setenv("INDUSTRY_PROVIDER_MAX_BOARDS", "12")
    monkeypatch.setenv("LLM_CANDIDATE_CONTEXT_ENABLED", "true")
    monkeypatch.setenv("LLM_CANDIDATE_CONTEXT_MAX_CANDIDATES", "5")
    monkeypatch.setenv("LLM_CANDIDATE_CONTEXT_PROVIDERS", "news,fund_flow")

    config = Config.from_env()

    assert config.industry_map_files == [Path("/tmp/industry.csv"), Path("/tmp/concepts.json")]
    assert config.industry_provider == "akshare"
    assert config.industry_provider_max_boards == 12
    assert config.llm_candidate_context_enabled is True
    assert config.llm_candidate_context_max_candidates == 5
    assert config.llm_candidate_context_providers == ["news", "fund_flow"]
    assert config.llm_candidate_context_cache_enabled is True


def test_config_reads_evaluation_cost(monkeypatch):
    monkeypatch.setenv("EVALUATION_COST_BPS", "15")
    monkeypatch.setenv("EVALUATION_FOLLOW_THROUGH_PCT", "4")
    monkeypatch.setenv("EVALUATION_FAILED_BREAKOUT_PCT", "-2.5")
    monkeypatch.setenv("EVALUATION_PRICE_PATH_ENABLED", "true")
    monkeypatch.setenv("EVALUATION_PRICE_PATH_LOOKBACK_DAYS", "45")

    config = Config.from_env()

    assert config.evaluation_cost_bps == 15
    assert config.evaluation_follow_through_pct == 4
    assert config.evaluation_failed_breakout_pct == -2.5
    assert config.evaluation_price_path_enabled is True
    assert config.evaluation_price_path_lookback_days == 45


def test_config_loads_extra_env_files(monkeypatch, tmp_path):
    env_file = tmp_path / "external.env"
    env_file.write_text(
        "\n".join([
            "LITELLM_MODEL=openai/test-model",
            "OPENAI_API_KEY=sk-from-file",
            "OPENAI_BASE_URL=https://example.test/v1",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("ALPHASIFT_ENV_FILES", str(env_file))

    config = Config.from_env()

    assert config.llm_model == "openai/test-model"
    assert config.llm_api_key == "sk-from-file"
    assert config.llm_base_url == "https://example.test/v1"


def test_empty_values_in_extra_env_file_do_not_block_later_files(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    first = tmp_path / "first.env"
    second = tmp_path / "second.env"
    first.write_text("GEMINI_API_KEY=\nGEMINI_MODEL=gemini-2.5-flash\n", encoding="utf-8")
    second.write_text("GEMINI_API_KEY=real-key\n", encoding="utf-8")
    monkeypatch.setenv("ALPHASIFT_ENV_FILES", os.pathsep.join([str(first), str(second)]))

    config = Config.from_env()

    assert config.llm_api_key == "real-key"
