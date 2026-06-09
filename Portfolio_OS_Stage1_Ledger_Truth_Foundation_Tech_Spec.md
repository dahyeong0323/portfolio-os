# Portfolio OS Stage 1 Tech Spec — Ledger Truth Foundation

> 목적: 이 문서는 Stage 1 구현을 위한 기술 명세서다.  
> 초점은 오직 **원장 데이터 무결성**, **현금·부채·세금 준비금 정합성**, **실제 계좌 스냅샷과의 대조**다.  
> 기준 저장소는 **SQLite**, 기준 구현 언어는 **Python 3.11+**, 금액·수량 계산은 반드시 `Decimal`을 사용한다.

---

## 0. Stage 1 Scope

### 0.1 Stage 1의 단 하나의 목표

```text
내 실제 계좌, 현금, 부채, 세금 준비금, 거래 기록이 하나의 공식 원장에서 재구성되고,
외부 계좌 스냅샷과 대조되어 현재 장부 상태가 명확히 판정되는 것.
```

### 0.2 Stage 1에서 만들어야 하는 것

- 계좌 마스터
- 종목 마스터
- 거래 원장
- 현금 잔고 기록
- 부채 기록
- 세금 준비금 기록
- 대조 스냅샷 기록
- 원장 상태 판정 로직
- 외부 계좌 스냅샷 입력 구조
- 원장 스냅샷 생성 로직
- 대조 결과 생성 로직
- 기본 무결성 검증 로직

### 0.3 Stage 1에서 절대 하지 않는 것

- 자동 주문
- 투자 판단 메모
- 종목 리서치
- 포트폴리오 위험 판단
- 알림/메신저 연동
- 실시간 시세 스트리밍
- 복잡한 사용자 화면
- 외부 계좌 쓰기 연동

---

## 1. Global Data Rules

### 1.1 SQLite Decimal Policy

SQLite는 진짜 고정소수점 타입을 강제하지 않는다.  
따라서 Stage 1에서는 다음 규칙을 따른다.

```text
DB 선언 타입: DECIMAL(38, 12)
Python 타입: Decimal
DB 저장 형식: Decimal을 문자열로 직렬화한 값
읽기 시 처리: 문자열 → Decimal
금지: float 사용
```

모든 금액, 수량, 가격, 환율, 수수료, 세금 관련 값은 `Decimal`로 처리한다.

---

### 1.2 Time Policy

모든 시간 필드는 UTC 기준 ISO-8601 문자열로 저장한다.

```text
예시: 2026-05-16T13:45:22Z
```

날짜만 필요한 필드는 `YYYY-MM-DD` 형식의 `TEXT`로 저장한다.

---

### 1.3 Currency Policy

통화 코드는 ISO 4217 스타일의 3글자 대문자 문자열로 저장한다.

```text
KRW
CHF
USD
EUR
JPY
```

DB 레벨에서는 `CHECK(length(currency) = 3)`을 사용한다.

---

### 1.4 Append-Only Principle

Stage 1의 기본 원칙은 append-only다.

- 이미 입력된 거래는 직접 수정하지 않는다.
- 잘못된 거래는 `reversal` 또는 `correction` 거래로 정정한다.
- 현금 잔고, 부채, 세금 준비금은 시점별 스냅샷으로 누적 저장한다.
- 대조 스냅샷은 삭제하지 않는다.
- 잘못된 입력을 논리적으로 무효화해야 할 때는 `is_voided = 1` 및 `void_reason`을 사용한다.

---

### 1.5 Foreign Key Policy

SQLite 연결 직후 반드시 다음을 실행한다.

```sql
pragma foreign_keys = ON;
pragma journal_mode = WAL;
pragma busy_timeout = 5000;
```

---

## 2. Database Schema

아래 스키마는 Stage 1의 최소 핵심 스키마다.  
각 테이블은 SQLite 기준이며, 금액/수량 계열은 `DECIMAL(38, 12)`로 표기한다.

---

# 2.1 `accounts` — 계좌 마스터

## 역할

투자 계좌, 현금 계좌, 저축 계좌, 대출 계좌 등 원장에 등장하는 모든 계좌의 기준 정보를 저장한다.

## Table Definition

| Column | SQLite Type | Python Type | PK | FK | Nullable | Default | Constraints / Notes |
|---|---:|---|---|---|---|---|---|
| `account_id` | INTEGER | int | Yes | No | No | auto | `PRIMARY KEY AUTOINCREMENT` |
| `account_name` | TEXT | str | No | No | No | - | 사람이 읽는 계좌명 |
| `institution_name` | TEXT | str | No | No | No | - | 금융기관명 |
| `account_type` | TEXT | str | No | No | No | - | `CHECK(account_type IN ('securities','cash','savings','loan','tax','other'))` |
| `base_currency` | TEXT | str | No | No | No | - | `CHECK(length(base_currency) = 3)` |
| `account_number_masked` | TEXT | str | No | No | Yes | NULL | 전체 계좌번호 저장 금지, 마스킹된 값만 허용 |
| `is_active` | INTEGER | bool | No | No | No | 1 | `CHECK(is_active IN (0,1))` |
| `opened_date` | TEXT | date str | No | No | Yes | NULL | `YYYY-MM-DD` |
| `closed_date` | TEXT | date str | No | No | Yes | NULL | `YYYY-MM-DD`, 활성 계좌면 NULL |
| `notes` | TEXT | str | No | No | Yes | NULL | 비고 |
| `created_at` | TEXT | datetime str | No | No | No | current UTC | ISO-8601 UTC |
| `updated_at` | TEXT | datetime str | No | No | No | current UTC | 변경 시 갱신 |

## Required Indexes

| Index Name | Columns | Unique | Purpose |
|---|---|---:|---|
| `idx_accounts_active` | `is_active` | No | 활성 계좌 조회 |
| `idx_accounts_institution` | `institution_name` | No | 기관별 계좌 조회 |
| `uq_accounts_name_institution` | `account_name`, `institution_name` | Yes | 같은 기관 내 계좌명 중복 방지 |

---

# 2.2 `instruments` — 종목 마스터

## 역할

거래 가능한 모든 자산의 기준 정보를 저장한다.  
거래 내역은 반드시 `instruments.instrument_id`를 참조해야 한다.

## Table Definition

