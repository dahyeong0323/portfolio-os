import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import type { StatusTone } from "../../lib/statusMap";

interface AuthorityCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  detail: string;
  tone: StatusTone;
  to?: string;
}

export function AuthorityCard({ icon: Icon, label, value, detail, tone, to }: AuthorityCardProps) {
  const content = (
    <article className={`authority-card authority-card--${tone}`}>
      <div className="authority-card__icon"><Icon aria-hidden="true" size={24} /></div>
      <div><p className="eyebrow">{label}</p><strong>{value}</strong><span>{detail}</span></div>
    </article>
  );

  if (to) {
    return (
      <Link className="authority-card-link" to={to}>
        {content}
      </Link>
    );
  }

  return content;
}
