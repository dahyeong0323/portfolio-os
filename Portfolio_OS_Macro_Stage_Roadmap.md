# Portfolio OS 개발 로드맵 — Macro-Stage Skeleton

> 목적: `프로젝트 바이블.md`와 `소프트웨어 아키텍쳐 진단서.md`를 기준으로, Portfolio OS 전체 개발을 Agile 방식으로 진행하기 위한 최상위 Macro-Stage 구조를 정의한다.  
> 범위: 이 문서는 **뼈대 설계 문서**다. 데이터베이스 컬럼, 함수명, API 명세, 상태 전이도 같은 구체적 Tech Spec은 포함하지 않는다.

---

## 0. Source of Truth

이 로드맵은 아래 두 문서만을 기준으로 한다.

1. `프로젝트 바이블.md`
   - Ledger-first
   - No sync, no official recommendation
   - Human final approval
   - LLM judges; code calculates
   - Override must be declared
   - Macro-aware portfolio risk
   - Risk-engine-gated manual order ticket

2. `소프트웨어 아키텍쳐 진단서.md`
   - 구현 순서 재조정
   - Macro Layer를 Senior Agent보다 앞에 배치
   - Override + Journal을 후반이 아니라 초기 운영 루프에 전진 배치
   - Model QA / RAG / full Context Economy는 후반으로 연기
   - Broker API 자동 실행은 MVP에서 제외
   - 하나의 포트폴리오 상태를 모든 모듈이 동일하게 이해하도록 계약 정의 필요

---

## 1. 핵심 재구성 원칙

기존 Phase 0~10을 그대로 나열하지 않고, 다음 원칙에 따라 5개의 Macro-Stage로 재구성한다.

```text
AI보다 Ledger가 먼저다.
Senior보다 Macro가 먼저다.
Trading UI보다 Ticket State가 먼저다.
Telegram보다 Manual Operating Loop가 먼저다.
Override는 후반 기능이 아니라 초기 생존 장치다.
Model QA / RAG / Broker API는 운영 루프가 검증된 뒤에 붙인다.
```

---

## 2. 전체 Macro-Stage 구조

```text
Macro-Stage 1 — Ledger Truth Foundation
Macro-Stage 2 — Risk-Gated Manual Operating Loop
Macro-Stage 3 — Fact Research & Macro Context Layer
Macro-Stage 4 — Senior Decision Memo Layer
Macro-Stage 5 — Governance, Context Economy & Optional Integrations
```

핵심 해석:

```text
Stage 1~2 = Portfolio OS의 생존 가능성 검증
Stage 3~4 = AI 판단 보조 레이어
Stage 5   = 장기 운영 안정화 레이어
```

---

# Macro-Stage 1: Ledger Truth Foundation

## 핵심 목표 (Objective)

Portfolio OS의 “진실 원천”을 만든다.

이 단계의 본질은 AI가 아니라, 실제 계좌·현금·부채·세금 준비금·수동 거래 기록이 하나의 공식 장부 안에서 재구성되고 대조되는 것이다.

Portfolio OS는 여기서부터 시작한다.

```text
정확한 장부가 없으면 Research도, Senior Memo도, Risk Engine도 전부 쓰레기 입력 위에서 작동한다.
```

---

## 포함되는 서브 페이즈 (Sub-Phases)

- Phase 0 — Architecture Freeze
- 진단서 추가 단계 — 기반 동결과 계약 정의
- Phase 1 — Ledger MVP
- Phase 2 — Reconciliation Engine
- 진단서 추가 요소 — 가치평가/환율 기준 레이어
- 진단서 추가 요소 — 계좌/자산 기준 마스터

---

## 주요 구현 대상 (Key Components)

- 아키텍처 기준 문서 고정
- 공통 상태 계약
- 공식 포트폴리오 원장
- 계좌 기준 정보
- 자산 기준 정보
- 실제 계좌 스냅샷 입력/비교 모듈
- Reconciliation Engine
- 가격/환율 기준 시점 관리
- 장부 상태 판정 정책