| Column | SQLite Type | Python Type | PK | FK | Nullable | Default | Constraints / Notes |
|---|---:|---|---|---|---|---|---|
| `instrument_id` | INTEGER | int | Yes | No | No | auto | `PRIMARY KEY AUTOINCREMENT` |
| `symbol` | TEXT | str | No | No | No | - | 거래 심볼, 예: `AAPL`, `QLD`, `BTC` |
| `instrument_name` | TEXT | str | No | No | No | - | 정식 명칭 |
| `instrument_type` | TEXT | str | No | No | No | - | `CHECK(instrument_type IN ('stock','etf','crypto','fund','bond','cash_equivalent','other'))` |
| `exchange` | TEXT | str | No | No | Yes | NULL | 거래소, 해당 없으면 NULL |
| `isin` | TEXT | str | No | No | Yes | NULL | ISIN, 없으면 NULL |
| `currency` | TEXT | str | No | No | No | - | 가격 기준 통화, `CHECK(length(currency) = 3)` |
| `country` | TEXT | str | No | No | Yes | NULL | 상장/발행 국가 |
| `is_fractional_allowed` | INTEGER | bool | No | No | No | 0 | `CHECK(is_fractional_allowed IN (0,1))` |
| `quantity_precision` | INTEGER | int | No | No | No | 6 | 수량 허용 소수 자릿수 |
| `price_precision` | INTEGER | int | No | No | No | 6 | 가격 허용 소수 자릿수 |
| `is_active` | INTEGER | bool | No | No | No | 1 | `CHECK(is_active IN (0,1))` |
| `notes` | TEXT | str | No | No | Yes | NULL | 비고 |
| `created_at` | TEXT | datetime str | No | No | No | current UTC | ISO-8601 UTC |
| `updated_at` | TEXT | datetime str | No | No | No | current UTC | 변경 시 갱신 |

## Required Indexes

| Index Name | Columns | Unique | Purpose |
|---|---|---:|---|
| `uq_instruments_symbol_exchange_currency` | `symbol`, `exchange`, `currency` | Yes | 같은 심볼의 중복 등록 방지 |
| `idx_instruments_type` | `instrument_type` | No | 유형별 조회 |
| `idx_instruments_active` | `is_active` | No | 활성 종목 조회 |

---

# 2.3 `transactions` — 거래 내역

## 역할

매수, 매도, 입금, 출금, 배당, 이자, 수수료, 세금, 정정 거래를 저장하는 핵심 원장 테이블이다.

Stage 1에서는 `transactions`가 보유 수량과 원가 계산의 원천이다.

## Table Definition

| Column | SQLite Type | Python Type | PK | FK | Nullable | Default | Constraints / Notes |
|---|---:|---|---|---|---|---|---|
| `transaction_id` | INTEGER | int | Yes | No | No | auto | `PRIMARY KEY AUTOINCREMENT` |
| `account_id` | INTEGER | int | No | Yes | No | - | `REFERENCES accounts(account_id)` |
| `instrument_id` | INTEGER | int | No | Yes | Yes | NULL | `REFERENCES instruments(instrument_id)`, 현금성 거래는 NULL 가능 |
| `transaction_type` | TEXT | str | No | No | No | - | `CHECK(transaction_type IN ('buy','sell','deposit','withdrawal','dividend','interest','fee','tax','transfer_in','transfer_out','reversal','correction'))` |
| `trade_date` | TEXT | date str | No | No | No | - | 체결일, `YYYY-MM-DD` |
| `settlement_date` | TEXT | date str | No | No | Yes | NULL | 결제일, `YYYY-MM-DD` |
| `currency` | TEXT | str | No | No | No | - | 거래 현금 통화, `CHECK(length(currency) = 3)` |
| `quantity` | DECIMAL(38, 12) | Decimal | No | No | Yes | NULL | 종목 수량. 현금 거래는 NULL 가능 |
| `price` | DECIMAL(38, 12) | Decimal | No | No | Yes | NULL | 단가. 현금 거래는 NULL 가능 |
| `gross_amount` | DECIMAL(38, 12) | Decimal | No | No | No | - | 수수료/세금 전 금액 |
| `fee_amount` | DECIMAL(38, 12) | Decimal | No | No | No | 0 | 수수료 |
| `tax_amount` | DECIMAL(38, 12) | Decimal | No | No | No | 0 | 거래 시점 세금 |
| `net_cash_amount` | DECIMAL(38, 12) | Decimal | No | No | No | - | 현금 증감. 현금 유입 양수, 유출 음수 |
| `fx_rate_to_base` | DECIMAL(38, 12) | Decimal | No | No | Yes | NULL | 계좌 기준 통화 환산율 |
| `source` | TEXT | str | No | No | No | `'manual'` | `CHECK(source IN ('manual','csv_import','external_snapshot','system_correction'))` |
| `external_ref` | TEXT | str | No | No | Yes | NULL | 외부 거래 식별자 또는 원본 행 번호 |
| `description` | TEXT | str | No | No | Yes | NULL | 설명 |
| `is_confirmed` | INTEGER | bool | No | No | No | 0 | `CHECK(is_confirmed IN (0,1))`, 대조 완료 여부 |
| `is_voided` | INTEGER | bool | No | No | No | 0 | `CHECK(is_voided IN (0,1))` |
| `void_reason` | TEXT | str | No | No | Yes | NULL | 무효 처리 사유 |
| `created_at` | TEXT | datetime str | No | No | No | current UTC | ISO-8601 UTC |
| `updated_at` | TEXT | datetime str | No | No | No | current UTC | 변경 시 갱신 |

## Required Indexes

| Index Name | Columns | Unique | Purpose |
|---|---|---:|---|
| `idx_transactions_account_date` | `account_id`, `trade_date` | No | 계좌별 거래 조회 |
| `idx_transactions_instrument` | `instrument_id` | No | 종목별 거래 조회 |
| `idx_transactions_confirmed` | `is_confirmed` | No | 미확정 거래 조회 |
| `idx_transactions_external_ref` | `source`, `external_ref` | No | 외부 입력 중복 탐지 |
| `idx_transactions_voided` | `is_voided` | No | 유효 거래 필터링 |

## Mandatory Validation Rules

| Rule ID | Rule |
|---|---|
| `TX-001` | `buy`, `sell`은 `instrument_id`, `quantity`, `price`가 NULL이면 안 된다. |
| `TX-002` | `buy`의 `quantity`는 양수여야 한다. |
| `TX-003` | `sell`의 `quantity`는 음수 또는 별도 정책상 양수 입력 후 계산 변환 중 하나로 통일해야 한다. Stage 1 기본값은 **매도 수량 음수**다. |
| `TX-004` | `net_cash_amount`는 현금 유입이면 양수, 현금 유출이면 음수다. |
| `TX-005` | `fee_amount`, `tax_amount`는 음수일 수 없다. |
| `TX-006` | `is_voided = 1`이면 `void_reason`은 NULL이면 안 된다. |
| `TX-007` | `reversal`, `correction` 거래는 `description`에 원 거래 식별 정보가 있어야 한다. |

---

# 2.4 `cash_balances` — 현금 잔고

## 역할

계좌별·통화별 현금 잔고의 시점 스냅샷을 저장한다.  
거래 내역으로 계산한 현금과 실제 입력된 현금 잔고를 대조할 때 사용한다.

## Table Definition

