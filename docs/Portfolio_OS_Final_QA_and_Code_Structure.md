# Portfolio OS Final QA & Code Structure

Final QA Status: PASS

작성일: 2026-06-24

이 문서는 완료된 Portfolio OS 백엔드 코어와 프론트엔드 Mission Control MVP의 최종 QA 결과와 코드 구조를 설명한다. 이 작업은 새 개발 stage가 아니며, 기능 추가, 런타임 소스 수정, 의존성 추가, Tauri 스캐폴드, 인증, 브로커 연동, 자동매매, 신규 API 구현을 포함하지 않는다.

## 1. Executive Summary

Portfolio OS는 개인 포트폴리오를 로컬에서 운영하기 위한 Mission Control 시스템이다. 핵심 목적은 계좌, 상품, 거래, 현금, 정산, 리스크 검증, 수동 실행 기록, 예외 선언, 리포트와 컨텍스트 자료를 한 흐름에서 점검하게 하는 것이다.

Portfolio OS가 해결하는 문제는 "내 포트폴리오 상태의 기준점이 무엇인가", "어떤 주문 의도가 Risk Engine을 통과했는가", "수동으로 외부 브로커에서 실행한 행위가 정산 증거로 확인되었는가"를 분리해서 기록하고 검토하는 것이다. 즉, 거래 버튼을 누르는 앱이 아니라 판단, 승인, 실행 기록, 정산 확인, 감사 자료를 연결하는 로컬 운영 장치다.

Portfolio OS는 자동매매 봇이 아니다. 브로커에 주문을 보내는 API가 없고, 자동 주문 생성이나 자동 실행 경로도 없다. 프론트엔드는 SQLite 파일을 직접 읽지 않고 FastAPI API를 통해서만 데이터를 조회하거나 제한된 워크플로 입력을 보낸다. 수동 실행 기록은 이미 외부 브로커에서 사람이 수행한 행위를 사후 기록하는 용도이며, Portfolio OS가 브로커 실행을 대신하지 않는다.

현재 완료 상태는 백엔드 코어와 프론트엔드 Mission Control MVP가 함께 동작하는 단계다. 백엔드는 Stage 1 ledger truth, reconciliation, Stage 2 Risk Engine과 ticket workflow, manual execution, override, journal, reports, research/macro/senior/governance context를 포함한다. 프론트엔드는 Stage 1-10 로드맵의 Mission Control 대시보드, 정산 워크플로, risk/ticket 운영 루프, 수동 실행 기록, 정산 확인, override/journal/postmortem, reports center, context explorer, system boundaries 화면을 제공한다.

## 2. Authority Model

Portfolio OS의 권한 모델은 다음 경계를 유지한다.

- Ledger truth는 Stage 1 ledger와 reconciliation 상태에서 온다. `accounts`, `instruments`, `transactions`, `cash_balances`, `reconciliation_snapshots`가 포트폴리오 상태 판단의 기준이다.
- Risk Engine은 유일한 리스크 권한이다. 주문 의도는 Risk Engine 검증 결과를 거쳐야 하며, ticket 생성은 통과 또는 조정된 risk validation을 기반으로 한다.
- Human approval은 수동 실행 기록 전에 필요하다. 승인되지 않은 ticket은 manual execution logging으로 넘어갈 수 없다.
- Manual execution logging은 외부 브로커에서 이미 사람이 실행한 행위를 기록할 뿐이다. 이 기록은 Portfolio OS가 브로커 주문을 넣었다는 뜻이 아니다.
- Reconciliation evidence는 confirmation 전에 필요하다. pending manual execution은 정산 결과와 확인된 ledger transaction 증거가 있어야 확정될 수 있다.
- Override는 선언된 예외이며 공식 Risk Engine validation이 아니다. override confirm/cancel은 감사 결정을 기록하는 것이고, Risk Engine을 대체하지 않는다.
- Research, Macro, Senior Memo, Governance는 context only다. 이 자료들은 주문 권한이 아니며, Risk Engine과 ticket workflow를 우회하지 않는다.
- Reports는 audit/review material이다. Reports Center는 기존 Markdown/JSON 산출물을 안전하게 조회, 복사, 다운로드하게 할 뿐 주문, 승인, 실행 권한을 제공하지 않는다.