예시 상태:

```text
reconciled
provisional
stale
broken
```

---

## 성공 기준 (Definition of Done)

이 단계가 끝났다고 판단할 수 있는 기준은 다음이다.

1. 실제 계좌 스냅샷과 OS 장부를 비교할 수 있다.
2. 보유 수량, 현금, 부채, 세금 준비금, 미확정 수동 거래가 하나의 공식 장부에서 재구성된다.
3. 장부 상태가 명확히 판정된다.
4. `ledger_status != reconciled`일 때 공식 추천이 차단된다.
5. 단, No-sync 상황에서도 emergency override ticket은 생성 가능해야 한다.
6. Senior Agent, full Research Agent, Macro Layer, Telegram 자동화, broker API, RAG 없이도 v0.1이 의미 있게 작동한다.

---

## 이 단계에서 절대 하지 말 것

- Senior Agent 구현
- 자동매매 구현
- Telegram 자동화에 집착
- full Research Agent 구현
- RAG / Context Economy 구현
- broker API 자동 주문 구현
- 멋진 리포트 생성에 집중

이 단계의 질문은 단 하나다.

```text
내 실제 계좌와 OS 장부가 맞는가?
```

---

# Macro-Stage 2: Risk-Gated Manual Operating Loop

## 핵심 목표 (Objective)

AI 없이도 “거래 전 검증 → 인간 승인 → 수동 실행 → 기록 → 다음 대조”의 운영 루프를 완성한다.

이 단계부터 Portfolio OS는 단순 장부가 아니라 실제 투자 행동을 통제하는 운영체제가 된다.

```text
공식 장부가 있고,
리스크 검증이 있고,
주문 티켓이 있고,
인간 승인이 있고,
수동 실행 기록이 있고,
우회 거래도 시스템 안에 남는다.
```

---

## 포함되는 서브 페이즈 (Sub-Phases)

- Phase 3 — Risk Engine Skeleton
- Phase 4 — Manual Order Ticket
- Phase 5 — Telegram Layer
  - 단, 핵심이 아니라 선택적 전달 어댑터로 취급
- Phase 9 — Override + Journal
  - 원래 후반이지만 이 단계로 전진 배치
- Decision Journal / Post-Mortem 초기 버전
- Manual Execution Log 운영 루프

---

## 주요 구현 대상 (Key Components)

- Risk / Constraint Engine
- Manual Order Ticket
- Human Approval Workflow
- Provisional Execution Log
- Declared Override System
- Decision Journal
- Post-Mortem 기록 구조
- Telegram 또는 markdown 기반 전달 레이어

---

## 성공 기준 (Definition of Done)

이 단계가 끝났다고 판단할 수 있는 기준은 다음이다.

1. 모든 거래 의도는 Risk Engine을 통과한다.
2. Risk Engine은 각 거래 의도에 대해 다음 중 하나를 반환한다.

```text
PASSED
REJECTED
ADJUSTED
```

3. 검증된 주문 티켓 없이 공식 주문 제안이 생성되지 않는다.
4. 인간이 직접 실행한 거래는 provisional 상태로 기록된다.
5. 다음 reconciliation에서 provisional 거래가 확정 또는 문제 상태로 판정된다.
6. 시스템 밖 거래는 금지하는 대신 Declared Override로 흡수된다.
7. 모든 실제 거래는 다음 중 하나에 연결된다.

```text
validated order ticket
declared override ticket
```

8. Decision Journal에는 승인, 거절, 수정, override, 감정적 거래 위험, 사후 복기 필요 여부가 남는다.

---

## 이 단계에서 중요한 설계 판단

Override + Journal은 후반 기능이 아니다.

Manual Order Ticket이 생기는 순간부터 Shadow Trading 리스크가 생긴다.  
따라서 Override는 Stage 2에 반드시 들어와야 한다.

