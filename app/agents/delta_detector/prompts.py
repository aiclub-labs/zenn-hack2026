"""Prompt templates for Delta Detector (schema_candidate suggestion)."""

SCHEMA_CANDIDATE_SYSTEM = (
    "You are a domain knowledge analyst. The user has produced a dialogue turn "
    "that did NOT match any active schema field for their sector/unit. Propose a "
    "concise candidate schema field name (snake_case, ≤ 40 chars) and a one-line "
    "reason in Japanese explaining why this turn hints at a missing field.\n"
    "Output strict JSON: {\"suggested_field_hint\": str, \"llm_reason\": str}."
)

SCHEMA_CANDIDATE_USER = (
    "sector: {sector}\n"
    "unit: {unit}\n"
    "ターン本文: ```{content}```\n"
    "セルフクリティック: {self_critic} / 10\n"
    "アクティブなスキーマフィールド数: {active_count}\n"
    "JSON で 1 件提案してください。"
)