## 3. Completed Roadmap

완료된 백엔드/core 범위는 다음과 같다.

- Stage 1 ledger truth foundation: SQLite schema/migrations, Decimal 기반 금액 처리, append-only transaction, cash balance, snapshot builder, reconciliation, ledger status state machine, CLI.
- Stage 2 risk/ticket workflow: transaction intents, Risk Engine validation, risk reports, order tickets, approval/rejection event 기록.
- Stage 3 research/macro context: asset thesis, research packets/facts/missing data, macro snapshots/context packets.
- Stage 4 senior memo workflow: senior memo input bundles, sections, decision candidates, no-action alternatives, opposing arguments, QA results.
- Stage 5 governance/context health: governance policies, canary/golden tests, context packages, memory, system health, read-only integration sources, governance audit events.
- Frontend API adapter: FastAPI, Pydantic schemas, routers, structured error envelope, read-only dependencies와 scoped writable dependencies.

완료된 프론트엔드 stages는 다음과 같다.

1. Read-only FastAPI API
2. Mission Control Dashboard
3. Reconciliation Workflow
4. Intent / Risk / Ticket Creation
5. Approval / Manual Execution Logging
6. Reconciliation Confirmation
7. Override / Journal / Postmortem
8. Reports Center
9. Research / Macro / Senior / Governance Explorer
10. Final Hardening / System Boundaries / Desktop Packaging Readiness

## 4. Repository Structure

실제 저장소 구조 기준의 설명이다.

- `src/portfolio_os/`: Portfolio OS Python package 루트다. 도메인 모델, 서비스, repository, CLI, API adapter가 들어 있다.
- `src/portfolio_os/api/`: FastAPI adapter 계층이다. `app.py`가 앱을 만들고 `/api/v1` prefix로 router를 등록한다. `deps.py`는 DB path, app mode, snapshot/report dir, upload limit, read-only/writable DB dependency를 담당한다. `errors.py`는 structured error envelope를 등록한다. `reports.py`와 `artifacts.py`는 safe report reference와 snapshot artifact path 검증을 담당한다.
- `src/portfolio_os/api/routers/`: API route handler 모음이다. 실제 파일은 `health.py`, `ledger.py`, `accounts.py`, `instruments.py`, `snapshots.py`, `reconciliation.py`, `reports.py`, `context_explorer.py`, `risk.py`, `tickets.py`, `executions.py`, `overrides.py`, `journal.py`, `postmortems.py`다.
- `src/portfolio_os/api/schemas/`: Pydantic response/request schema 모음이다. accounts, health, instruments, ledger, snapshots, reconciliation, reports, context_explorer, risk, intents, tickets, executions, overrides, journal, postmortems schema가 있다.
- `src/portfolio_os/db/`: SQLite connection, pragmas, migration runner가 있다. `Database`는 read-only mode와 writable mode를 구분한다.
- `src/portfolio_os/repositories/`: Stage 1 core repository가 있다. accounts, instruments, transactions, cash balances, liabilities, tax reserves, reconciliation snapshots를 다룬다.
- Domain/service modules:
  - `ledger/`: ledger snapshot builder.
  - `reconciliation/`: reconciliation service, workflow, report writer.
  - `risk/`: Risk Engine, checks, action classifier, default policy, report writer, repositories.
  - `intents/`: transaction intent model, validator, repository, service.
  - `tickets/`: order ticket model, repository, service, report writer.
  - `execution/`: manual execution model, validator, repository, service.
  - `override/`: override ticket repository/service/model.
  - `journal/`: decision journal and postmortem repositories/services/models.
  - `reports` model은 API의 `portfolio_os.api.reports.ReportRegistry`로 노출된다.
  - `research/`, `macro/`, `senior/`, `governance/`, `context/`, `integrations/`: context explorer와 governance/context health의 upstream 자료를 제공한다.