```text
우회를 막으려 하지 말고,
우회를 시스템 안으로 끌어들여 기록 가능한 예외로 만든다.
```

---

## 이 단계에서 절대 하지 말 것

- Senior Agent가 계산하게 만들기
- LLM이 매수 금액을 확정하게 만들기
- Risk Engine 검증 없는 주문 티켓 생성
- Telegram을 핵심 엔진처럼 다루기
- broker API 자동 실행 붙이기
- 인간 승인 없는 실행

이 단계의 질문은 단 하나다.

```text
내 실제 거래 행동이 시스템 안에서 통제되고 기록되는가?
```

---

# Macro-Stage 3: Fact Research & Macro Context Layer

## 핵심 목표 (Objective)

Senior Agent가 판단하기 전에, 자산별 사실 자료와 포트폴리오 전체의 공통 위험 노출을 먼저 만든다.

이 단계의 본질은 추천이 아니라 판단 재료의 정규화다.

```text
Research는 판단하지 않는다.
Macro는 전체 포트폴리오 위험을 본다.
Senior는 이 둘이 준비된 뒤에만 올라온다.
```

---

## 포함되는 서브 페이즈 (Sub-Phases)

- Phase 6 — Research Agent
- Anti-thesis QA
  - 단, 독립 대형 에이전트가 아니라 Research Packet 검증 규칙으로 시작
- Phase 8 — Macro Layer
  - Senior보다 앞에 전진 배치
- Crash Playbook 초기 정책
- Delta-based Review의 얇은 초기 형태

---

## 주요 구현 대상 (Key Components)

- Fact-only Research Packet
- Anti-thesis QA
- 금지 판단 표현 검사
- Missing Data 표시
- Source List 관리
- Macro & Correlation Risk Layer
- Portfolio Factor Diagnosis
- Regime Classification
- Crash Playbook Policy
- Risk Engine에 전달할 macro/risk envelope

---

## Research Packet의 역할

Research Agent는 애널리스트다.  
하지만 추천자는 아니다.

Research Packet은 다음을 포함해야 한다.

```text
Bull facts
Bear facts
Neutral facts
Thesis-supporting facts
Thesis-challenging facts
Missing data
Source list
Research status
```

금지되는 표현:

```text
buy
sell
attractive
should add
good opportunity
undervalued
overvalued
strongly recommended
```

---

## Macro Layer의 역할

Macro Layer는 개별 자산이 아니라 포트폴리오 전체의 공통 위험 노출을 본다.

진단 대상 예시:

```text
Risk-on exposure
Liquidity sensitivity
BTC-related exposure
Nasdaq/growth exposure
Correlation stress
Defensive buffer
Macro regime
```

Macro Regime 예시:

```text
Normal
Stress
Crisis
```

---

## 성공 기준 (Definition of Done)

이 단계가 끝났다고 판단할 수 있는 기준은 다음이다.

1. Research Agent는 사실만 정리하고 추천하지 않는다.
2. 모든 Research Packet에는 반대 논리가 포함된다.
3. Anti-thesis가 없는 Research Packet은 Senior Agent로 넘어가지 않는다.
4. Macro Layer는 포트폴리오 전체의 공통 factor exposure를 진단한다.
5. Macro regime 변화가 Risk Engine의 허용 범위에 영향을 준다.
6. Senior Agent 없이도 “이번 주 포트폴리오가 더 위험해졌는가, 덜 위험해졌는가”를 판단할 수 있다.
7. Senior Agent는 이 단계가 끝난 뒤에만 붙일 수 있다.

---

## 이 단계에서 중요한 설계 판단

진단서의 핵심 지적은 다음이다.

```text
Macro Layer가 Senior Agent보다 뒤에 있으면,
Senior Agent는 포트폴리오 수준 macro/correlation 진단 없이 판단하게 된다.
그 경우 그는 진짜 Senior Agent가 아니다.
```