| Column | SQLite Type | Python Type | PK | FK | Nullable | Default | Constraints / Notes |
|---|---:|---|---|---|---|---|---|
| `cash_balance_id` | INTEGER | int | Yes | No | No | auto | `PRIMARY KEY AUTOINCREMENT` |
| `account_id` | INTEGER | int | No | Yes | No | - | `REFERENCES accounts(account_id)` |
| `as_of_date` | TEXT | date str | No | No | No | - | 기준일, `YYYY-MM-DD` |
| `currency` | TEXT | str | No | No | No | - | `CHECK(length(currency) = 3)` |
| `amount` | DECIMAL(38, 12) | Decimal | No | No | No | - | 해당 시점 현금 잔고 |
| `source` | TEXT | str | No | No | No | `'manual'` | `CHECK(source IN ('manual','csv_import','external_snapshot','system_correction'))` |
| `external_ref` | TEXT | str | No | No | Yes | NULL | 원본 식별자 |
| `is_reconciled` | INTEGER | bool | No | No | No | 0 | `CHECK(is_reconciled IN (0,1))` |
| `notes` | TEXT | str | No | No | Yes | NULL | 비고 |
| `created_at` | TEXT | datetime str | No | No | No | current UTC | ISO-8601 UTC |
| `updated_at` | TEXT | datetime str | No | No | No | current UTC | 변경 시 갱신 |

## Required Indexes

| Index Name | Columns | Unique | Purpose |
|---|---|---:|---|
| `uq_cash_balances_account_date_currency` | `account_id`, `as_of_date`, `currency` | Yes | 같은 계좌·일자·통화 잔고 중복 방지 |
| `idx_cash_balances_date` | `as_of_date` | No | 기준일 조회 |
| `idx_cash_balances_reconciled` | `is_reconciled` | No | 미대조 현금 조회 |

---

# 2.5 `liabilities` — 부채

## 역할

대출, 미지급금, 신용 사용액 등 투자 가능 현금 판단에 영향을 주는 부채를 저장한다.

Stage 1에서는 부채도 원장 상태의 일부다.

## Table Definition

| Column | SQLite Type | Python Type | PK | FK | Nullable | Default | Constraints / Notes |
|---|---:|---|---|---|---|---|---|
| `liability_id` | INTEGER | int | Yes | No | No | auto | `PRIMARY KEY AUTOINCREMENT` |
| `account_id` | INTEGER | int | No | Yes | Yes | NULL | `REFERENCES accounts(account_id)`, 특정 계좌와 무관하면 NULL |
| `liability_name` | TEXT | str | No | No | No | - | 부채명 |
| `liability_type` | TEXT | str | No | No | No | - | `CHECK(liability_type IN ('loan','margin','credit_card','tax_payable','other'))` |
| `currency` | TEXT | str | No | No | No | - | `CHECK(length(currency) = 3)` |
| `principal_amount` | DECIMAL(38, 12) | Decimal | No | No | Yes | NULL | 최초 원금 |
| `current_amount` | DECIMAL(38, 12) | Decimal | No | No | No | - | 현재 잔액. 부채는 양수로 저장 |
| `interest_rate_annual` | DECIMAL(18, 8) | Decimal | No | No | Yes | NULL | 연 이자율, 예: 0.0525 |
| `as_of_date` | TEXT | date str | No | No | No | - | 기준일 |
| `due_date` | TEXT | date str | No | No | Yes | NULL | 만기일 |
| `source` | TEXT | str | No | No | No | `'manual'` | `CHECK(source IN ('manual','csv_import','external_snapshot','system_correction'))` |
| `is_active` | INTEGER | bool | No | No | No | 1 | `CHECK(is_active IN (0,1))` |
| `notes` | TEXT | str | No | No | Yes | NULL | 비고 |
| `created_at` | TEXT | datetime str | No | No | No | current UTC | ISO-8601 UTC |
| `updated_at` | TEXT | datetime str | No | No | No | current UTC | 변경 시 갱신 |

## Required Indexes

| Index Name | Columns | Unique | Purpose |
|---|---|---:|---|
| `idx_liabilities_active` | `is_active` | No | 활성 부채 조회 |
| `idx_liabilities_as_of` | `as_of_date` | No | 기준일 조회 |
| `idx_liabilities_account` | `account_id` | No | 계좌별 부채 조회 |

## Mandatory Validation Rules

| Rule ID | Rule |
|---|---|
| `LB-001` | `current_amount`는 음수일 수 없다. |
| `LB-002` | `is_active = 0`이면 `current_amount = 0`이어야 한다. |
| `LB-003` | `due_date`가 있으면 `as_of_date`보다 과거일 수 없다. 단, 연체 상태를 따로 표시하기 전까지는 입력 거부한다. |

---

# 2.6 `tax_reserves` — 세금 준비금

## 역할

실현손익 또는 예상 세금 이벤트에 대비해 따로 보호해야 하는 현금 준비금을 저장한다.

Stage 1에서는 세금 준비금이 실제 현금과 분리되어 관리되어야 한다.

## Table Definition

| Column | SQLite Type | Python Type | PK | FK | Nullable | Default | Constraints / Notes |
|---|---:|---|---|---|---|---|---|
| `tax_reserve_id` | INTEGER | int | Yes | No | No | auto | `PRIMARY KEY AUTOINCREMENT` |
| `account_id` | INTEGER | int | No | Yes | Yes | NULL | `REFERENCES accounts(account_id)`, 특정 계좌와 무관하면 NULL |
| `tax_year` | INTEGER | int | No | No | No | - | 과세연도 |
| `tax_type` | TEXT | str | No | No | No | - | `CHECK(tax_type IN ('capital_gains','dividend','interest','wealth','income','other'))` |
| `currency` | TEXT | str | No | No | No | - | `CHECK(length(currency) = 3)` |
| `reserved_amount` | DECIMAL(38, 12) | Decimal | No | No | No | - | 보호해야 하는 금액 |
| `as_of_date` | TEXT | date str | No | No | No | - | 기준일 |
| `source` | TEXT | str | No | No | No | `'manual'` | `CHECK(source IN ('manual','csv_import','external_snapshot','system_correction'))` |
| `calculation_basis` | TEXT | str | No | No | Yes | NULL | 산정 근거 요약 |
| `is_active` | INTEGER | bool | No | No | No | 1 | `CHECK(is_active IN (0,1))` |
| `notes` | TEXT | str | No | No | Yes | NULL | 비고 |
| `created_at` | TEXT | datetime str | No | No | No | current UTC | ISO-8601 UTC |
| `updated_at` | TEXT | datetime str | No | No | No | current UTC | 변경 시 갱신 |

## Required Indexes

| Index Name | Columns | Unique | Purpose |
|---|---|---:|---|
| `idx_tax_reserves_year` | `tax_year` | No | 과세연도별 조회 |
| `idx_tax_reserves_active` | `is_active` | No | 활성 준비금 조회 |
| `idx_tax_reserves_account` | `account_id` | No | 계좌별 준비금 조회 |
| `uq_tax_reserves_scope` | `account_id`, `tax_year`, `tax_type`, `currency`, `as_of_date` | Yes | 같은 기준일 중복 방지 |

## Mandatory Validation Rules

