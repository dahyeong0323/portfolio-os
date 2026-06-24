import type { ApiClientError } from "../api/client";
import type { OrderTicket } from "../api/types";

export function isOpenTicket(ticket: OrderTicket): boolean {
  return ticket.status === "validated" || ticket.status === "approved";
}

export function errorMessage(error: unknown): string {
  if (error && typeof error === "object" && "message" in error) return String((error as ApiClientError).message);
  return "데이터를 불러오는 중 알 수 없는 오류가 발생했습니다.";
}