- `frontend/`: React + TypeScript + Vite Mission Control frontend다.
- `frontend/src/app/`: app bootstrap, providers, router가 있다. `router.tsx`가 stable route와 error/404 fallback을 등록한다.
- `frontend/src/api/`: API client, response/request type, mock fallback이 있다.
- `frontend/src/api/queries/`: TanStack Query hook 모음이다. accounts, health, ledger, reconciliation, reports, contextExplorer, risk, intents, tickets, executions, overrides, journal, postmortems query/mutation hook이 있다.
- `frontend/src/api/mocks/`: mock mode용 sample data와 mock client가 있다. mock records는 `DEMO-*` 또는 sample label로 실제 포트폴리오 상태와 구분된다.
- `frontend/src/components/`: layout, mission-control panel, status badge, table component 등 공통 UI가 있다.
- `frontend/src/features/`: dashboard, ledger, reconciliation, risk, tickets, executions, overrides, journal, postmortems, reports, context-explorer, system 화면이 있다.
- `frontend/src/styles/`: global CSS와 theme CSS가 있다.
- `tests/`: Python unit/integration tests가 있다. Stage 1-5 core tests와 frontend stage API integration tests를 포함한다.
- `docs/frontend/`: frontend stage별 implementation report, API contract, handoff, desktop packaging readiness 문서가 있다.

## 5. Backend Architecture

FastAPI 앱은 `portfolio_os.api.app:create_app`에서 생성된다. 앱은 title/version을 설정하고, `PORTFOLIO_OS_DB_PATH` 등 환경 설정을 해석한 뒤, error handler를 등록하고 `api_router`를 `/api/v1` prefix로 include한다.

Router 조직은 도메인별로 분리되어 있다. health, ledger, accounts, instruments 같은 조회 router와 snapshots/reconciliation/intents/tickets/executions/overrides 같은 제한된 mutation router가 같은 API adapter 아래에 있지만, DB dependency를 통해 read-only와 writable 경계를 나눈다.

Pydantic schema는 API wire contract의 안정성을 담당한다. 도메인 모델이나 repository row를 프론트엔드가 이해할 수 있는 response shape로 변환하고, POST payload의 검증 조건을 명시한다.

SQLite는 `src/portfolio_os/db/connection.py`의 `Database` abstraction을 통해 사용된다. `read_only=True`일 때 SQLite URI `mode=ro`를 사용하고 read-only pragmas를 적용한다. migration readiness는 `deps.inspect_database`가 migration checksum과 필수 API table 존재 여부를 확인한다.

기본 조회 API는 `get_database`를 통해 read-only database를 연다. mutation endpoint는 `get_writable_database`를 명시적으로 사용한다. 따라서 읽기 화면은 DB를 수정하지 않고, 쓰기 endpoint는 snapshot artifact import, reconciliation run, intent/risk validation, ticket decision, manual execution logging, reconciliation confirmation, override decision 같은 제한된 워크플로에만 존재한다.

Structured error envelope는 다음 형태다.

```json
{
  "error": {
    "code": "error_code",
    "message": "human-readable message",
    "details": null
  }
}
```

Report registry는 safe-reference model이다. 서버가 `report_...` opaque reference를 만들고, detail/download 요청에서 category와 filename을 decode한 뒤 category directory, filename suffix, path containment를 다시 검증한다. 절대 경로를 API response로 노출하지 않고, Markdown/JSON만 지원한다.

브로커 write path는 없다. API router와 service 계층은 브로커 주문 전송, 자동 주문 실행, 브로커 credential 저장을 제공하지 않는다.

## 6. Frontend Architecture

프론트엔드는 React + TypeScript + Vite 구조다. `frontend/package.json` 기준 runtime dependencies는 React, React Router, TanStack Query, lucide-react이며, dev checks는 TypeScript, ESLint, Vitest, Vite로 구성된다.

Router는 `frontend/src/app/router.tsx`에서 `createBrowserRouter`로 정의된다. 루트 shell은 `AppShell`이며, child routes로 dashboard, ledger, reconciliation, risk, tickets, executions, overrides, journal, postmortems, reports, context explorer, system page가 등록되어 있다. app-level `errorElement`와 unknown route `path: "*"` fallback이 있다.

Mission Control layout은 `frontend/src/components/layout/`의 `AppShell`, `Sidebar`, `TopSystemBar`를 중심으로 한다. dashboard는 system status, thesis map, pending actions, open tickets, alerts, activity timeline을 보여주는 운영 화면이다.