| Rule ID | Rule |
|---|---|
| `TR-001` | `reserved_amount`는 음수일 수 없다. |
| `TR-002` | `tax_year`는 2000 이상이어야 한다. |
| `TR-003` | 같은 계좌·과세연도·세금 유형·통화·기준일 조합은 하나만 존재한다. |

---

# 2.7 `reconciliation_snapshots` — 대조 스냅샷

## 역할

특정 시점의 OS 원장 상태와 외부 계좌 스냅샷을 비교한 결과를 저장한다.

Stage 1에서는 이 테이블이 장부 상태 판정의 기준 기록이다.

## Table Definition

| Column | SQLite Type | Python Type | PK | FK | Nullable | Default | Constraints / Notes |
|---|---:|---|---|---|---|---|---|
| `reconciliation_id` | INTEGER | int | Yes | No | No | auto | `PRIMARY KEY AUTOINCREMENT` |
| `account_id` | INTEGER | int | No | Yes | Yes | NULL | `REFERENCES accounts(account_id)`, 전체 계좌 대조면 NULL |
| `as_of_date` | TEXT | date str | No | No | No | - | 대조 기준일 |
| `started_at` | TEXT | datetime str | No | No | No | - | 대조 시작 시각 |
| `completed_at` | TEXT | datetime str | No | No | Yes | NULL | 대조 완료 시각 |
| `ledger_status_before` | TEXT | str | No | No | No | - | `CHECK(... IN ('reconciled','provisional','stale','broken'))` |
| `ledger_status_after` | TEXT | str | No | No | No | - | `CHECK(... IN ('reconciled','provisional','stale','broken'))` |
| `reconciliation_status` | TEXT | str | No | No | No | - | `CHECK(reconciliation_status IN ('passed','failed','needs_review'))` |
| `snapshot_source` | TEXT | str | No | No | No | - | `CHECK(snapshot_source IN ('manual','csv_import','external_statement'))` |
| `position_diff_count` | INTEGER | int | No | No | No | 0 | 수량 차이 발생 종목 수 |
| `cash_diff_count` | INTEGER | int | No | No | No | 0 | 현금 차이 발생 통화 수 |
| `liability_diff_count` | INTEGER | int | No | No | No | 0 | 부채 차이 발생 항목 수 |
| `tax_reserve_diff_count` | INTEGER | int | No | No | No | 0 | 세금 준비금 차이 발생 항목 수 |
| `total_abs_cash_diff_base` | DECIMAL(38, 12) | Decimal | No | No | No | 0 | 기준 통화 환산 절대 현금 차이 합 |
| `tolerance_cash_abs` | DECIMAL(38, 12) | Decimal | No | No | No | 0 | 허용 현금 차이 |
| `tolerance_quantity_abs` | DECIMAL(38, 12) | Decimal | No | No | No | 0 | 허용 수량 차이 |
| `expected_positions_json` | TEXT | str | No | No | No | `'[]'` | OS 원장 기준 포지션 목록 |
| `actual_positions_json` | TEXT | str | No | No | No | `'[]'` | 외부 스냅샷 기준 포지션 목록 |
| `position_diffs_json` | TEXT | str | No | No | No | `'[]'` | 포지션 차이 목록 |
| `expected_cash_json` | TEXT | str | No | No | No | `'[]'` | OS 원장 기준 현금 목록 |
| `actual_cash_json` | TEXT | str | No | No | No | `'[]'` | 외부 스냅샷 기준 현금 목록 |
| `cash_diffs_json` | TEXT | str | No | No | No | `'[]'` | 현금 차이 목록 |
| `expected_liabilities_json` | TEXT | str | No | No | No | `'[]'` | OS 원장 기준 부채 목록 |
| `actual_liabilities_json` | TEXT | str | No | No | No | `'[]'` | 외부 스냅샷 기준 부채 목록 |
| `liability_diffs_json` | TEXT | str | No | No | No | `'[]'` | 부채 차이 목록 |
| `expected_tax_reserves_json` | TEXT | str | No | No | No | `'[]'` | OS 원장 기준 세금 준비금 목록 |
| `actual_tax_reserves_json` | TEXT | str | No | No | No | `'[]'` | 외부 스냅샷 기준 세금 준비금 목록 |
| `tax_reserve_diffs_json` | TEXT | str | No | No | No | `'[]'` | 세금 준비금 차이 목록 |
| `failure_reason` | TEXT | str | No | No | Yes | NULL | 실패 또는 검토 필요 사유 |
| `created_at` | TEXT | datetime str | No | No | No | current UTC | ISO-8601 UTC |

## Required Indexes

| Index Name | Columns | Unique | Purpose |
|---|---|---:|---|
| `idx_recon_account_date` | `account_id`, `as_of_date` | No | 계좌별 대조 이력 조회 |
| `idx_recon_status` | `reconciliation_status` | No | 실패/검토 필요 대조 조회 |
| `idx_recon_ledger_after` | `ledger_status_after` | No | 현재 장부 상태 추론 |
| `idx_recon_completed` | `completed_at` | No | 최근 대조 조회 |

## Mandatory Validation Rules

| Rule ID | Rule |
|---|---|
| `RC-001` | `reconciliation_status = 'passed'`이면 `ledger_status_after = 'reconciled'`이어야 한다. |
| `RC-002` | `reconciliation_status = 'failed'`이면 `ledger_status_after = 'broken'`이어야 한다. |
| `RC-003` | `reconciliation_status = 'needs_review'`이면 `ledger_status_after`는 `provisional` 또는 `broken`이어야 한다. |
| `RC-004` | `position_diff_count`, `cash_diff_count`, `liability_diff_count`, `tax_reserve_diff_count`는 음수일 수 없다. |
| `RC-005` | `completed_at`은 `started_at`보다 빠를 수 없다. |
| `RC-006` | `passed` 상태에서는 모든 diff count가 0이어야 한다. 단, 허용 오차 이내의 cash diff는 0으로 정규화한다. |

---

## 3. Ledger State Machine Definition

Stage 1의 장부 상태는 네 가지다.

```text
reconciled
provisional
stale
broken
```

---

# 3.1 State Meaning

| State | Meaning | Stage 1 Interpretation |
|---|---|---|
| `reconciled` | 외부 계좌 스냅샷과 OS 원장이 대조 완료됨 | 현재 장부를 기준 상태로 사용할 수 있음 |
| `provisional` | 원장에 새 입력이 있으나 아직 대조 전 | 계산은 가능하지만 확정 상태 아님 |
| `stale` | 마지막 대조 이후 허용 기간 초과 | 최신성 부족으로 확정 상태 아님 |
| `broken` | 외부 계좌 스냅샷과 OS 원장 간 차이 발견 | 먼저 정정 또는 원인 확인 필요 |

---

# 3.2 Core Transition Table

