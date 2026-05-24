FINANCIAL_REPORT_PROMPT = """你是一位资深A股分析师。请分析以下公司的财务数据，并给出简要评估。

股票: {stock_name} ({symbol})
最新财务数据:
- 营业收入: {revenue}
- 净利润(归母): {net_profit}
- 每股收益: {eps}
- 净资产收益率: {roe}
- 总资产: {total_assets}
- 资产负债率: {debt_ratio}

请从以下角度分析（用中文，简洁）:
1. 盈利能力评价（1-2句）
2. 成长性判断（1-2句）
3. 财务健康度（1-2句）
4. 综合评分（0-100分）

请以JSON格式输出，包含字段: profit_assessment, growth_assessment, health_assessment, overall_score
"""

NEWS_SENTIMENT_PROMPT = """分析以下A股相关新闻的情绪倾向。

股票: {stock_name} ({symbol})
近期新闻:
{news_list}

请分析:
1. 整体情绪: positive / negative / neutral
2. 情绪评分: -100（极度负面）到 100（极度正面）
3. 关键影响因素（1-2句话）

请以JSON格式输出，包含字段: sentiment_label, sentiment_score, key_factors
"""

INDUSTRY_OUTLOOK_PROMPT = """你是A股行业分析师。请评估以下行业的前景。

行业: {industry}
所属公司: {stock_name} ({symbol})
近期行业动态:
{industry_context}

请分析:
1. 行业当前景气度: 高/中/低
2. 未来3-6个月趋势判断（1-2句）
3. 该股票在行业中的竞争地位（1-2句）

请以JSON格式输出，包含字段: prosperity, outlook, competitive_position
"""

COMPREHENSIVE_RECOMMENDATION_PROMPT = """你是一位资深A股投资顾问。请基于以下多维度分析，给出综合投资建议。

股票: {stock_name} ({symbol})
当前价格: {current_price}

财务分析: {financial_summary}
新闻情绪: {news_summary}
行业前景: {industry_summary}

量化模型评分:
- 综合得分: {composite_score}/100
- 预测收益率: {predicted_return}%
- 动量得分: {momentum_score}/100
- 质量得分: {quality_score}/100
- 风险等级: {risk_level}

请给出:
1. 投资建议摘要（2-3句话，包含核心逻辑）
2. 主要风险提示（列出2-3条）
3. 综合建议: "强烈推荐" / "推荐" / "中性" / "谨慎"

请以JSON格式输出，包含字段: summary, risk_flags (数组), recommendation_level
"""