따라서 Macro Layer는 Senior보다 먼저 또는 최소한 동시에 올라와야 한다.  
이 로드맵에서는 명확히 Senior보다 먼저 배치한다.

---

## 이 단계에서 절대 하지 말 것

- Research Agent가 buy/sell 판단하기
- Anti-thesis 없는 리서치를 valid 처리하기
- Macro Layer 없이 Senior Agent 먼저 만들기
- 거대한 factor model부터 만들기
- 과도하게 정밀한 regime 예측 모델 만들기
- 모든 원문을 무식하게 LLM context에 넣기

이 단계의 질문은 단 하나다.

```text
Senior가 판단하기 전에 필요한 사실과 포트폴리오 맥락이 준비되었는가?
```

---

# Macro-Stage 4: Senior Decision Memo Layer

## 핵심 목표 (Objective)

Senior Agent를 “주문 생성기”가 아니라 “구조화된 투자 판단 메모 작성자”로 붙인다.

이 단계에서 AI는 계산하지 않는다.  
AI는 장부, 리서치, 매크로, 리스크 맥락을 바탕으로 행동 후보와 no-action alternative를 제시한다.

```text
Senior Agent = judgment
Risk Engine = calculation and hard constraints
Trading Agent = validated ticket communicator
Human = final decision maker
```

---

## 포함되는 서브 페이즈 (Sub-Phases)

- Phase 7 — Senior Agent
  - 단, Macro Layer 이후로 이동
- Senior Memo Generation
- Portfolio-level Diagnosis
- No-action Alternative
- Strongest Opposing Argument
- Required Risk Engine Validation
- Trading Agent의 제한적 티켓 요약 기능

---

## 주요 구현 대상 (Key Components)

- Senior Investor Agent
- Senior Memo
- Decision Candidate
- No-action Alternative Generator
- Opposing Argument Section
- Risk Engine Pre-check Envelope 해석
- Trading Agent Summary Layer

---

## Senior Memo의 필수 성격

Senior Memo는 투자 판단 메모다.  
주문 명령서가 아니다.

포함해야 할 내용:

```text
Executive summary
Portfolio-level diagnosis
Macro/correlation risk interpretation
Cash and liquidity interpretation
Asset-level thesis status
Proposed action draft
No-action alternative
Strongest opposing argument
What would change the decision
Required Risk Engine validation
```

---

## Senior Agent가 할 수 있는 것

- thesis status 판단
- 시나리오별 해석
- 우선순위 결정
- no-action alternative 제시
- watchlist 우선순위 제시
- proposed action draft 생성

---

## Senior Agent가 할 수 없는 것

- 최종 주문 생성
- 매수 금액 확정
- 세금/현금 한도 계산
- Risk Engine 없는 강한 추천
- broker execution
- invalid research 기반 신규 매수 추천
- 인간 승인 없는 실행

---

## 성공 기준 (Definition of Done)

이 단계가 끝났다고 판단할 수 있는 기준은 다음이다.

1. Senior Agent는 Research Packet과 Macro Layer 진단을 입력으로 받는다.
2. Senior Memo는 장황한 리포트가 아니라 의사결정에 필요한 구조화 메모다.
3. 모든 행동 후보에는 no-action alternative가 함께 제시된다.
4. 모든 행동 후보에는 strongest opposing argument가 포함된다.
5. Senior Agent는 숫자 한도를 직접 확정하지 않는다.
6. Senior Memo가 생성되어도 Risk Engine 검증 전에는 공식 주문 티켓으로 승격되지 않는다.
7. Trading Agent는 Senior 텍스트를 직접 믿지 않고 Risk Engine이 검증한 결과만 사용한다.

---

## 이 단계에서 중요한 설계 판단

Senior Agent는 시스템의 왕이 아니다.  
Senior Agent는 Risk Engine, Ledger, Reconciliation, Macro Layer, Human Approval에 의해 제약되는 판단 레이어다.

