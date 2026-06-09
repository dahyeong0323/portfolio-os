# Portfolio OS Stage 2 Tech Spec — Risk-Gated Manual Operating Loop

> 목적: 이 문서는 Portfolio OS **Macro-Stage 2: Risk-Gated Manual Operating Loop** 구현을 위한 기술 명세서다.  
> Stage 2는 투자 판단 시스템이 아니라, **거래 행동을 시스템 안에 가두는 운영 루프**다.  
> 기준: Python 3.13, SQLite, `Decimal`, 표준 `argparse`, 표준 라이브러리 런타임, `pytest` 개발 의존성.

---

## 0. Stage 2 Goal

Stage 2의 목표는 단 하나다.

```text
모든 실제 거래가
1. risk-validated, human-approved order ticket
또는
2. declared override

중 하나에 연결되고,
실제 수동 체결은 provisional transaction으로 남아 다음 reconciliation에서 확인되는 것.
```

Stage 2는 다음 운영 루프를 만든다.

```text
LedgerSnapshot
 -> Transaction Intent
 -> Risk Validation
 -> Manual Order Ticket
 -> Human Approval / Reject / Modify
 -> Human Manual Execution
 -> Manual Execution Log
 -> Stage 1 provisional transaction
 -> Next Reconciliation
 -> Execution confirmed or broken
 -> Decision Journal / Post-Mortem
```

---

## 1. Stage 1 Contracts That Must Be Preserved

Stage 2는 Stage 1을 재구현하지 않는다. Stage 2는 Stage 1의 안정 계약을 소비한다.

### 1.1 Stable Stage 1 Inputs

Stage 2가 신뢰하고 재사용해야 하는 Stage 1 계약:

```text
DB connection layer
Migration system
schema_migrations
Decimal policy
accounts repository
instruments repository
transactions repository
cash_balances as internal OS cash anchors only
LedgerSnapshotBuilder
ReconciliationService
LedgerStateMachine
External snapshot import boundary
Reconciliation report export path
```

Stage 2는 반드시 `LedgerSnapshot`과 `ledger_status`를 사용한다. Stage 2가 자체적으로 “진짜 장부”를 다시 계산하면 안 된다.

### 1.2 Non-Breakable Stage 1 Invariants

```text
No external snapshot values into cash_balances.
No bypassing reconciliation before treating ledger as reconciled.
No direct mutation of historical transactions.
No float arithmetic.
No risk or order logic that ignores ledger_status.
No Stage 1 schema modification without migration.
No moving existing root documents.
No treating external snapshot artifacts as internal ledger facts.
```

---

## 2. Stage 2 Scope

### 2.1 Implemented in Stage 2

- 가격 스냅샷
- 환율 스냅샷
- 종목 리스크 프로필
- 리스크 정책 버전
- 리스크 규칙
- 거래 의도
- 리스크 검증 결과
- 수동 주문 티켓
- 주문 티켓 이벤트 로그
- 인간 승인/거절/수정 상태
- 수동 체결 로그
- provisional transaction 생성 연결
- declared override ticket
- decision journal
- post-mortem task
- markdown/json risk and ticket report
- Stage 2 CLI
- Stage 2 tests

### 2.2 Explicitly Not Implemented in Stage 2

- 자동 주문 실행
- 외부 계좌 쓰기 연동
- 투자 리서치 생성
- 거시경제/상관관계 분석
- 투자 판단 메모 생성
- 대화형 투자 비서
- 실시간 시세 스트리밍
- 복잡한 GUI
- 고급 알림 어댑터
- 모델/프롬프트 평가 체계
- 장기 기억/문서 검색 계층

---

## 3. Global Engineering Rules

### 3.1 Decimal Policy

Stage 1 정책을 그대로 유지한다.

```text
Python type: Decimal
DB storage: canonical decimal string
SQLite declared type: DECIMAL_TEXT or TEXT
Forbidden: float
```

모든 수량, 금액, 가격, 환율, 수수료, 세금, 한도 계산은 `Decimal`로 한다.

### 3.2 Append-Only Audit Policy

Stage 2 핵심 객체들은 상태가 바뀌더라도 이벤트 또는 저널을 남긴다.

```text
risk_validation_results: immutable
order_tickets: current status + event log
order_ticket_events: append-only
manual_execution_logs: append-only unless voided
override_tickets: current status + journal
decision_journal: append-only
```

### 3.3 No Automatic Execution Policy

Stage 2는 실제 주문을 실행하지 않는다.

```text
System creates ticket.
Human approves ticket.
Human manually executes outside the system.
Human logs actual execution.
System records provisional transaction.
Next reconciliation confirms.
```

---

# 4. Database Schema — Stage 2 Additions

Stage 2는 Stage 1 테이블을 직접 수정하지 않고 새 migration으로 확장한다.

권장 migration 번호:

```text
009_create_price_snapshots.sql
010_create_fx_rates.sql
011_create_instrument_risk_profiles.sql
012_create_risk_policy_versions.sql
013_create_risk_rules.sql
014_create_transaction_intents.sql
015_create_risk_validation_results.sql
016_create_order_tickets.sql
017_create_order_ticket_events.sql
018_create_manual_execution_logs.sql
019_create_override_tickets.sql
020_create_decision_journal.sql
021_create_postmortem_tasks.sql
022_create_stage2_indexes.sql
```

---

## 4.1 `price_snapshots`

### Role

