import type { LedgerStatus, ReconciliationStatus, RiskValidationStatus, TicketStatus } from "../api/types";

export type StatusTone = "green" | "amber" | "yellow" | "red" | "cyan" | "gray" | "violet";

export interface StatusDefinition {
  label: string;
  tone: StatusTone;
  description: string;
}

export const ledgerStatusMap: Record<LedgerStatus, StatusDefinition> = {
  reconciled: { label: "정상", tone: "green", description: "정산 완료" },
  provisional: { label: "미확정", tone: "amber", description: "정산 전 입력 존재" },
  stale: { label: "오래됨", tone: "yellow", description: "정산 데이터 갱신 필요" },
  broken: { label: "불일치", tone: "red", description: "정산 차이 확인 필요" },
};

export const reconciliationStatusMap: Record<ReconciliationStatus | "none", StatusDefinition> = {
  passed: { label: "통과", tone: "green", description: "허용 범위 내 정산" },
  failed: { label: "실패", tone: "red", description: "허용 오차 초과" },
  needs_review: { label: "검토 필요", tone: "amber", description: "수동 검토 필요" },
  none: { label: "기록 없음", tone: "gray", description: "아직 정산 기록 없음" },
};

export const riskValidationStatusMap: Record<RiskValidationStatus, StatusDefinition> = {
  passed: { label: "통과", tone: "green", description: "Risk Engine 검증 통과" },
  adjusted: { label: "조정됨", tone: "amber", description: "허용 수량 또는 금액 조정" },
  rejected: { label: "거절", tone: "red", description: "공식 티켓 생성 불가" },
};

export const ticketStatusMap: Record<TicketStatus, StatusDefinition> = {
  validated: { label: "검증됨", tone: "cyan", description: "사람 승인 또는 거절 대기" },
  approved: { label: "승인됨", tone: "green", description: "사람 승인 기록 존재" },
  rejected: { label: "거절됨", tone: "red", description: "사람이 거절한 티켓" },
  modified: { label: "수정됨", tone: "violet", description: "수정 후 재검증 필요" },
  expired: { label: "만료됨", tone: "gray", description: "유효 기간 종료" },
  executed_provisional: { label: "실행 기록됨", tone: "amber", description: "수동 실행 기록 후 정산 대기" },
  reconciled: { label: "정산 완료", tone: "green", description: "실행까지 정산 완료" },
  broken: { label: "불일치", tone: "red", description: "실행 또는 정산 문제" },
  cancelled: { label: "취소됨", tone: "gray", description: "취소된 티켓" },
};