TanStack Query hook은 `frontend/src/api/queries/`에 모여 있다. GET query는 `apiGet`을 사용하고, mutation은 `apiPostJson` 또는 `apiPostForm`을 사용한다. mock mode에서는 GET fallback만 sample data로 전환되고, POST mutation은 mock success를 만들지 않고 차단된다.

API client는 live FastAPI 호출을 우선 사용한다. 네트워크 실패나 dev proxy unavailable 상황에서는 mock source로 전환하고 UI shell에서 mock/source 상태를 표시한다. HTTP 4xx/5xx error envelope는 그대로 사용자에게 드러나며 fake success로 숨기지 않는다.

UI에는 한국어 권한 경고와 read-only tag가 포함된다. `/system` 화면은 no broker integration, no automatic trading, no frontend SQLite access, no CLI invocation, report/context inert rendering 같은 system boundaries를 보여준다.

Reports Center와 context explorer는 report/context content를 executable HTML로 렌더링하지 않는다. Reports Center는 `selectedReport.content`를 `<pre>` 안에 표시하고, context explorer는 detail payload를 문자열 또는 JSON stringify 결과로 변환해 `<pre>`에 표시한다.

반응형 설계와 route fallback도 구현되어 있다. unknown route는 404 fallback으로 이동하고, route error는 `RouteErrorPage`로 표시된다.

## 7. Main User Flows

### 7.1 Reconciliation Flow

1. 사용자가 외부 브로커나 계좌 snapshot CSV를 준비한다.
2. `/reconciliation` 화면에서 external CSV snapshot import를 실행한다.
3. API는 CSV를 검증하고 `data/imports/account_snapshots` 아래 artifact로 저장한다.
4. 사용자는 artifact summary를 검토한다.
5. reconciliation run을 실행하면 backend가 ledger snapshot과 external snapshot을 비교한다.
6. diff viewer가 positions, cash, liabilities, tax reserves 차이를 보여준다.
7. report viewer가 생성된 reconciliation Markdown report를 plaintext로 표시한다.

### 7.2 Official Manual Operating Loop

1. `/risk` 화면에서 transaction intent를 작성한다.
2. intent는 Risk Engine validation을 받는다.
3. validation이 passed 또는 adjusted이면 official manual order ticket을 생성할 수 있다.
4. `/tickets` 또는 `/tickets/:ticketId`에서 사람이 ticket을 approve 또는 reject한다.
5. approved ticket만 manual execution logging으로 넘어간다.
6. manual execution logging은 외부 브로커에서 이미 사람이 실행한 체결 정보를 기록하고 provisional transaction을 만든다.
7. 실행 기록은 pending reconciliation 상태가 된다.
8. `/executions`에서 reconciliation evidence가 충족된 execution만 confirm-after-reconciliation으로 확정한다.

### 7.3 Override Flow

1. `/overrides`에서 사람이 override를 선언한다.
2. override는 공식 Risk Engine validation이 아니라 명시적 예외와 warning/audit record로 저장된다.
3. override detail은 linked journal entry와 postmortem task visibility를 제공한다.
4. 사용자는 override를 confirm 또는 cancel할 수 있다.
5. confirm/cancel은 감사 결정이며 브로커 주문이나 자동 실행이 아니다.

### 7.4 Reports and Context Flow

1. `/reports`에서 category별 report catalog를 조회한다.
2. report detail은 opaque reference로만 열리고 Markdown/JSON content가 plaintext로 표시된다.
3. `/research`, `/macro`, `/senior-memos`, `/governance`에서 context record를 read-only로 탐색한다.
4. context 화면의 report link는 safe report reference만 `/reports?reference=...`로 연결한다.
5. 이 흐름은 검토와 감사 자료용이며 주문 권한을 갖지 않는다.

## 8. API Surface Map

모든 path는 `/api/v1` prefix 기준이다.