리스크 검증 시 포지션 평가금액, 주문 예상 금액, 자산 비중 계산에 사용할 가격 기준을 저장한다. Stage 2에서는 수동 또는 CSV 기반 가격 입력만 다룬다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `price_snapshot_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `instrument_id` | INTEGER | int | No | Yes | No | `REFERENCES instruments(instrument_id)` |
| `price_date` | TEXT | date str | No | No | No | `YYYY-MM-DD` |
| `price_timestamp` | TEXT | datetime str | No | No | Yes | UTC ISO-8601 |
| `currency` | TEXT | str | No | No | No | 3-letter code |
| `price` | DECIMAL_TEXT | Decimal | No | No | No | canonical decimal string |
| `source` | TEXT | str | No | No | No | `manual/csv_import/system_correction` |
| `source_ref` | TEXT | str | No | No | Yes | 원본 파일/행 |
| `is_active` | INTEGER | bool | No | No | No | `0/1` |
| `notes` | TEXT | str | No | No | Yes | 비고 |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

Indexes:

```text
uq_price_snapshots_instrument_date_source(instrument_id, price_date, source, source_ref)
idx_price_snapshots_instrument_date(instrument_id, price_date)
idx_price_snapshots_active(is_active)
```

---

## 4.2 `fx_rates`

### Role

계좌 기준 통화와 주문/종목 통화가 다를 때 환산에 사용한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `fx_rate_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `rate_date` | TEXT | date str | No | No | No | `YYYY-MM-DD` |
| `base_currency` | TEXT | str | No | No | No | 3-letter code |
| `quote_currency` | TEXT | str | No | No | No | 3-letter code |
| `rate` | DECIMAL_TEXT | Decimal | No | No | No | `1 base_currency = rate quote_currency` |
| `source` | TEXT | str | No | No | No | `manual/csv_import/system_correction` |
| `source_ref` | TEXT | str | No | No | Yes | 원본 파일/행 |
| `is_active` | INTEGER | bool | No | No | No | `0/1` |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

Indexes:

```text
uq_fx_rates_pair_date_source(rate_date, base_currency, quote_currency, source, source_ref)
idx_fx_rates_pair_date(base_currency, quote_currency, rate_date)
idx_fx_rates_active(is_active)
```

---

## 4.3 `instrument_risk_profiles`

### Role

종목별 리스크 bucket과 특별 제한을 저장한다. 이는 판단 정보가 아니라 deterministic risk check를 위한 기준 정보다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `risk_profile_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `instrument_id` | INTEGER | int | No | Yes | No | `REFERENCES instruments(instrument_id)` |
| `risk_bucket` | TEXT | str | No | No | No | `core_equity/leveraged_etf/crypto/high_growth/cash_equivalent/other` |
| `is_leveraged` | INTEGER | bool | No | No | No | `0/1` |
| `is_crypto_related` | INTEGER | bool | No | No | No | `0/1` |
| `is_single_name_equity` | INTEGER | bool | No | No | No | `0/1` |
| `max_asset_weight_override` | DECIMAL_TEXT | Decimal | No | No | Yes | ratio |
| `max_order_notional_override` | DECIMAL_TEXT | Decimal | No | No | Yes | amount |
| `is_active` | INTEGER | bool | No | No | No | `0/1` |
| `notes` | TEXT | str | No | No | Yes | 비고 |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `updated_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

Indexes:

```text
uq_instrument_risk_profiles_instrument(instrument_id)
idx_instrument_risk_profiles_bucket(risk_bucket)
idx_instrument_risk_profiles_active(is_active)
```

---

## 4.4 `risk_policy_versions`

### Role

리스크 규칙 묶음을 버전 관리한다. 모든 risk validation은 어떤 정책 버전으로 계산됐는지 저장해야 한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `policy_version_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `policy_name` | TEXT | str | No | No | No | 예: `stage2_default_policy` |
| `version` | TEXT | str | No | No | No | 예: `v1.0.0` |
| `base_currency` | TEXT | str | No | No | No | 기준 계산 통화 |
| `is_active` | INTEGER | bool | No | No | No | active policy |
| `description` | TEXT | str | No | No | Yes | 설명 |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

Indexes:

```text
uq_risk_policy_versions_name_version(policy_name, version)
uq_one_active_risk_policy(is_active) WHERE is_active = 1
idx_risk_policy_versions_active(is_active)
```

---

## 4.5 `risk_rules`

### Role

리스크 정책 버전에 속한 개별 hard rule을 저장한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `risk_rule_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `policy_version_id` | INTEGER | int | No | Yes | No | `REFERENCES risk_policy_versions(policy_version_id)` |
| `rule_code` | TEXT | str | No | No | No | 예: `MIN_CASH_RESERVE` |
| `rule_scope` | TEXT | str | No | No | No | `global/account/instrument/bucket` |
| `account_id` | INTEGER | int | No | Yes | Yes | `REFERENCES accounts(account_id)` |
| `instrument_id` | INTEGER | int | No | Yes | Yes | `REFERENCES instruments(instrument_id)` |
| `risk_bucket` | TEXT | str | No | No | Yes | bucket rule |
| `threshold_value` | DECIMAL_TEXT | Decimal | No | No | No | rule threshold |
| `threshold_unit` | TEXT | str | No | No | No | `amount/ratio/count` |
| `currency` | TEXT | str | No | No | Yes | amount rule currency |
| `severity` | TEXT | str | No | No | No | `hard_block/adjust_down/warn` |
| `is_active` | INTEGER | bool | No | No | No | `0/1` |
| `description` | TEXT | str | No | No | Yes | 설명 |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `updated_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

Indexes:

```text
idx_risk_rules_policy(policy_version_id)
idx_risk_rules_code(rule_code)
idx_risk_rules_active(is_active)
```

---

## 4.6 `transaction_intents`

### Role

아직 주문 티켓이 아닌 “거래 의도”를 저장한다. 모든 official order ticket은 transaction intent에서 시작해야 한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `intent_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `account_id` | INTEGER | int | No | Yes | No | `REFERENCES accounts(account_id)` |
| `instrument_id` | INTEGER | int | No | Yes | No | `REFERENCES instruments(instrument_id)` |
| `intent_type` | TEXT | str | No | No | No | `buy/sell` |
| `intent_source` | TEXT | str | No | No | No | `manual/correction/override_precheck` |
| `requested_quantity` | DECIMAL_TEXT | Decimal | No | No | Yes | requested quantity |
| `requested_notional` | DECIMAL_TEXT | Decimal | No | No | Yes | requested notional |
| `limit_price` | DECIMAL_TEXT | Decimal | No | No | Yes | limit price |
| `currency` | TEXT | str | No | No | No | order currency |
| `order_type` | TEXT | str | No | No | No | Stage 2 allows only `limit` |
| `rationale` | TEXT | str | No | No | Yes | human rationale |
| `status` | TEXT | str | No | No | No | intent state |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `updated_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `expires_at` | TEXT | datetime str | No | No | Yes | intent expiry |

Validation:

```text
requested_quantity or requested_notional must exist.
requested_quantity and requested_notional cannot be negative.
order_type must be limit.
buy is risk_increasing.
sell is risk_reducing only if current holdings are sufficient.
```

---

## 4.7 `risk_validation_results`

### Role

특정 거래 의도에 대한 deterministic risk engine 결과를 저장한다. Order ticket은 반드시 `passed` 또는 `adjusted` validation에서만 생성된다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `risk_validation_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `intent_id` | INTEGER | int | No | Yes | No | `REFERENCES transaction_intents(intent_id)` |
| `policy_version_id` | INTEGER | int | No | Yes | No | `REFERENCES risk_policy_versions(policy_version_id)` |
| `reconciliation_id` | INTEGER | int | No | Yes | Yes | `REFERENCES reconciliation_snapshots(reconciliation_id)` |
| `ledger_status_at_validation` | TEXT | str | No | No | No | `reconciled/provisional/stale/broken` |
| `ledger_snapshot_as_of` | TEXT | date str | No | No | No | validation basis date |
| `ledger_snapshot_digest` | TEXT | str | No | No | Yes | snapshot digest |
| `validation_status` | TEXT | str | No | No | No | `passed/rejected/adjusted` |
| `action_class` | TEXT | str | No | No | No | `risk_increasing/risk_reducing/correction/override_precheck` |
| `requested_quantity` | DECIMAL_TEXT | Decimal | No | No | Yes | original quantity |
| `requested_notional` | DECIMAL_TEXT | Decimal | No | No | Yes | original notional |
| `approved_quantity` | DECIMAL_TEXT | Decimal | No | No | Yes | passed/adjusted quantity |
| `approved_notional` | DECIMAL_TEXT | Decimal | No | No | Yes | passed/adjusted notional |
| `max_allowed_notional` | DECIMAL_TEXT | Decimal | No | No | Yes | calculated max |
| `currency` | TEXT | str | No | No | No | order currency |
| `cash_before` | DECIMAL_TEXT | Decimal | No | No | Yes | before trade |
| `cash_after` | DECIMAL_TEXT | Decimal | No | No | Yes | after trade |
| `tax_reserve_required` | DECIMAL_TEXT | Decimal | No | No | Yes | protected reserve |
| `checks_json` | TEXT | str | No | No | No | per-check results |
| `failure_reasons_json` | TEXT | str | No | No | No | failure reasons |
| `warnings_json` | TEXT | str | No | No | No | warnings |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `expires_at` | TEXT | datetime str | No | No | Yes | validation expiry |
| `is_superseded` | INTEGER | bool | No | No | No | `0/1` |