```text
Senior는 판단한다.
하지만 계산하지 않는다.
Senior는 제안한다.
하지만 실행하지 않는다.
Senior는 설득한다.
하지만 최종 승인하지 않는다.
```

---

## 이 단계에서 절대 하지 말 것

- Senior Agent에게 현금 한도 계산 맡기기
- Senior Agent가 주문 티켓 직접 확정하기
- Senior Memo를 공식 추천으로 오해하게 만들기
- Risk Engine 없이 sizing 확정하기
- Senior를 Research/Macro보다 먼저 만들기
- no-action alternative 없는 메모 허용하기

이 단계의 질문은 단 하나다.

```text
AI 판단이 계산과 실행 권한 없이, 의사결정을 더 선명하게 만드는가?
```

---

# Macro-Stage 5: Governance, Context Economy & Optional Integrations

## 핵심 목표 (Objective)

이미 돌아가는 Portfolio OS를 장기 운영 가능한 시스템으로 만든다.

이 단계의 본질은 기능 추가가 아니라 다음 리스크를 통제하는 것이다.

```text
prompt drift
model degradation
token bankruptcy
memory explosion
input friction
maintenance burden
broker API risk
```

---

## 포함되는 서브 페이즈 (Sub-Phases)

- Phase 10 — Model QA + Context Economy
- Prompt Governance
- Canary Run
- Golden Test Set
- Context Economy / RAG / Token Budget
- 선택적 Read-only Broker Integration
- Telegram 고도화
- 장기 Post-Mortem / Review Cadence 강화

---

## 주요 구현 대상 (Key Components)

- Model QA Layer
- Prompt Governance
- Canary QA
- Golden Test Set
- Context Economy Layer
- Delta Review
- Thesis Memory
- Decision Memory
- Token Budget Control
- Optional Read-only Broker Adapter
- Optional UI/Notification Adapter

---

## Context Economy의 원칙

LLM에게 모든 것을 읽히지 않는다.

Senior Agent 입력은 제한되어야 한다.

```text
Current portfolio state
Reconciled cash/debt/tax reserve
Structured research packet
Macro regime summary
Risk Engine pre-check envelope
Relevant thesis memory
Last decision and outcome summary
```

매주 전체 원문을 다시 읽지 않는다.  
매주 보는 것은 변화분이다.

```text
가격 변화
thesis-relevant news
earnings/event update
macro regime change
correlation spike
cash/ledger change
risk rule breach
```

---

## Model QA의 원칙

모델은 신뢰하지 않는다.  
프롬프트도 신뢰하지 않는다.  
출력도 QA 전에는 신뢰하지 않는다.

관리 대상:

```text
Research Agent prompt
Senior Agent prompt
Trading Agent prompt
output schema
model version
eval results
canary test results
```

---

## Optional Broker Integration의 원칙

Broker API는 자동 실행을 위한 것이 아니다.

이 단계에서도 우선순위는 다음이다.

```text
read-only account snapshot import
input friction reduction
reconciliation support
```

자동 주문은 여전히 기본 제외다.

---

## 성공 기준 (Definition of Done)

이 단계가 끝났다고 판단할 수 있는 기준은 다음이다.

1. Research/Senior/Trading 프롬프트 변경 시 QA 없이 실사용되지 않는다.
2. 모델이나 프롬프트가 바뀌어도 canary 또는 golden test로 regression을 조기에 잡는다.
3. 매주 전체 원문을 LLM에 넣지 않고 변화분 중심으로 review한다.
4. Senior Agent 입력은 제한된 structured context로 유지된다.
5. token budget이 폭발하지 않는다.
6. thesis memory와 decision memory가 장기 운영에 도움을 준다.
7. Broker 연동은 자동 주문이 아니라 read-only 입력 마찰 감소 수준에서만 검토된다.
8. Stage 1~2의 실사용 루프가 무너지지 않은 상태에서만 이 단계가 의미를 가진다.

