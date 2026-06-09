from __future__ import annotations

DEFAULT_GOVERNANCE_POLICY_NAME = "stage5_default_governance"
DEFAULT_GOVERNANCE_POLICY_VERSION = "1.0.0"

DEFAULT_GOVERNANCE_RULES: tuple[dict[str, str], ...] = (
    {
        "rule_code": "VALID_MEMO_ONLY",
        "rule_scope": "senior_memo",
        "rule_value": "required",
        "severity": "hard_block",
        "description": "Context packages may consume only valid Senior Memos.",
    },
    {
        "rule_code": "VALID_RESEARCH_ONLY",
        "rule_scope": "research",
        "rule_value": "required",
        "severity": "hard_block",
        "description": "Context packages may consume only research packets with packet_status valid and QA passed.",
    },
    {
        "rule_code": "VALID_MACRO_ONLY",
        "rule_scope": "macro",
        "rule_value": "required",
        "severity": "hard_block",
        "description": "Context packages may consume only valid macro context packets.",
    },
    {
        "rule_code": "NO_AUTHORITY_ESCALATION",
        "rule_scope": "system",
        "rule_value": "required",
        "severity": "hard_block",
        "description": "Stage 5 artifacts are context and governance records, not order authority.",
    },
    {
        "rule_code": "MAX_CONTEXT_ITEMS",
        "rule_scope": "context",
        "rule_value": "50",
        "threshold_value": "50",
        "severity": "hard_block",
        "description": "Context packages fail validation above 50 items.",
    },
    {
        "rule_code": "CONTEXT_BUDGET_WARNING_ITEMS",
        "rule_scope": "context",
        "rule_value": "40",
        "threshold_value": "40",
        "severity": "warning",
        "description": "Context packages warn at 40 items.",
    },
    {
        "rule_code": "CANARY_REQUIRED_BEFORE_TEMPLATE_ACTIVATION",
        "rule_scope": "template",
        "rule_value": "required",
        "severity": "hard_block",
        "description": "Non-default or modified template activation requires the latest canary run to pass.",
    },
    {
        "rule_code": "READ_ONLY_INTEGRATION_ONLY",
        "rule_scope": "integration",
        "rule_value": "required",
        "severity": "hard_block",
        "description": "Stage 5 integration sources must be read-only.",
    },
)