---

## 4.8 `order_tickets`

### Role

인간이 실제 외부 계좌 화면에서 수동 실행할 수 있도록 생성되는 검증된 주문 티켓이다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `order_ticket_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `intent_id` | INTEGER | int | No | Yes | No | `REFERENCES transaction_intents(intent_id)` |
| `risk_validation_id` | INTEGER | int | No | Yes | No | `REFERENCES risk_validation_results(risk_validation_id)` |
| `account_id` | INTEGER | int | No | Yes | No | `REFERENCES accounts(account_id)` |
| `instrument_id` | INTEGER | int | No | Yes | No | `REFERENCES instruments(instrument_id)` |
| `side` | TEXT | str | No | No | No | `buy/sell` |
| `order_type` | TEXT | str | No | No | No | Stage 2 only `limit` |
| `ticket_quantity` | DECIMAL_TEXT | Decimal | No | No | No | approved quantity |
| `limit_price` | DECIMAL_TEXT | Decimal | No | No | Yes | limit price |
| `ticket_notional` | DECIMAL_TEXT | Decimal | No | No | No | approved notional |
| `currency` | TEXT | str | No | No | No | order currency |
| `status` | TEXT | str | No | No | No | ticket state |
| `human_decision` | TEXT | str | No | No | Yes | `approved/rejected/modified/cancelled` |
| `human_decision_reason` | TEXT | str | No | No | Yes | reason |
| `approved_at` | TEXT | datetime str | No | No | Yes | UTC ISO-8601 |
| `rejected_at` | TEXT | datetime str | No | No | Yes | UTC ISO-8601 |
| `expires_at` | TEXT | datetime str | No | No | No | ticket expiry |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `updated_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

Rule:

```text
No order ticket can be created from rejected validation.
No order ticket can be created from expired validation.
No ticket can be executed unless status = approved.
```

---

## 4.9 `order_ticket_events`

### Role