| Group | Method / Path | Type | Purpose | Authority Boundary |
| --- | --- | --- | --- | --- |
| health | `GET /health` | Read-only | API/database/app mode health 조회 | 운영 상태 표시만 한다. |
| ledger | `GET /ledger/status` | Read-only | ledger status 조회 | Stage 1 ledger state를 읽는다. |
| ledger | `GET /ledger/snapshot` | Read-only | ledger snapshot 조회 | ledger truth를 표시하되 수정하지 않는다. |
| ledger | `GET /accounts` | Read-only | account list 조회 | 계좌 기준 데이터를 읽는다. |
| ledger | `GET /instruments` | Read-only | instrument list 조회 | 상품 기준 데이터를 읽는다. |
| reconciliation | `POST /snapshots/external-imports` | Mutation | external CSV snapshot artifact 생성 | 외부 snapshot을 artifact로 저장한다. ledger cash truth로 직접 삽입하지 않는다. |
| reconciliation | `GET /reconciliations/latest` | Read-only | 최신 reconciliation 결과 조회 | 정산 상태 조회만 한다. |
| reconciliation | `POST /reconciliations` | Mutation | artifact 기반 reconciliation run 실행 | ledger와 외부 증거 비교 및 결과 저장이다. 브로커/주문 권한이 아니다. |
| reconciliation | `GET /reconciliations/{reconciliation_id}` | Read-only | reconciliation detail 조회 | 정산 결과 조회만 한다. |
| reconciliation | `GET /reconciliations/{reconciliation_id}/report` | Read-only | reconciliation Markdown report 조회 | report는 감사 자료다. |
| intents | `POST /intents` | Mutation | transaction intent 생성 | intent는 주문이 아니며 Risk Engine 전 단계다. |
| risk validations | `POST /intents/{intent_id}/validate` | Mutation | Risk Engine validation 실행 및 저장 | Risk Engine만 공식 validation 권한이다. |
| risk validations | `GET /risk/validations/{risk_validation_id}` | Read-only | validation detail 조회 | Risk result 조회만 한다. |
| tickets | `GET /tickets` | Read-only | ticket list 조회 | ticket registry 조회다. |
| tickets | `POST /tickets` | Mutation | passed/adjusted risk validation에서 ticket 생성 | Risk validation 없이 official ticket을 만들 수 없다. |
| tickets | `GET /tickets/{ticket_id}` | Read-only | ticket detail/event 조회 | ticket 상태 조회다. |
| tickets | `POST /tickets/{ticket_id}/approve` | Mutation | 사람이 ticket 승인 기록 | human approval 기록이며 브로커 실행이 아니다. |
| tickets | `POST /tickets/{ticket_id}/reject` | Mutation | 사람이 ticket 거절 기록 | 실행 경로를 닫는 감사 기록이다. |
| executions | `GET /executions/pending` | Read-only | pending manual execution 조회 | 정산 대기 상태 조회다. |
| executions | `POST /executions` | Mutation | approved ticket에 대한 manual execution logging | 외부 브로커에서 사람이 수행한 실행을 기록한다. Portfolio OS가 주문하지 않는다. |
| executions | `GET /executions/{execution_id}` | Read-only | manual execution detail 조회 | 실행 기록 조회다. |
| executions | `POST /executions/confirm-after-reconciliation` | Mutation | reconciliation evidence 기반 confirmation | 정산 증거가 있어야 확정된다. |
| overrides | `GET /overrides` | Read-only | override list 조회 | 예외 기록 조회다. |
| overrides | `POST /overrides` | Mutation | override 선언 | 공식 Risk Engine validation이 아닌 예외 선언이다. |
| overrides | `GET /overrides/{override_id}` | Read-only | override detail 조회 | journal/postmortem visibility를 제공한다. |
| overrides | `POST /overrides/{override_id}/confirm` | Mutation | override confirm audit decision | 브로커 실행이나 official risk ticket이 아니다. |
| overrides | `POST /overrides/{override_id}/cancel` | Mutation | override cancel audit decision | 예외를 취소하는 감사 기록이다. |
| journal | `GET /journal` | Read-only | decision journal list 조회 | 감사/회고 자료 조회다. |
| journal | `GET /journal/{journal_id}` | Read-only | journal detail 조회 | 주문 권한이 없다. |
| postmortems | `GET /postmortems` | Read-only | scheduled postmortem task 조회 | completion recording은 구현되지 않았다. |
| reports | `GET /reports/categories` | Read-only | report category 조회 | report registry 조회다. |
| reports | `GET /reports` | Read-only | report list 조회 | audit/review material 조회다. |
| reports | `GET /reports/{report_reference}` | Read-only | opaque reference 기반 report detail 조회 | 임의 파일 읽기가 아니다. |
| reports | `GET /reports/{report_reference}/download` | Read-only | 검증된 Markdown/JSON report 다운로드 | registry-resolved file만 제공한다. |
| research | `GET /research` | Read-only | research context list 조회 | context only, order authority 없음. |
| research | `GET /research/{research_id}` | Read-only | research detail 조회 | report links도 safe reference만 사용한다. |
| macro | `GET /macro` | Read-only | macro context list 조회 | context only. |
| macro | `GET /macro/{macro_id}` | Read-only | macro detail 조회 | order authority 없음. |
| senior memos | `GET /senior-memos` | Read-only | senior memo list 조회 | decision support context다. |
| senior memos | `GET /senior-memos/{memo_id}` | Read-only | senior memo detail 조회 | ticket/Risk Engine을 우회하지 않는다. |
| governance | `GET /governance` | Read-only | governance/context health overview 조회 | system context 조회다. |
| governance | `GET /governance/events` | Read-only | governance audit events 조회 | 감사 자료 조회다. |

