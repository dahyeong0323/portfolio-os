import type { DecimalString } from "../api/types";

export function formatDecimal(value: DecimalString | null | undefined, maximumFractionDigits = 6): string {
  if (value == null || value === "") return "-";
  const match = value.match(/^([+-]?)(\d+)(?:\.(\d+))?$/);
  if (!match) return value;
  const sign = match[1] ?? "";
  const integer = (match[2] ?? "0").replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const fraction = (match[3] ?? "").slice(0, maximumFractionDigits).replace(/0+$/, "");
  return `${sign}${integer}${fraction ? `.${fraction}` : ""}`;
}

export function formatMoney(value: DecimalString | null | undefined, currency: string): string {
  return `${formatDecimal(value, 2)} ${currency}`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "기록 없음";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(date);
}
