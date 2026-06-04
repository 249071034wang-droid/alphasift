# 策略文件说明

本目录存放选股策略 YAML 文件。

## 文件格式

每个 `.yaml` 文件定义一个选股策略，包含 `screening:` 段描述筛选规则。

详见 [策略编写指南](../docs/strategy-guide.md)。

内置策略不仅配置 `hard_filters` 和 `factor_weights`，也配置了风格化 profile：

- `scoring_profile`：因子评分曲线，例如追高惩罚、理想量比/换手
- `risk_profile`：风险阈值，例如异常量比、高换手、低置信度
- `portfolio_profile`：LLM 行业/主题风险桶
- `scorecard_profile`：默认 L3 scorecard 加减分规则

`capital_heat` 和 `balanced_alpha` 已包含可选 `theme_heat` 因子；当本地映射或 `industry-cache` 提供 `board_heat_score`、`board_heat_trend_score`、`board_heat_persistence_score`、`board_heat_cooling_score` 时，板块/主题热度、持续性和升温/降温趋势会进入软评分和 LLM 上下文。

## 可用策略

| 文件 | 名称 | 分类 | 说明 |
|------|------|------|------|
| `shrink_pullback.yaml` | 缩量回踩 | trend | L1 后候选级日 K 增强，识别均线多头与回踩结构 |
| `dual_low.yaml` | 双低选股 | value | 低 PE + 低 PB 稳健筛选 |
| `volume_breakout.yaml` | 放量突破 | trend | 放量突破关键阻力位 |
| `quality_value.yaml` | 稳健价值 | value | 估值合理、流动性充足、波动不过热 |
| `capital_heat.yaml` | 资金热度 | momentum | 资金活跃、量价同步但未极端过热 |
| `oversold_reversal.yaml` | 超跌反转 | reversal | 跌幅可控且流动性仍在的修复候选 |
| `balanced_alpha.yaml` | 均衡多因子 | framework | 综合估值、资金、动量、稳定性 |
| `momentum_quality.yaml` | 趋势质量 | framework | 兼顾趋势确认和基本面质量的中线候选发现 |

## 示例策略（可选，不计入内置策略）

`examples/` 子目录存放可选示例策略，不会被自动加载，也不改变内置策略列表。如需使用，将文件复制到本目录（仓库本地自定义策略机制会自动识别）：

| 文件 | 名称 | 分类 | 说明 |
|------|------|------|------|
| `examples/dual_low_us.yaml` | Dual Low (US) | value | 美股低 PE + 低 PB 价值筛选（`market_scope: [us]`，需安装 `yfinance` 并配合 `--market us`） |

```bash
cp strategies/examples/dual_low_us.yaml strategies/
alphasift screen dual_low_us --market us --no-llm
```

## 运行与评估

依赖日 K 的策略会自动在 L1 后对 Top N 候选做轻量增强，包括 MA、MACD/RSI、20 日突破幅度、区间振幅、20 日量能比、实体强度、MA20 回踩距离和平台持续天数：

```bash
alphasift screen shrink_pullback --no-llm
```

策略语义变化应更新 YAML 中的 `version`。保存运行后可做 T+N 后验评估，评估会标记突破延续、突破失败、MA20 回踩修复等形态状态：

```bash
alphasift screen balanced_alpha --no-llm --save-run
alphasift evaluate <run_id> --explain
```
