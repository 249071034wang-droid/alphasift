from alphasift.dsa_provider import apply_dsa_provider_context
from alphasift.models import Pick


def _pick(code: str, rank: int) -> Pick:
    return Pick(
        rank=rank,
        code=code,
        name=f"股票{code}",
        final_score=90.0 - rank,
        screen_score=90.0 - rank,
    )


def test_dsa_provider_respects_light_context_budget_without_news():
    calls: dict[str, list[str]] = {"quote": [], "fundamentals": [], "news": []}
    picks = [_pick("600519", 1), _pick("000858", 2), _pick("000001", 3)]

    def quote_provider(code: str):
        calls["quote"].append(code)
        return {"price": 10.0}

    def fundamentals_provider(code: str):
        calls["fundamentals"].append(code)
        return {"coverage": {"valuation": "available"}}

    def news_provider(code: str, name: str, max_results: int = 3):
        calls["news"].append(code)
        return {"success": True, "results": [{"title": f"{name}新闻"}]}

    notes = apply_dsa_provider_context(
        picks,
        {
            "dsa": {
                "mode": "pre_rank_light",
                "max_candidates": 2,
                "include_news": False,
                "get_realtime_quote": quote_provider,
                "get_fundamental_context": fundamentals_provider,
                "search_stock_news": news_provider,
            }
        },
    )

    assert calls["quote"] == ["600519", "000858"]
    assert calls["fundamentals"] == ["600519", "000858"]
    assert calls["news"] == []
    assert picks[0].dsa_context["news"]["skipped"] is True
    assert picks[0].dsa_news == []
    assert picks[2].dsa_context == {}
    assert notes == ["DSA provider context applied 2 of 2 candidates"]


def test_dsa_provider_passes_light_options_to_candidate_getter():
    captured: dict[str, object] = {}
    picks = [_pick("600519", 1)]

    def candidate_getter(code: str, name: str, **kwargs):
        captured["code"] = code
        captured["name"] = name
        captured["kwargs"] = kwargs
        return {
            "enriched": True,
            "quote": {"price": 1688.0},
            "news": {"success": True, "results": [{"title": "不应进入预筛提示"}]},
        }

    apply_dsa_provider_context(
        picks,
        {
            "dsa": {
                "mode": "pre_rank_light",
                "include_news": False,
                "get_candidate_context": candidate_getter,
            }
        },
    )

    assert captured["code"] == "600519"
    assert captured["name"] == "股票600519"
    assert captured["kwargs"] == {
        "include_news": False,
        "mode": "pre_rank_light",
        "include_fundamentals": True,
    }
    assert picks[0].dsa_context["news"]["skipped"] is True
    assert picks[0].dsa_news == []
