import { Circle } from "lucide-react";
import type { StatusTone } from "../../lib/statusMap";

interface StatusBadgeProps { label: string; tone?: StatusTone; title?: string }

export function StatusBadge({ label, tone = "gray", title }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`} title={title}><Circle aria-hidden="true" size={8} fill="currentColor" />{label}</span>;
}