## 9. Frontend Route Map

`frontend/src/app/router.tsx` 기준 stable routes는 다음과 같다.

| Route | Page | Description |
| --- | --- | --- |
| `/` | DashboardPage | Mission Control dashboard. ledger/reconciliation/ticket/execution/override/report/context 상태를 요약한다. |
| `/ledger` | LedgerPage | accounts, instruments, ledger status/snapshot 조회 화면이다. |
| `/reconciliation` | ReconciliationPage | external snapshot import, reconciliation run, diff viewer, report viewer를 제공한다. |
| `/risk` | RiskWorkspacePage | intent 생성, Risk Engine validation, ticket 생성 workspace다. |
| `/tickets` | TicketsPage | order ticket register다. |
| `/tickets/:ticketId` | TicketDetailPage | ticket detail, approval/rejection, allowed manual execution logging을 제공한다. |
| `/executions` | PendingExecutionsPage | pending manual execution과 reconciliation confirmation 화면이다. |
| `/overrides` | OverridesPage | override register와 exception declaration 화면이다. |
| `/overrides/:overrideId` | OverrideDetailPage | override detail, linked journal, postmortem task visibility를 제공한다. |
| `/journal` | JournalPage | decision journal list다. |
| `/journal/:journalId` | JournalDetailPage | decision journal detail이다. |
| `/postmortems` | PostmortemsPage | scheduled postmortem tasks 조회 화면이다. |
| `/reports` | ReportsPage | Reports Center. safe local Markdown/JSON artifacts를 plaintext로 조회한다. |
| `/research` | ResearchPage | research context list/detail explorer다. |
| `/research/:researchId` | ResearchPage | 특정 research context detail을 표시한다. |
| `/macro` | MacroPage | macro context list/detail explorer다. |
| `/macro/:macroId` | MacroPage | 특정 macro context detail을 표시한다. |
| `/senior-memos` | SeniorMemosPage | senior memo list/detail explorer다. |
| `/senior-memos/:memoId` | SeniorMemosPage | 특정 senior memo detail을 표시한다. |
| `/governance` | GovernancePage | governance/context health explorer다. |
| `/system` | SystemPage | System Boundaries와 desktop packaging readiness를 보여준다. |
| unknown route | NotFoundPage | `path: "*"` 404 fallback이다. dashboard와 system page로 돌아갈 수 있다. |

App-level route error는 `RouteErrorPage`로 처리된다.

## 10. Data and State Model

Portfolio OS의 데이터와 상태 모델은 다음처럼 이해할 수 있다.