주문 티켓의 모든 상태 변화를 append-only로 기록한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `event_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `order_ticket_id` | INTEGER | int | No | Yes | No | `REFERENCES order_tickets(order_ticket_id)` |
| `event_type` | TEXT | str | No | No | No | `created/approved/rejected/modified/expired/execution_logged/reconciled/broken` |
| `from_status` | TEXT | str | No | No | Yes | previous status |
| `to_status` | TEXT | str | No | No | No | next status |
| `event_payload_json` | TEXT | str | No | No | No | event payload |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

---

## 4.10 `manual_execution_logs`

### Role

인간이 실제로 수동 체결한 내용을 기록한다. 공식 티켓 또는 override 중 정확히 하나에 연결되어야 한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `manual_execution_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `order_ticket_id` | INTEGER | int | No | Yes | Yes | `REFERENCES order_tickets(order_ticket_id)` |
| `override_ticket_id` | INTEGER | int | No | Yes | Yes | `REFERENCES override_tickets(override_ticket_id)` |
| `created_transaction_id` | INTEGER | int | No | Yes | Yes | `REFERENCES transactions(transaction_id)` |
| `account_id` | INTEGER | int | No | Yes | No | `REFERENCES accounts(account_id)` |
| `instrument_id` | INTEGER | int | No | Yes | No | `REFERENCES instruments(instrument_id)` |
| `side` | TEXT | str | No | No | No | `buy/sell` |
| `executed_quantity` | DECIMAL_TEXT | Decimal | No | No | No | actual quantity |
| `executed_price` | DECIMAL_TEXT | Decimal | No | No | No | actual price |
| `gross_amount` | DECIMAL_TEXT | Decimal | No | No | No | gross |
| `fee_amount` | DECIMAL_TEXT | Decimal | No | No | No | fee |
| `tax_amount` | DECIMAL_TEXT | Decimal | No | No | No | tax |
| `net_cash_amount` | DECIMAL_TEXT | Decimal | No | No | No | buy negative, sell positive |
| `currency` | TEXT | str | No | No | No | execution currency |
| `executed_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `broker_execution_ref` | TEXT | str | No | No | Yes | optional external ref |
| `execution_status` | TEXT | str | No | No | No | execution state |
| `reconciliation_deadline` | TEXT | date str | No | No | Yes | deadline |
| `reconciled_at` | TEXT | datetime str | No | No | Yes | confirmed time |
| `reconciliation_id` | INTEGER | int | No | Yes | Yes | `REFERENCES reconciliation_snapshots(reconciliation_id)` |
| `notes` | TEXT | str | No | No | Yes | notes |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `updated_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

Constraint:

```sql
CHECK (
  (order_ticket_id IS NOT NULL AND override_ticket_id IS NULL)
  OR
  (order_ticket_id IS NULL AND override_ticket_id IS NOT NULL)
)
```

---

## 4.11 `override_tickets`

### Role

공식 risk/order 루프 밖에서 인간이 거래하려는 상황을 기록 가능한 예외로 흡수한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `override_ticket_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `override_type` | TEXT | str | No | No | No | `emergency_buy/manual_correction/no_sync/thesis_conviction/panic/other` |
| `account_id` | INTEGER | int | No | Yes | No | `REFERENCES accounts(account_id)` |
| `instrument_id` | INTEGER | int | No | Yes | Yes | `REFERENCES instruments(instrument_id)` |
| `side` | TEXT | str | No | No | Yes | `buy/sell` |
| `requested_quantity` | DECIMAL_TEXT | Decimal | No | No | Yes | requested quantity |
| `requested_notional` | DECIMAL_TEXT | Decimal | No | No | Yes | requested notional |
| `currency` | TEXT | str | No | No | Yes | currency |
| `ledger_status_at_declaration` | TEXT | str | No | No | No | ledger status |
| `risk_warning` | TEXT | str | No | No | No | warning text |
| `max_suggested_notional` | DECIMAL_TEXT | Decimal | No | No | Yes | optional max |
| `human_reason` | TEXT | str | No | No | No | required reason |
| `human_final_choice` | TEXT | str | No | No | Yes | `execute/cancel/modify` |
| `status` | TEXT | str | No | No | No | override state |
| `mandatory_reconciliation_deadline` | TEXT | date str | No | No | Yes | deadline |
| `mandatory_postmortem_date` | TEXT | date str | No | No | Yes | postmortem date |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `updated_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

---

## 4.12 `decision_journal`

### Role

거래 관련 인간 의사결정을 append-only로 기록한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `decision_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `decision_type` | TEXT | str | No | No | No | `ticket_approval/ticket_rejection/ticket_modification/override_declared/manual_execution_logged/postmortem` |
| `order_ticket_id` | INTEGER | int | No | Yes | Yes | `REFERENCES order_tickets(order_ticket_id)` |
| `override_ticket_id` | INTEGER | int | No | Yes | Yes | `REFERENCES override_tickets(override_ticket_id)` |
| `risk_validation_id` | INTEGER | int | No | Yes | Yes | `REFERENCES risk_validation_results(risk_validation_id)` |
| `manual_execution_id` | INTEGER | int | No | Yes | Yes | `REFERENCES manual_execution_logs(manual_execution_id)` |
| `human_decision` | TEXT | str | No | No | No | decision |
| `reason` | TEXT | str | No | No | Yes | reason |
| `emotional_state` | TEXT | str | No | No | Yes | optional |
| `context_json` | TEXT | str | No | No | No | context snapshot |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

---

## 4.13 `postmortem_tasks`

### Role

override 또는 중요한 거래에 대해 나중에 복기해야 할 항목을 예약한다.

| Column | SQLite Type | Python Type | PK | FK | Nullable | Notes |
|---|---:|---|---|---|---|---|
| `postmortem_task_id` | INTEGER | int | Yes | No | No | `PRIMARY KEY AUTOINCREMENT` |
| `order_ticket_id` | INTEGER | int | No | Yes | Yes | `REFERENCES order_tickets(order_ticket_id)` |
| `override_ticket_id` | INTEGER | int | No | Yes | Yes | `REFERENCES override_tickets(override_ticket_id)` |
| `due_date` | TEXT | date str | No | No | No | `YYYY-MM-DD` |
| `status` | TEXT | str | No | No | No | `scheduled/completed/cancelled/overdue` |
| `prompt_questions_json` | TEXT | str | No | No | No | questions |
| `completed_decision_id` | INTEGER | int | No | Yes | Yes | `REFERENCES decision_journal(decision_id)` |
| `created_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |
| `updated_at` | TEXT | datetime str | No | No | No | UTC ISO-8601 |

---

# 5. State Machine Definitions

## 5.1 Transaction Intent State Machine

States:

```text
drafted
submitted
risk_passed
risk_adjusted
risk_rejected
ticket_created
cancelled
superseded
```

Transitions:

| From | Trigger | Condition | To |
|---|---|---|---|
| none | create intent | valid account/instrument/side/quantity or notional | `drafted` |
| `drafted` | submit for validation | required fields valid | `submitted` |
| `submitted` | risk validation passed | `validation_status = passed` | `risk_passed` |
| `submitted` | risk validation adjusted | `validation_status = adjusted` | `risk_adjusted` |
| `submitted` | risk validation rejected | `validation_status = rejected` | `risk_rejected` |
| `risk_passed` | create order ticket | validation not expired | `ticket_created` |
| `risk_adjusted` | create adjusted order ticket | human accepts adjusted size | `ticket_created` |
| any active | cancel intent | no executed ticket exists | `cancelled` |
| any active | modified intent created | original no longer current | `superseded` |

---

## 5.2 Risk Validation Status

Risk validation is immutable after creation.

| Status | Meaning | Ticket Creation |
|---|---|---|
| `passed` | 요청 의도가 모든 hard rule 통과 | allowed |
| `adjusted` | 요청 크기는 너무 크지만 더 작은 크기는 허용 | allowed only with adjusted values |
| `rejected` | official ticket 불가 | not allowed |

---

## 5.3 Order Ticket State Machine

States:

```text
validated
approved
rejected
modified
expired
executed_provisional
reconciled
broken
cancelled
```

Transitions:

| From | Trigger | Condition | To |
|---|---|---|---|
| none | create ticket | risk validation passed/adjusted | `validated` |
| `validated` | human approves | before expiry | `approved` |
| `validated` | human rejects | reason recorded | `rejected` |
| `validated` | human modifies | new intent created | `modified` |
| `validated` | time passes | now > expires_at | `expired` |
| `approved` | manual execution logged | valid execution input | `executed_provisional` |
| `approved` | time passes | now > expires_at and no execution | `expired` |
| `executed_provisional` | reconciliation passed | linked transaction confirmed | `reconciled` |
| `executed_provisional` | reconciliation failed | mismatch detected | `broken` |
| any non-terminal | cancel | no execution logged | `cancelled` |

Terminal states:

```text
rejected
expired
reconciled
broken
cancelled
```

---

## 5.4 Manual Execution State Machine

States:

```text
logged
transaction_created
pending_reconciliation
reconciled
reconciliation_failed
voided
```

Transitions:

| From | Trigger | Condition | To |
|---|---|---|---|
| none | log manual execution | approved ticket or confirmed override | `logged` |
| `logged` | create Stage 1 transaction | valid sign convention | `transaction_created` |
| `transaction_created` | insert transaction with `is_confirmed = 0` | ledger becomes provisional | `pending_reconciliation` |
| `pending_reconciliation` | reconciliation passed after execution | linked transaction confirmed | `reconciled` |
| `pending_reconciliation` | reconciliation failed | mismatch detected | `reconciliation_failed` |
| any before reconciled | void execution log | correction required | `voided` |

---

## 5.5 Override Ticket State Machine

States:

```text
declared
risk_warned
human_confirmed
cancelled
executed_provisional
reconciled
postmortem_due
postmortem_completed
```

Transitions:

| From | Trigger | Condition | To |
|---|---|---|---|
| none | declare override | reason and ledger status recorded | `declared` |
| `declared` | show risk warning | warning persisted | `risk_warned` |
| `risk_warned` | human confirms | final choice = execute | `human_confirmed` |
| `risk_warned` | human cancels | final choice = cancel | `cancelled` |
| `human_confirmed` | manual execution logged | valid execution input | `executed_provisional` |
| `executed_provisional` | reconciliation passed | linked execution confirmed | `reconciled` |
| `reconciled` | postmortem date reached | postmortem required | `postmortem_due` |
| `postmortem_due` | journal entry recorded | postmortem completed | `postmortem_completed` |

---

# 6. Risk Engine Policy

## 6.1 Action Classes

| Action Class | Examples | Ledger Gate |
|---|---|---|
| `risk_increasing` | buy, adding exposure | requires `reconciled` |
| `risk_reducing` | sell existing holding | allowed in `reconciled/provisional/stale`; special handling if `broken` |
| `correction` | accounting correction | allowed when needed |
| `override_precheck` | declared exception | allowed but not official ticket |

---

## 6.2 Ledger Status Gate

| Ledger Status | Risk-Increasing Official Ticket | Risk-Reducing Official Ticket | Override Ticket | Correction Flow |
|---|---|---|---|---|
| `reconciled` | allowed after validation | allowed after validation | allowed | allowed |
| `provisional` | blocked | allowed with warning | allowed | allowed |
| `stale` | blocked | allowed with warning | allowed | allowed |
| `broken` | blocked | blocked as official ticket | allowed | allowed |

Important:

```text
No reconciled ledger, no risk-increasing official ticket.
No broken ledger official ticket.
Broken ledger can still accept correction flow and declared override.
```

---

## 6.3 Required Risk Checks

| Check Code | Description | Required For |
|---|---|---|
| `LEDGER_STATUS_GATE` | ledger_status 기반 official ticket 가능 여부 | all |
| `PRICE_AVAILABLE` | 기준 가격 존재 여부 | buy/sell |
| `FX_AVAILABLE` | 필요한 환율 존재 여부 | cross-currency |
| `NO_MARKET_ORDER` | market order 금지 | all |
| `CASH_AVAILABLE` | buy 후 현금 음수 방지 | buy |
| `TAX_RESERVE_PROTECTION` | 세금 준비금 침범 방지 | buy |
| `MIN_CASH_RESERVE` | 최소 현금 버퍼 보호 | buy |
| `DAILY_BUY_LIMIT` | 일일 매수 한도 | buy |
| `WEEKLY_BUY_LIMIT` | 주간 매수 한도 | buy |
| `MAX_ORDER_NOTIONAL` | 단일 주문 금액 한도 | buy |
| `MAX_ASSET_WEIGHT` | 주문 후 종목 비중 한도 | buy |
| `MAX_BUCKET_WEIGHT` | 주문 후 bucket 비중 한도 | buy |
| `HOLDING_AVAILABLE_FOR_SELL` | 보유 수량 초과 매도 금지 | sell |
| `DEBT_EXPOSURE_CHECK` | 부채가 과도할 때 신규 위험 차단 | buy |
| `DECIMAL_VALIDATION` | float/invalid decimal 차단 | all |