| From State | Trigger | Condition | To State | Notes |
|---|---|---|---|---|
| none | 최초 DB 생성 | 대조 기록 없음 | `provisional` | 초기 상태 |
| `provisional` | 외부 계좌 스냅샷 업로드 후 대조 실행 | 모든 포지션·현금·부채·세금 준비금 차이가 0 또는 허용 오차 이내 | `reconciled` | 대조 성공 |
| `provisional` | 외부 계좌 스냅샷 업로드 후 대조 실행 | 하나 이상의 차이가 허용 오차 초과 | `broken` | 원인 확인 필요 |
| `provisional` | 시간 경과 검사 | 마지막 원장 변경 또는 마지막 대조 이후 `STALE_AFTER_DAYS` 초과 | `stale` | 기본값 7일 |
| `reconciled` | 새 거래 입력 | 유효한 `transactions` row 추가 | `provisional` | 새 입력은 아직 대조 전 |
| `reconciled` | 현금 잔고 입력 | 새 `cash_balances` row 추가 | `provisional` | 새 잔고는 아직 대조 전 |
| `reconciled` | 부채 입력 | 새 `liabilities` row 추가 | `provisional` | 새 부채는 아직 대조 전 |
| `reconciled` | 세금 준비금 입력 | 새 `tax_reserves` row 추가 | `provisional` | 새 준비금은 아직 대조 전 |
| `reconciled` | 시간 경과 검사 | 마지막 대조 이후 `STALE_AFTER_DAYS` 초과 | `stale` | 최신 스냅샷 필요 |
| `stale` | 외부 계좌 스냅샷 업로드 후 대조 실행 | 모든 차이가 0 또는 허용 오차 이내 | `reconciled` | 최신성 회복 |
| `stale` | 외부 계좌 스냅샷 업로드 후 대조 실행 | 하나 이상의 차이가 허용 오차 초과 | `broken` | 최신 스냅샷 기준 불일치 |
| `stale` | 새 원장 입력 | 거래·현금·부채·세금 준비금 변경 발생 | `provisional` | 새 입력으로 인해 미대조 상태 |
| `broken` | 정정 입력 | correction 또는 reversal 입력 완료 | `provisional` | 아직 재대조 필요 |
| `broken` | 외부 계좌 스냅샷 재업로드 후 대조 실행 | 모든 차이가 0 또는 허용 오차 이내 | `reconciled` | 정합성 회복 |
| `broken` | 외부 계좌 스냅샷 재업로드 후 대조 실행 | 차이가 계속 존재 | `broken` | 문제 지속 |
| any | DB 무결성 검사 실패 | FK 오류, 필수 기준 정보 누락, Decimal 파싱 실패 | `broken` | 기술적 불일치도 broken 처리 |
| any | 계좌 비활성화 | 비활성화 전 모든 현금·포지션이 0이고 대조 완료 | `reconciled` | 종료 상태의 계좌도 마지막 대조 필요 |

---

# 3.3 Reconciliation Decision Logic

대조 실행 결과는 아래 순서로 판정한다.

```text
1. 외부 계좌 스냅샷 형식 검증
2. OS 원장 스냅샷 생성
3. 포지션 수량 비교
4. 현금 잔고 비교
5. 부채 잔액 비교
6. 세금 준비금 비교
7. 허용 오차 적용
8. diff count 계산
9. reconciliation_status 결정
10. ledger_status_after 결정
11. reconciliation_snapshots에 결과 저장
12. 관련 transactions/cash_balances의 대조 플래그 갱신
```

판정 규칙:

```text
if all diff counts == 0:
    reconciliation_status = "passed"
    ledger_status_after = "reconciled"

elif any required reference is missing:
    reconciliation_status = "needs_review"
    ledger_status_after = "broken"

elif any diff exceeds tolerance:
    reconciliation_status = "failed"
    ledger_status_after = "broken"

else:
    reconciliation_status = "needs_review"
    ledger_status_after = "provisional"
```

---

# 3.4 Stale Detection Rule

기본 설정:

```text
STALE_AFTER_DAYS = 7
```

현재 날짜 기준으로 가장 최근 `reconciliation_snapshots.completed_at`이 7일을 초과하면 `stale`로 판정한다.

예외:

- 대조 기록이 전혀 없으면 `provisional`
- 마지막 상태가 `broken`이면 시간 경과로 `stale`이 되지 않고 계속 `broken`
- 새 입력이 있으면 `provisional`
- 비활성 계좌는 마지막 대조 성공 이후 변경이 없으면 `reconciled` 유지

---

# 3.5 Tolerance Rules

Stage 1 기본 허용 오차:

```text
CASH_TOLERANCE_ABS = Decimal("1.00")
QUANTITY_TOLERANCE_ABS = Decimal("0.000001")
LIABILITY_TOLERANCE_ABS = Decimal("1.00")
TAX_RESERVE_TOLERANCE_ABS = Decimal("1.00")
```

해석:

- 현금은 통화 단위 기준 절대값 1.00 이하 차이를 허용한다.
- 수량은 소수점 6자리 수준까지 허용한다.
- 부채와 세금 준비금은 통화 단위 기준 절대값 1.00 이하 차이를 허용한다.
- 허용 오차 이내 차이는 diff count에 포함하지 않는다.
- 허용 오차 초과 차이는 반드시 대조 실패로 처리한다.

---

## 4. Core Interface & Function Signatures

아래는 Stage 1 구현을 위한 Python 타입 및 함수 시그니처다.  
내부 구현 로직은 이 문서에서 다루지 않는다.

---

# 4.1 Common Types

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal, Optional, Sequence


CurrencyCode = str
ISODateString = str
UTCDateTimeString = str

LedgerStatus = Literal["reconciled", "provisional", "stale", "broken"]
ReconciliationStatus = Literal["passed", "failed", "needs_review"]
AccountType = Literal["securities", "cash", "savings", "loan", "tax", "other"]
InstrumentType = Literal["stock", "etf", "crypto", "fund", "bond", "cash_equivalent", "other"]
TransactionType = Literal[
    "buy",
    "sell",
    "deposit",
    "withdrawal",
    "dividend",
    "interest",
    "fee",
    "tax",
    "transfer_in",
    "transfer_out",
    "reversal",
    "correction",
]
DataSource = Literal["manual", "csv_import", "external_snapshot", "system_correction"]
SnapshotSource = Literal["manual", "csv_import", "external_statement"]
```

---

# 4.2 Data Models

```python
@dataclass(frozen=True)
class Account:
    account_id: int
    account_name: str
    institution_name: str
    account_type: AccountType
    base_currency: CurrencyCode
    account_number_masked: Optional[str]
    is_active: bool
    opened_date: Optional[date]
    closed_date: Optional[date]
    notes: Optional[str]


@dataclass(frozen=True)
class Instrument:
    instrument_id: int
    symbol: str
    instrument_name: str
    instrument_type: InstrumentType
    exchange: Optional[str]
    isin: Optional[str]
    currency: CurrencyCode
    country: Optional[str]
    is_fractional_allowed: bool
    quantity_precision: int
    price_precision: int
    is_active: bool
    notes: Optional[str]