- Accounts: 포트폴리오 계좌 단위다. account name, institution, account type, base currency, active 상태를 가진다.
- Instruments: 거래 대상 상품 기준 데이터다. symbol, currency, exchange, precision, fractional 가능 여부를 포함한다.
- Transactions: ledger truth의 핵심 기록이다. trade/settlement date, quantity, price, fee, tax, net cash amount, confirmation/void 상태를 가진다.
- Cash balances: 내부 ledger 기준 cash anchor다. 외부 snapshot은 cash balance에 직접 들어가지 않고 reconciliation actual로 쓰인다.
- Reconciliation results: ledger expected와 external actual snapshot의 비교 결과다. positions, cash, liabilities, tax reserves 차이와 ledger status before/after를 저장한다.
- Risk validation results: transaction intent에 대해 Risk Engine이 계산한 통과/조정/거절 결과와 checks, warnings를 저장한다.
- Order tickets: 공식 manual operating loop의 ticket이다. Risk validation을 기반으로 생성되고 approval/rejection event를 가진다.
- Manual executions: approved ticket에 대해 사람이 외부 브로커에서 수행한 실행을 기록한다. pending reconciliation과 reconciled 상태 흐름을 가진다.
- Override tickets: 공식 Risk Engine path 밖에서 선언된 예외다. human reason, risk warning, deadline/postmortem schedule과 함께 감사 기록으로 남는다.
- Decision journal entries: ticket decision, override decision 등 인간 판단의 이유와 상태를 기록한다.
- Postmortem tasks: override 등과 연결된 회고 예정 작업이다. completion recording UI는 아직 없다.
- Reports and context records: reconciliation/risk/ticket/senior/research/macro/governance/canary/health/context package 등에서 생성된 Markdown/JSON 산출물과 read-only context 자료다.

## 11. Safety and Security Boundaries

최종 QA에서 확인한 안전 경계는 다음과 같다.

- React는 SQLite를 직접 읽지 않는다. runtime source에서 SQLite access/import pattern은 발견되지 않았다.
- React는 CLI를 호출하지 않는다. subprocess/process invocation pattern은 runtime source에서 발견되지 않았다.
- React는 CLI stdout을 parse하지 않는다. API client는 HTTP fetch와 mock fallback만 사용한다.
- 브로커 write API가 없다.
- 자동매매, 자동 주문, 자동 실행 경로가 없다.
- untrusted report/context content를 executable HTML로 렌더링하지 않는다. `dangerouslySetInnerHTML`과 `innerHTML` 사용은 발견되지 않았다.
- Reports Center는 report content를 `<pre>{selectedReport.content}</pre>`로 표시한다.
- Context explorer는 detail payload를 text/JSON으로 변환해 `<pre>`로 표시한다.
- Report reference는 opaque `report_...` 값이며, 서버에서 category, filename, suffix, directory containment를 검증한다.
- 임의 파일 읽기 API가 없다. report download는 registry-resolved Markdown/JSON file로 제한된다.
- mock mode는 API source 상태와 sample data label로 실제 포트폴리오 상태와 구분된다.
- runtime frontend source에서 direct-trade CTA string `Buy Now`, `Sell Now`, `Quick Trade`, `즉시 매수`, `즉시 매도`, `利됱떆 留ㅼ닔`, `利됱떆 留ㅻ룄`는 발견되지 않았다.
- broad SQLite text search에서 `/system` 화면의 "No frontend SQLite access" 설명 문장만 발견되었다. 이는 접근 경로가 아니라 안전 경계 설명이므로 이슈가 아니다.
- broad CLI text search에서 backend start command 표시 문구가 발견되었다. 이는 사용자를 위한 실행 안내 텍스트이며 subprocess 호출이 아니므로 이슈가 아니다.

브라우저 localhost 검증은 이번 최종 QA에서 통과했다고 주장하지 않는다. 이 문서의 PASS는 자동화 테스트, production build, static safety search, route/static source inspection 기준이다.

## 12. Final QA Checklist

### Backend

| Check | Result |
| --- | --- |
| `python -m compileall -q src tests` | PASS. 출력 없음. |
| `python -m pytest -q` | PASS. `105 passed, 1 warning in 115.33s`. |

Backend warning:

- `C:\Users\dahye\AppData\Roaming\Python\Python313\site-packages\starlette\formparsers.py:12`: `PendingDeprecationWarning: Please use import python_multipart instead.`

### Frontend