---

## 6.4 Validation Result Logic

Pseudo-logic:

```text
if ledger gate blocks official ticket:
    return REJECTED

if required price/fx/cash/tax data missing:
    return REJECTED

if sell quantity > current holding:
    return REJECTED

if buy violates hard non-adjustable rule:
    return REJECTED

if buy amount exceeds adjustable limits:
    compute max_allowed_notional

    if max_allowed_notional > 0:
        return ADJUSTED
    else:
        return REJECTED

if all checks pass:
    return PASSED
```

Adjustable rules:

```text
DAILY_BUY_LIMIT
WEEKLY_BUY_LIMIT
MAX_ORDER_NOTIONAL
MAX_ASSET_WEIGHT
MAX_BUCKET_WEIGHT
MIN_CASH_RESERVE
```

Non-adjustable hard rules:

```text
NO_MARKET_ORDER
LEDGER_STATUS_GATE
PRICE_AVAILABLE
FX_AVAILABLE
DECIMAL_VALIDATION
HOLDING_AVAILABLE_FOR_SELL
```

---

# 7. Core Interface & Function Signatures

## 7.1 Common Types

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional


CurrencyCode = str

LedgerStatus = Literal["reconciled", "provisional", "stale", "broken"]
IntentType = Literal["buy", "sell"]
RiskValidationStatus = Literal["passed", "rejected", "adjusted"]
ActionClass = Literal["risk_increasing", "risk_reducing", "correction", "override_precheck"]

IntentStatus = Literal[
    "drafted", "submitted", "risk_passed", "risk_adjusted", "risk_rejected",
    "ticket_created", "cancelled", "superseded",
]

OrderTicketStatus = Literal[
    "validated", "approved", "rejected", "modified", "expired",
    "executed_provisional", "reconciled", "broken", "cancelled",
]

ManualExecutionStatus = Literal[
    "logged", "transaction_created", "pending_reconciliation",
    "reconciled", "reconciliation_failed", "voided",
]

OverrideStatus = Literal[
    "declared", "risk_warned", "human_confirmed", "cancelled",
    "executed_provisional", "reconciled", "postmortem_due", "postmortem_completed",
]
```

---

## 7.2 Core Data Models

```python
@dataclass(frozen=True)
class TransactionIntent:
    intent_id: int
    account_id: int
    instrument_id: int
    intent_type: IntentType
    intent_source: str
    requested_quantity: Optional[Decimal]
    requested_notional: Optional[Decimal]
    limit_price: Optional[Decimal]
    currency: CurrencyCode
    order_type: Literal["limit"]
    rationale: Optional[str]
    status: IntentStatus
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]


@dataclass(frozen=True)
class RiskCheckResult:
    check_code: str
    status: Literal["passed", "failed", "adjusted", "warning"]
    message: str
    threshold_value: Optional[Decimal]
    observed_value: Optional[Decimal]
    adjusted_value: Optional[Decimal]


@dataclass(frozen=True)
class RiskValidationResult:
    risk_validation_id: Optional[int]
    intent_id: int
    policy_version_id: int
    reconciliation_id: Optional[int]
    ledger_status_at_validation: LedgerStatus
    ledger_snapshot_as_of: date
    ledger_snapshot_digest: Optional[str]
    validation_status: RiskValidationStatus
    action_class: ActionClass
    requested_quantity: Optional[Decimal]
    requested_notional: Optional[Decimal]
    approved_quantity: Optional[Decimal]
    approved_notional: Optional[Decimal]
    max_allowed_notional: Optional[Decimal]
    currency: CurrencyCode
    cash_before: Optional[Decimal]
    cash_after: Optional[Decimal]
    tax_reserve_required: Optional[Decimal]
    checks: tuple[RiskCheckResult, ...]
    failure_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at: datetime
    expires_at: Optional[datetime]
    is_superseded: bool


@dataclass(frozen=True)
class OrderTicket:
    order_ticket_id: int
    intent_id: int
    risk_validation_id: int
    account_id: int
    instrument_id: int
    side: IntentType
    order_type: Literal["limit"]
    ticket_quantity: Decimal
    limit_price: Optional[Decimal]
    ticket_notional: Decimal
    currency: CurrencyCode
    status: OrderTicketStatus
    human_decision: Optional[str]
    human_decision_reason: Optional[str]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
```

```python
@dataclass(frozen=True)
class ManualExecutionLog:
    manual_execution_id: int
    order_ticket_id: Optional[int]
    override_ticket_id: Optional[int]
    created_transaction_id: Optional[int]
    account_id: int
    instrument_id: int
    side: IntentType
    executed_quantity: Decimal
    executed_price: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    net_cash_amount: Decimal
    currency: CurrencyCode
    executed_at: datetime
    broker_execution_ref: Optional[str]
    execution_status: ManualExecutionStatus
    reconciliation_deadline: Optional[date]
    reconciled_at: Optional[datetime]
    reconciliation_id: Optional[int]
    notes: Optional[str]


@dataclass(frozen=True)
class OverrideTicket:
    override_ticket_id: int
    override_type: str
    account_id: int
    instrument_id: Optional[int]
    side: Optional[IntentType]
    requested_quantity: Optional[Decimal]
    requested_notional: Optional[Decimal]
    currency: Optional[CurrencyCode]
    ledger_status_at_declaration: LedgerStatus
    risk_warning: str
    max_suggested_notional: Optional[Decimal]
    human_reason: str
    human_final_choice: Optional[str]
    status: OverrideStatus
    mandatory_reconciliation_deadline: Optional[date]
    mandatory_postmortem_date: Optional[date]
    created_at: datetime
    updated_at: datetime
```

---

## 7.3 Service Interfaces

```python
class RiskEngine:
    def classify_action(
        self,
        intent: TransactionIntent,
        ledger_snapshot: "LedgerSnapshot",
    ) -> ActionClass:
        """Classify intent before risk validation."""

    def validate_intent(
        self,
        intent: TransactionIntent,
        ledger_snapshot: "LedgerSnapshot",
        policy_version_id: int,
        as_of_date: date,
    ) -> RiskValidationResult:
        """Run deterministic risk checks and return passed/rejected/adjusted."""