---

## 이 단계에서 중요한 설계 판단

Model QA, RAG, Context Economy는 멋있지만 초반 기능이 아니다.

이것들은 Research Agent와 Senior Agent가 반복적으로 쓰이고, 실제 운영 볼륨이 생긴 뒤에 가치가 생긴다.

```text
운영 루프가 없으면 Governance도 없다.
반복 사용이 없으면 Model QA도 없다.
기억할 결정이 없으면 Decision Memory도 없다.
```

---

## 이 단계에서 절대 하지 말 것

- Stage 1~2가 안정되기 전에 RAG부터 만들기
- full document ingestion을 기본값으로 두기
- 모든 문제를 model router로 해결하려 하기
- broker write API를 성급히 붙이기
- Telegram 고도화를 핵심 시스템으로 착각하기
- QA 없는 prompt/model 변경 후 실사용하기

이 단계의 질문은 단 하나다.

```text
이미 작동하는 Portfolio OS가 장기적으로 무너지지 않게 운영 가능한가?
```

---

# 3. 최종 개발 우선순위

Portfolio OS의 개발 우선순위는 다음 순서로 고정한다.

```text
1. Ledger가 맞는가?
2. 실제 계좌와 대조되는가?
3. Risk Engine 없이 주문이 나가지 않는가?
4. 인간 거래가 ticket 또는 override로 기록되는가?
5. Macro가 Senior보다 먼저 포트폴리오 전체 위험을 보는가?
6. Research는 추천하지 않고 사실과 반대 논리를 제공하는가?
7. Senior는 판단하되 계산하지 않는가?
8. Model QA와 Context Economy는 실제 운영 루프 이후에 붙는가?
9. Broker API는 자동 실행이 아니라 입력 마찰 감소에만 쓰이는가?
```

---

# 4. Stage 간 의존 관계

```text
Stage 1 없이는 Stage 2 불가
Stage 2 없이는 Stage 3의 실사용 가치 낮음
Stage 3 없이는 Stage 4의 Senior Agent가 불완전함
Stage 4가 반복 사용되기 전에는 Stage 5의 Model QA/RAG가 과설계임
```

더 압축하면:

```text
Ledger → Reconciliation → Risk/Ticket/Override → Research/Macro → Senior → Governance
```

---

# 5. 이 로드맵의 핵심 판정

이 프로젝트의 성공 여부는 AI Agent의 지능보다 다음에 달려 있다.

```text
하나의 포트폴리오 상태를 모든 모듈이 동일하게 이해하는가?
실제 계좌와 장부가 계속 맞는가?
Risk Engine이 Senior Agent보다 강한 권한을 가지는가?
인간의 우회 거래가 시스템 밖으로 사라지지 않고 기록되는가?
Macro Layer가 개별 종목 확신을 견제하는가?
```

따라서 이 프로젝트는 “AI 투자 비서”로 시작하면 실패할 가능성이 높다.

올바른 시작점은 다음이다.

```text
정확한 장부
실제 계좌 대조
수동 주문 티켓
리스크 검증
오버라이드 기록
결정 저널
```

그 다음에야 Research, Macro, Senior, Model QA를 올릴 가치가 있다.

---

# 6. 최종 한 문장

Portfolio OS는 시장을 맞히는 시스템이 아니다.

```text
공격적인 장기 투자자가 자신의 확신, 감정, 편향, 장부 오류, 계산 실수, 과매매 충동, 세금 문제, 유동성 리스크, AI 환각을 하나의 운영체계 안에서 통제하면서 더 나은 의사결정을 반복하도록 만드는 시스템이다.
```

그러므로 최종 로드맵의 중심은 이것이다.

```text
Ledger first.
Risk gated.
Macro before Senior.
Human approved.
Override declared.
AI assisted, never AI executed.
```