| Check | Result |
| --- | --- |
| `npm.cmd run typecheck` | PASS. |
| `npm.cmd run lint` | PASS. |
| `npm.cmd run test` | PASS. `Test Files 11 passed (11)`, `Tests 46 passed (46)`. |
| `npm.cmd run build` | PASS. Vite build succeeded, `1673 modules transformed`. |

### Safety Searches

| Search | Result |
| --- | --- |
| direct SQLite access/import patterns in `frontend/src` runtime source | PASS. No findings. |
| subprocess/process invocation patterns in `frontend/src` runtime source | PASS. No findings. |
| prohibited direct-trade CTA strings in `frontend/src` runtime source | PASS. No findings. |
| `dangerouslySetInnerHTML` and `innerHTML` in `frontend/src` | PASS. No findings. |

Notes:

- Broad SQLite text search found only the `/system` page safety text "No frontend SQLite access".
- Broad CLI text search found display-only local run commands and "No CLI invocation" boundary text, not runtime execution.

### Route / Static Checks

| Check | Result |
| --- | --- |
| all stable frontend routes are registered | PASS. Routes listed in section 9 are present in `frontend/src/app/router.tsx`. |
| `/system` exists | PASS. `path: "system"` is registered. |
| app-level route error fallback exists | PASS. `errorElement: <RouteErrorPage />` is registered. |
| 404 fallback exists | PASS. `path: "*"` is registered with `NotFoundPage`. |
| Reports Center renders report content as plaintext/inert content | PASS. Report content is rendered in `<pre>`. |
| Context explorer renders detail content as plaintext/inert content | PASS. Detail content is rendered in `<pre>`. |

Final QA Status: PASS

## 13. How to Run Locally

Backend setup and start from repository root:

```powershell
python -m pip install -e ".[dev]"
python -m portfolio_os.cli.main init-db
python -m uvicorn portfolio_os.api.app:app --host 127.0.0.1 --port 8000
```

Frontend install and start:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Vite serves:

```text
http://127.0.0.1:5173
```

Vite proxies `/api` to:

```text
http://127.0.0.1:8000
```

Frontend production build:

```powershell
cd frontend
npm.cmd run build
```

Tests and checks:

```powershell
python -m compileall -q src tests
python -m pytest -q
cd frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```

Environment variables used by the API:

- `PORTFOLIO_OS_DB_PATH`: SQLite database path. Default is `data/portfolio_os.sqlite3`.
- `PORTFOLIO_OS_APP_MODE`: app mode label. Default is `local-operating-loop`.
- `PORTFOLIO_OS_SNAPSHOT_DIR`: external snapshot artifact directory. Default is `data/imports/account_snapshots`.
- `PORTFOLIO_OS_REPORT_DIR`: reconciliation report directory. Default is `data/exports/reconciliation_reports`.
- `PORTFOLIO_OS_UPLOAD_LIMIT_BYTES`: snapshot upload size limit. Default is 5 MiB.

Frontend mock variable:

- `VITE_USE_MOCKS=true`: force frontend sample data mode. Mutations remain disabled in mock mode.

## 14. Known Limitations

- 인증과 RBAC가 없다.
- 브로커 연동이 없다.
- 자동매매가 없다.
- ticket modification flow가 없다.
- override execution logging이 없다.
- postmortem completion recording이 없다.
- persistent audit export UI가 없다.
- Tauri scaffold가 없다.
- future broker work는 먼저 read-only import로 시작해야 하며 broker write를 추가하면 안 된다.
- browser localhost verification은 이번 최종 QA에서 수행/통과로 기록하지 않았다.

## 15. Suggested Next Steps

다음 단계는 비침습적인 정리 작업만 권장한다.

- 현재 상태를 git commit으로 고정한다.
- release tag를 만든다.
- 최종 demo script를 작성한다.
- 주요 화면 screenshot을 남긴다.
- portfolio/CV summary에 "local portfolio Mission Control, not auto trading" 관점으로 정리한다.
- optional v2 roadmap을 별도 문서로 만든다.
- production auth/security는 이후 단계에서 별도 설계한다.
- desktop packaging은 이후 단계에서 Tauri 권한 모델을 먼저 정의한 뒤 진행한다.