class OrderTicketService:
    def create_ticket_from_validation(
        self,
        risk_validation_id: int,
        expires_at: datetime,
    ) -> OrderTicket:
        """Create order ticket only from passed or adjusted validation."""

    def approve_ticket(
        self,
        order_ticket_id: int,
        reason: Optional[str],
    ) -> OrderTicket:
        """Human approves a validated ticket."""

    def reject_ticket(
        self,
        order_ticket_id: int,
        reason: str,
    ) -> OrderTicket:
        """Human rejects a validated ticket."""

    def modify_ticket(
        self,
        order_ticket_id: int,
        requested_quantity: Optional[Decimal],
        requested_notional: Optional[Decimal],
        reason: str,
    ) -> TransactionIntent:
        """Mark original ticket modified and create a new intent."""


class ManualExecutionService:
    def log_execution_for_ticket(
        self,
        order_ticket_id: int,
        executed_quantity: Decimal,
        executed_price: Decimal,
        fee_amount: Decimal,
        tax_amount: Decimal,
        executed_at: datetime,
        broker_execution_ref: Optional[str],
    ) -> ManualExecutionLog:
        """Log human manual execution for an approved ticket."""

    def create_provisional_transaction(
        self,
        execution_id: int,
    ) -> int:
        """Create Stage 1 transaction with is_confirmed=0."""

    def mark_reconciled_after_passed_reconciliation(
        self,
        reconciliation_id: int,
    ) -> int:
        """Mark pending executions reconciled after a passed reconciliation."""


class OverrideService:
    def declare_override(
        self,
        override_type: str,
        account_id: int,
        instrument_id: Optional[int],
        side: Optional[IntentType],
        requested_quantity: Optional[Decimal],
        requested_notional: Optional[Decimal],
        currency: Optional[CurrencyCode],
        human_reason: str,
    ) -> OverrideTicket:
        """Create declared override with ledger status and warning."""

    def confirm_override(
        self,
        override_ticket_id: int,
        final_choice: str,
    ) -> OverrideTicket:
        """Human confirms or cancels override."""


class DecisionJournalService:
    def record_ticket_decision(
        self,
        order_ticket_id: int,
        decision: str,
        reason: Optional[str],
        emotional_state: Optional[str] = None,
    ) -> int:
        """Record approval/rejection/modification."""

    def record_override_decision(
        self,
        override_ticket_id: int,
        decision: str,
        reason: Optional[str],
        emotional_state: Optional[str] = None,
    ) -> int:
        """Record override decision."""
```

---

# 8. CLI Commands — Stage 2

Every command must support global `--db`.

## 8.1 Price / FX

```text
portfolio-os record-price
portfolio-os record-fx-rate
portfolio-os list-prices
portfolio-os list-fx-rates
```

## 8.2 Risk Policy

```text
portfolio-os seed-default-risk-policy
portfolio-os create-risk-policy
portfolio-os activate-risk-policy
portfolio-os add-risk-rule
portfolio-os list-risk-rules
portfolio-os set-instrument-risk-profile
```

## 8.3 Intent and Validation

```text
portfolio-os create-intent
portfolio-os validate-intent
portfolio-os show-risk-validation
```

## 8.4 Order Ticket Workflow

```text
portfolio-os create-order-ticket
portfolio-os show-order-ticket
portfolio-os approve-ticket
portfolio-os reject-ticket
portfolio-os modify-ticket
portfolio-os expire-tickets
portfolio-os list-open-tickets
```

## 8.5 Manual Execution

```text
portfolio-os log-manual-execution
portfolio-os list-pending-executions
portfolio-os confirm-executions-after-reconciliation
```

## 8.6 Override and Journal

```text
portfolio-os declare-override
portfolio-os confirm-override
portfolio-os log-override-execution
portfolio-os list-overrides
portfolio-os record-postmortem
portfolio-os list-journal
```

## 8.7 Reports

```text
portfolio-os export-risk-report
portfolio-os export-ticket-report
portfolio-os export-decision-journal
```

---

# 9. Directory Structure — Stage 2 Additions

```text
portfolio-os/
  docs/
    stage2_risk_gated_manual_operating_loop.md
    stage2_database_schema.md
    stage2_state_machines.md
    stage2_risk_rules.md
    stage2_cli_usage.md

  migrations/
    009_create_price_snapshots.sql
    010_create_fx_rates.sql
    011_create_instrument_risk_profiles.sql
    012_create_risk_policy_versions.sql
    013_create_risk_rules.sql
    014_create_transaction_intents.sql
    015_create_risk_validation_results.sql
    016_create_order_tickets.sql
    017_create_order_ticket_events.sql
    018_create_manual_execution_logs.sql
    019_create_override_tickets.sql
    020_create_decision_journal.sql
    021_create_postmortem_tasks.sql
    022_create_stage2_indexes.sql

  data/
    exports/
      risk_reports/
      order_tickets/
      decision_journal/
      postmortems/

  src/
    portfolio_os/
      pricing/
        __init__.py
        repositories.py
        valuation_service.py

      risk/
        __init__.py
        models.py
        repositories.py
        default_policy.py
        engine.py
        checks.py
        action_classifier.py
        report_writer.py

      intents/
        __init__.py
        models.py
        repository.py
        service.py
        validators.py

      tickets/
        __init__.py
        models.py
        repository.py
        service.py
        state_machine.py
        report_writer.py

      execution/
        __init__.py
        models.py
        repository.py
        service.py
        validators.py

      override/
        __init__.py
        models.py
        repository.py
        service.py
        warnings.py

      journal/
        __init__.py
        models.py
        repository.py
        service.py
        postmortem.py

      cli/
        stage2_commands.py

  tests/
    unit/
      test_stage2_price_fx_validation.py
      test_stage2_risk_policy.py
      test_stage2_action_classifier.py
      test_stage2_risk_engine.py
      test_stage2_ticket_state_machine.py
      test_stage2_manual_execution_validation.py
      test_stage2_override_service.py
      test_stage2_decision_journal.py

    integration/
      test_stage2_migrations.py
      test_stage2_buy_ticket_passed_flow.py
      test_stage2_buy_ticket_adjusted_flow.py
      test_stage2_buy_ticket_rejected_flow.py
      test_stage2_sell_reduce_only_stale_flow.py
      test_stage2_manual_execution_creates_provisional_transaction.py
      test_stage2_reconciliation_confirms_execution.py
      test_stage2_override_flow.py
      test_stage2_cli_smoke.py