@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    account_id: int
    instrument_id: Optional[int]
    transaction_type: TransactionType
    trade_date: date
    settlement_date: Optional[date]
    currency: CurrencyCode
    quantity: Optional[Decimal]
    price: Optional[Decimal]
    gross_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    net_cash_amount: Decimal
    fx_rate_to_base: Optional[Decimal]
    source: DataSource
    external_ref: Optional[str]
    description: Optional[str]
    is_confirmed: bool
    is_voided: bool
    void_reason: Optional[str]


@dataclass(frozen=True)
class CashBalance:
    cash_balance_id: int
    account_id: int
    as_of_date: date
    currency: CurrencyCode
    amount: Decimal
    source: DataSource
    external_ref: Optional[str]
    is_reconciled: bool
    notes: Optional[str]


@dataclass(frozen=True)
class Liability:
    liability_id: int
    account_id: Optional[int]
    liability_name: str
    liability_type: str
    currency: CurrencyCode
    principal_amount: Optional[Decimal]
    current_amount: Decimal
    interest_rate_annual: Optional[Decimal]
    as_of_date: date
    due_date: Optional[date]
    source: DataSource
    is_active: bool
    notes: Optional[str]


@dataclass(frozen=True)
class TaxReserve:
    tax_reserve_id: int
    account_id: Optional[int]
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    reserved_amount: Decimal
    as_of_date: date
    source: DataSource
    calculation_basis: Optional[str]
    is_active: bool
    notes: Optional[str]
```

---

# 4.3 Snapshot Models

```python
@dataclass(frozen=True)
class LedgerPosition:
    account_id: int
    instrument_id: int
    symbol: str
    currency: CurrencyCode
    quantity: Decimal
    average_cost: Optional[Decimal]


@dataclass(frozen=True)
class LedgerCash:
    account_id: int
    currency: CurrencyCode
    amount: Decimal


@dataclass(frozen=True)
class LedgerLiability:
    liability_id: int
    account_id: Optional[int]
    currency: CurrencyCode
    current_amount: Decimal


@dataclass(frozen=True)
class LedgerTaxReserve:
    tax_reserve_id: int
    account_id: Optional[int]
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    reserved_amount: Decimal


@dataclass(frozen=True)
class LedgerSnapshot:
    as_of_date: date
    ledger_status: LedgerStatus
    positions: tuple[LedgerPosition, ...]
    cash: tuple[LedgerCash, ...]
    liabilities: tuple[LedgerLiability, ...]
    tax_reserves: tuple[LedgerTaxReserve, ...]
    generated_at: datetime


@dataclass(frozen=True)
class ExternalPosition:
    account_id: int
    symbol: str
    currency: CurrencyCode
    quantity: Decimal


@dataclass(frozen=True)
class ExternalCash:
    account_id: int
    currency: CurrencyCode
    amount: Decimal


@dataclass(frozen=True)
class ExternalLiability:
    account_id: Optional[int]
    liability_name: str
    currency: CurrencyCode
    current_amount: Decimal


@dataclass(frozen=True)
class ExternalTaxReserve:
    account_id: Optional[int]
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    reserved_amount: Decimal


@dataclass(frozen=True)
class ExternalAccountSnapshot:
    as_of_date: date
    source: SnapshotSource
    positions: tuple[ExternalPosition, ...]
    cash: tuple[ExternalCash, ...]
    liabilities: tuple[ExternalLiability, ...]
    tax_reserves: tuple[ExternalTaxReserve, ...]
    received_at: datetime
```

---

# 4.4 Reconciliation Models

```python
@dataclass(frozen=True)
class ReconciliationTolerance:
    cash_abs: Decimal
    quantity_abs: Decimal
    liability_abs: Decimal
    tax_reserve_abs: Decimal


@dataclass(frozen=True)
class PositionDifference:
    account_id: int
    instrument_id: Optional[int]
    symbol: str
    expected_quantity: Decimal
    actual_quantity: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class CashDifference:
    account_id: int
    currency: CurrencyCode
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class LiabilityDifference:
    account_id: Optional[int]
    liability_name: str
    currency: CurrencyCode
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class TaxReserveDifference:
    account_id: Optional[int]
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class ReconciliationResult:
    reconciliation_id: Optional[int]
    as_of_date: date
    ledger_status_before: LedgerStatus
    ledger_status_after: LedgerStatus
    reconciliation_status: ReconciliationStatus
    position_differences: tuple[PositionDifference, ...]
    cash_differences: tuple[CashDifference, ...]
    liability_differences: tuple[LiabilityDifference, ...]
    tax_reserve_differences: tuple[TaxReserveDifference, ...]
    failure_reason: Optional[str]
    completed_at: datetime
```

---

# 4.5 Database Connection Interface

```python
class Database:
    def __init__(self, db_path: Path) -> None: ...

    def connect(self) -> None: ...

    def close(self) -> None: ...

    def execute(self, sql: str, params: Sequence[object] = ()) -> None: ...

    def fetch_one(self, sql: str, params: Sequence[object] = ()) -> Optional[dict[str, object]]: ...

    def fetch_all(self, sql: str, params: Sequence[object] = ()) -> list[dict[str, object]]: ...

    def begin(self) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


def initialize_database(db_path: Path) -> None:
    """Create Stage 1 SQLite schema and required indexes."""