```

---

# 10. Reports

## 10.1 Risk Report

Paths:

```text
data/exports/risk_reports/risk_validation_<id>.md
data/exports/risk_reports/risk_validation_<id>.json
```

Must include:

```text
risk_validation_id
intent_id
ledger_status_at_validation
policy_version
validation_status
action_class
requested_quantity / requested_notional
approved_quantity / approved_notional
failed checks
warnings
cash_before
cash_after
tax_reserve_required
expires_at
```

---

## 10.2 Order Ticket Report

Paths:

```text
data/exports/order_tickets/order_ticket_<id>.md
data/exports/order_tickets/order_ticket_<id>.json
```

Must include:

```text
order_ticket_id
account
instrument
side
order_type
ticket_quantity
limit_price
ticket_notional
currency
risk_validation_id
human approval status
expiry
manual execution instructions
```

The report must clearly state:

```text
The system does not execute this order.
Place it manually in your external account interface only if you choose to approve it.
After execution, log the actual filled quantity, price, fees, tax, and timestamp.
```

---

# 11. Test Plan

## 11.1 Unit Tests

Required unit tests:

```text
Decimal values still reject float
price snapshot validation
fx rate validation
risk rule validation
instrument risk profile validation
transaction intent validation
action classification buy -> risk_increasing
action classification sell within holdings -> risk_reducing
ledger_status gate for reconciled/provisional/stale/broken
minimum cash reserve check
tax reserve protection check
daily buy limit check
weekly buy limit check
max asset weight check
max bucket weight check
holding available for sell check
risk result passed
risk result adjusted
risk result rejected
ticket state transitions
manual execution sign convention
override ticket state transitions
decision journal append-only behavior
```

---

## 11.2 Integration Tests

Required integration tests:

```text
Stage 2 migrations apply after Stage 1 migrations
seed default risk policy
record price and fx snapshots
create buy intent on reconciled ledger
validate buy intent -> passed
create ticket from passed validation
approve ticket
log manual execution
manual execution creates Stage 1 transaction with is_confirmed=0
ledger becomes provisional after execution
run reconciliation
execution becomes reconciled after passed reconciliation
buy intent rejected when ledger_status = stale
risk-reducing sell allowed when ledger_status = stale
official ticket blocked when ledger_status = broken
override can be declared when ledger_status = broken
external snapshot values still never enter cash_balances
CLI smoke for create-intent -> validate-intent -> create-order-ticket -> approve-ticket -> log-manual-execution
```

---

# 12. Implementation Order

Codex should implement in this order.

```text
1. Add Stage 2 migrations only. Do not alter Stage 1 migrations.
2. Add Stage 2 dataclass models.
3. Add price/fx repositories and validators.
4. Add instrument risk profile repository.
5. Add risk policy/risk rule repositories.
6. Add transaction intent repository and validators.
7. Add valuation service using LedgerSnapshot + price/fx snapshots.
8. Add risk action classifier.
9. Add risk engine checks one by one.
10. Add risk validation persistence and risk report writer.
11. Add order ticket repository, event log, and state machine.
12. Add order ticket service and ticket report writer.
13. Add manual execution service.
14. Connect manual execution to Stage 1 transaction creation.
15. Add override ticket service.
16. Add decision journal service.
17. Add postmortem task service.
18. Add Stage 2 CLI commands.
19. Add unit tests.
20. Add integration tests.
21. Run full pytest.
22. Generate Stage 2 implementation handoff report.
```

---

# 13. Stage 2 Definition of Done

Stage 2 is complete only when all of the following are true.

```text
1. Stage 1 tests still pass.
2. Stage 2 migrations apply cleanly after Stage 1 migrations.
3. Stage 2 never modifies existing root documents.
4. Stage 2 never writes external snapshot values into cash_balances.
5. Decimal policy remains intact.
6. A buy intent can be validated as passed/rejected/adjusted.
7. No order ticket can be created from rejected validation.
8. No order ticket can be created without risk validation.
9. No order ticket can be executed without human approval.
10. Manual execution creates a provisional Stage 1 transaction.
11. Provisional transaction makes ledger status provisional.
12. Passed reconciliation can confirm execution.
13. Broken/stale/provisional ledger gates risk-increasing official tickets correctly.
14. Declared override can be created even when official ticket is blocked.
15. Decision journal records approvals, rejections, modifications, overrides, and executions.
16. Markdown/JSON risk and ticket reports are generated.
17. CLI smoke test passes.
18. Full pytest passes.
```

---

# 14. Non-Negotiable Rules

```text
No automatic order execution.
No human approval, no official execution log.
No rejected validation, no order ticket.
No risk validation, no order ticket.
No external snapshot cash into cash_balances.
No float arithmetic.
No direct mutation of historical transactions.
No official risk-increasing ticket when ledger_status != reconciled.
No official ticket when ledger_status = broken.
No manual execution without ticket or override.
No order ticket without expiry.
No order ticket without event log.
No override without human reason.
No postmortem-required override without postmortem task.
No Stage 3+ functionality.
```

---

# 15. Final Stage 2 Rule

```text
Stage 2 is finished only when the system can prove this:

Every real trade is linked to either
1. a risk-validated, human-approved order ticket, or
2. a declared override,

and every manual execution creates a provisional transaction that must later be reconciled.
```