```

---

# 4.6 Repository Interfaces

```python
class AccountRepository:
    def create_account(
        self,
        account_name: str,
        institution_name: str,
        account_type: AccountType,
        base_currency: CurrencyCode,
        account_number_masked: Optional[str] = None,
        opened_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> Account: ...

    def get_account(self, account_id: int) -> Optional[Account]: ...

    def list_active_accounts(self) -> list[Account]: ...

    def deactivate_account(self, account_id: int, closed_date: date, notes: Optional[str] = None) -> Account: ...


class InstrumentRepository:
    def create_instrument(
        self,
        symbol: str,
        instrument_name: str,
        instrument_type: InstrumentType,
        currency: CurrencyCode,
        exchange: Optional[str] = None,
        isin: Optional[str] = None,
        country: Optional[str] = None,
        is_fractional_allowed: bool = False,
        quantity_precision: int = 6,
        price_precision: int = 6,
        notes: Optional[str] = None,
    ) -> Instrument: ...

    def get_instrument(self, instrument_id: int) -> Optional[Instrument]: ...

    def find_by_symbol(
        self,
        symbol: str,
        exchange: Optional[str],
        currency: CurrencyCode,
    ) -> Optional[Instrument]: ...

    def list_active_instruments(self) -> list[Instrument]: ...


class TransactionRepository:
    def record_transaction(self, transaction: Transaction) -> Transaction: ...

    def list_transactions(
        self,
        account_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
        include_voided: bool = False,
    ) -> list[Transaction]: ...

    def list_unconfirmed_transactions(self, account_id: Optional[int] = None) -> list[Transaction]: ...

    def void_transaction(self, transaction_id: int, void_reason: str) -> Transaction: ...

    def mark_transactions_confirmed(self, transaction_ids: Sequence[int]) -> int: ...


class CashBalanceRepository:
    def record_cash_balance(self, cash_balance: CashBalance) -> CashBalance: ...

    def get_latest_cash_balances(
        self,
        as_of_date: date,
        account_id: Optional[int] = None,
    ) -> list[CashBalance]: ...

    def mark_cash_balances_reconciled(self, cash_balance_ids: Sequence[int]) -> int: ...


class LiabilityRepository:
    def record_liability(self, liability: Liability) -> Liability: ...

    def list_active_liabilities(self, as_of_date: Optional[date] = None) -> list[Liability]: ...

    def deactivate_liability(self, liability_id: int, as_of_date: date, notes: Optional[str] = None) -> Liability: ...


class TaxReserveRepository:
    def record_tax_reserve(self, tax_reserve: TaxReserve) -> TaxReserve: ...

    def list_active_tax_reserves(
        self,
        tax_year: Optional[int] = None,
        as_of_date: Optional[date] = None,
    ) -> list[TaxReserve]: ...

    def deactivate_tax_reserve(self, tax_reserve_id: int, as_of_date: date, notes: Optional[str] = None) -> TaxReserve: ...


class ReconciliationRepository:
    def save_reconciliation_result(self, result: ReconciliationResult) -> ReconciliationResult: ...

    def get_latest_reconciliation(
        self,
        account_id: Optional[int] = None,
    ) -> Optional[ReconciliationResult]: ...

    def list_reconciliations(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[ReconciliationStatus] = None,
    ) -> list[ReconciliationResult]: ...
```

---

# 4.7 Validation Interfaces

```python
class ValidationError(Exception):
    pass


class IntegrityValidationError(ValidationError):
    pass


class DecimalValidationError(ValidationError):
    pass


class ReferenceValidationError(ValidationError):
    pass


def validate_currency_code(currency: CurrencyCode) -> None:
    """Validate 3-letter uppercase currency code."""


def validate_decimal_string(value: str) -> Decimal:
    """Parse a DB decimal string into Decimal or raise DecimalValidationError."""


def validate_account(account: Account) -> None:
    """Validate account master data before insert or update."""


def validate_instrument(instrument: Instrument) -> None:
    """Validate instrument master data before insert or update."""


def validate_transaction(transaction: Transaction) -> None:
    """Validate transaction business rules before insert."""


def validate_cash_balance(cash_balance: CashBalance) -> None:
    """Validate cash balance before insert."""


def validate_liability(liability: Liability) -> None:
    """Validate liability before insert."""


def validate_tax_reserve(tax_reserve: TaxReserve) -> None:
    """Validate tax reserve before insert."""


def validate_external_snapshot(snapshot: ExternalAccountSnapshot) -> None:
    """Validate external account snapshot before reconciliation."""
```

---

# 4.8 Snapshot Builder Interface

```python
class LedgerSnapshotBuilder:
    def build_snapshot(
        self,
        as_of_date: date,
        account_id: Optional[int] = None,
    ) -> LedgerSnapshot:
        """Build OS ledger snapshot from transactions, cash balances, liabilities, and tax reserves."""

    def build_positions(
        self,
        as_of_date: date,
        account_id: Optional[int] = None,
    ) -> tuple[LedgerPosition, ...]:
        """Build current positions from non-voided transactions."""

    def build_cash(
        self,
        as_of_date: date,
        account_id: Optional[int] = None,
    ) -> tuple[LedgerCash, ...]:
        """Build cash view from latest cash balance records and transaction-derived cash movement."""

    def build_liabilities(
        self,
        as_of_date: date,
        account_id: Optional[int] = None,
    ) -> tuple[LedgerLiability, ...]:
        """Build current liability view."""

    def build_tax_reserves(
        self,
        as_of_date: date,
        account_id: Optional[int] = None,
    ) -> tuple[LedgerTaxReserve, ...]:
        """Build current tax reserve view."""
```

---

# 4.9 State Machine Interface

```python
class LedgerStateMachine:
    def get_current_status(
        self,
        account_id: Optional[int] = None,
        as_of_date: Optional[date] = None,
    ) -> LedgerStatus:
        """Return current ledger status for one account or entire ledger."""

    def determine_next_status_after_input(
        self,
        previous_status: LedgerStatus,
    ) -> LedgerStatus:
        """Return next status after a valid ledger input."""

    def determine_next_status_after_reconciliation(
        self,
        previous_status: LedgerStatus,
        reconciliation_status: ReconciliationStatus,
        has_unresolved_differences: bool,
    ) -> LedgerStatus:
        """Return next status after reconciliation result."""

    def mark_stale_if_needed(
        self,
        current_status: LedgerStatus,
        last_reconciled_at: Optional[datetime],
        now: datetime,
        stale_after_days: int,
    ) -> LedgerStatus:
        """Return stale if last reconciliation is older than threshold."""
```

---

# 4.10 Reconciliation Service Interface

```python
class ReconciliationService:
    def run_reconciliation(
        self,
        ledger_snapshot: LedgerSnapshot,
        external_snapshot: ExternalAccountSnapshot,
        tolerance: ReconciliationTolerance,
    ) -> ReconciliationResult:
        """Compare OS ledger snapshot with external account snapshot."""

    def compare_positions(
        self,
        expected: Sequence[LedgerPosition],
        actual: Sequence[ExternalPosition],
        tolerance: Decimal,
    ) -> tuple[PositionDifference, ...]:
        """Compare expected and actual positions."""

    def compare_cash(
        self,
        expected: Sequence[LedgerCash],
        actual: Sequence[ExternalCash],
        tolerance: Decimal,
    ) -> tuple[CashDifference, ...]:
        """Compare expected and actual cash balances."""

    def compare_liabilities(
        self,
        expected: Sequence[LedgerLiability],
        actual: Sequence[ExternalLiability],
        tolerance: Decimal,
    ) -> tuple[LiabilityDifference, ...]:
        """Compare expected and actual liabilities."""

    def compare_tax_reserves(
        self,
        expected: Sequence[LedgerTaxReserve],
        actual: Sequence[ExternalTaxReserve],
        tolerance: Decimal,
    ) -> tuple[TaxReserveDifference, ...]:
        """Compare expected and actual tax reserves."""

    def persist_result(
        self,
        result: ReconciliationResult,
    ) -> ReconciliationResult:
        """Persist reconciliation result to reconciliation_snapshots."""
```

---

# 4.11 Import Interfaces

```python
class CSVImportError(Exception):
    pass


class AccountSnapshotCSVImporter:
    def parse_positions_csv(self, file_path: Path, account_id: int, as_of_date: date) -> tuple[ExternalPosition, ...]:
        """Parse external positions CSV."""

    def parse_cash_csv(self, file_path: Path, account_id: int, as_of_date: date) -> tuple[ExternalCash, ...]:
        """Parse external cash CSV."""

    def parse_liabilities_csv(self, file_path: Path, as_of_date: date) -> tuple[ExternalLiability, ...]:
        """Parse external liabilities CSV."""

    def parse_tax_reserves_csv(self, file_path: Path, as_of_date: date) -> tuple[ExternalTaxReserve, ...]:
        """Parse external tax reserve CSV."""

    def build_external_snapshot(
        self,
        as_of_date: date,
        source: SnapshotSource,
        positions: Sequence[ExternalPosition],
        cash: Sequence[ExternalCash],
        liabilities: Sequence[ExternalLiability],
        tax_reserves: Sequence[ExternalTaxReserve],
    ) -> ExternalAccountSnapshot:
        """Build validated external account snapshot."""
```

---

# 4.12 Reporting Interface

```python
class ReconciliationReportWriter:
    def write_markdown_report(
        self,
        result: ReconciliationResult,
        output_path: Path,
    ) -> Path:
        """Write a human-readable reconciliation report."""

    def write_json_report(
        self,
        result: ReconciliationResult,
        output_path: Path,
    ) -> Path:
        """Write a machine-readable reconciliation report."""
```

---

## 5. Stage 1 Directory Structure

아래 구조만 Stage 1 범위다.

```text
portfolio-os/
  README.md
  pyproject.toml
  .gitignore

  data/
    portfolio_os.sqlite3
    imports/
      account_snapshots/
      transactions/
      cash/
      liabilities/
      tax_reserves/
    exports/
      reconciliation_reports/

  docs/
    stage1_ledger_truth_foundation.md
    database_schema.md
    state_machine.md
    reconciliation_rules.md
    decimal_policy.md

  migrations/
    001_create_accounts.sql
    002_create_instruments.sql
    003_create_transactions.sql
    004_create_cash_balances.sql
    005_create_liabilities.sql
    006_create_tax_reserves.sql
    007_create_reconciliation_snapshots.sql
    008_create_indexes.sql

  src/
    portfolio_os/
      __init__.py

      db/
        __init__.py
        connection.py
        migrations.py
        pragmas.py

      models/
        __init__.py
        account.py
        instrument.py
        transaction.py
        cash_balance.py
        liability.py
        tax_reserve.py
        snapshots.py
        reconciliation.py
        states.py

      repositories/
        __init__.py
        accounts.py
        instruments.py
        transactions.py
        cash_balances.py
        liabilities.py
        tax_reserves.py
        reconciliation_snapshots.py

      validators/
        __init__.py
        decimals.py
        currencies.py
        accounts.py
        instruments.py
        transactions.py
        cash_balances.py
        liabilities.py
        tax_reserves.py
        snapshots.py

      ledger/
        __init__.py
        snapshot_builder.py
        position_calculator.py
        cash_calculator.py
        liability_view.py
        tax_reserve_view.py

      reconciliation/
        __init__.py
        service.py
        comparators.py
        tolerances.py
        serializer.py
        report_writer.py

      state/
        __init__.py
        state_machine.py
        stale_detector.py

      importers/
        __init__.py
        csv_snapshot_importer.py
        csv_transaction_importer.py

      cli/
        __init__.py
        init_db.py
        import_snapshot.py
        record_transaction.py
        run_reconciliation.py
        ledger_status.py

  tests/
    unit/
      test_decimal_policy.py
      test_currency_validation.py
      test_account_repository.py
      test_instrument_repository.py
      test_transaction_validation.py
      test_cash_balance_repository.py
      test_liability_repository.py
      test_tax_reserve_repository.py
      test_ledger_snapshot_builder.py
      test_reconciliation_comparators.py
      test_state_machine.py
      test_stale_detector.py

    integration/
      test_create_stage1_schema.py
      test_record_transaction_and_build_snapshot.py
      test_reconciliation_passed.py
      test_reconciliation_failed_position_diff.py
      test_reconciliation_failed_cash_diff.py
      test_broken_to_reconciled_after_correction.py

  scripts/
    reset_local_db.py
    seed_sample_accounts.py
    seed_sample_instruments.py
    run_sample_reconciliation.py
```

---

## 6. Implementation Order

주니어 개발자는 아래 순서로 구현한다.

```text
1. SQLite 연결 및 pragma 설정
2. migrations 작성
3. accounts 테이블 및 repository
4. instruments 테이블 및 repository
5. transactions 테이블 및 validation
6. cash_balances 테이블 및 validation
7. liabilities 테이블 및 validation
8. tax_reserves 테이블 및 validation
9. LedgerSnapshotBuilder
10. ExternalAccountSnapshot 모델 및 CSV importer
11. ReconciliationService 비교 로직
12. reconciliation_snapshots 저장
13. LedgerStateMachine
14. stale detector
15. CLI 명령
16. 단위 테스트
17. 통합 테스트
```

---

## 7. Minimum CLI Commands for Stage 1

Stage 1에서 필요한 최소 CLI 명령은 다음이다.

```text
portfolio-os init-db
portfolio-os add-account
portfolio-os add-instrument
portfolio-os record-transaction
portfolio-os record-cash-balance
portfolio-os record-liability
portfolio-os record-tax-reserve
portfolio-os import-external-snapshot
portfolio-os run-reconciliation
portfolio-os ledger-status
portfolio-os export-reconciliation-report
```

각 CLI는 내부적으로 위 Repository와 Service 인터페이스만 호출해야 한다.

---

## 8. Definition of Done

Stage 1 완료 조건은 다음이다.

1. SQLite DB가 초기화된다.
2. 모든 필수 테이블과 인덱스가 생성된다.
3. 모든 외래키 제약이 작동한다.
4. 금액·수량 계산에서 float가 사용되지 않는다.
5. 계좌와 종목 마스터가 없으면 거래 입력이 거부된다.
6. 거래, 현금, 부채, 세금 준비금이 입력된다.
7. 특정 기준일의 LedgerSnapshot이 생성된다.
8. 외부 계좌 스냅샷을 입력할 수 있다.
9. OS 원장과 외부 스냅샷을 대조할 수 있다.
10. 차이가 없으면 장부 상태가 `reconciled`가 된다.
11. 새 입력이 생기면 장부 상태가 `provisional`이 된다.
12. 허용 기간을 넘기면 장부 상태가 `stale`이 된다.
13. 대조 차이가 있으면 장부 상태가 `broken`이 된다.
14. 정정 입력 후 재대조하여 차이가 사라지면 `reconciled`로 복귀한다.
15. 대조 결과가 markdown 및 JSON 리포트로 출력된다.
16. 핵심 상태 전이와 대조 결과에 대한 통합 테스트가 통과한다.

---

## 9. Non-Negotiable Engineering Rules

```text
No float for money.
No direct update for historical transactions.
No transaction without account reference.
No buy/sell transaction without instrument reference.
No duplicated account snapshot for same account/date/currency.
No deletion of reconciliation history.
No reconciled status without successful reconciliation snapshot.
No silent correction.
No missing failure reason for broken status.
No external snapshot reconciliation without validation.
```

---

## 10. Final Stage 1 Rule

```text
Stage 1 is finished only when the system can answer this question with evidence:

"Does the OS ledger match the real account snapshot as of this date?"
```
