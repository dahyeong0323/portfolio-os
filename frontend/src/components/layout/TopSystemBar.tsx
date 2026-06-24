import { Menu, RadioTower } from "lucide-react";
import { useEffect, useState } from "react";
import { useHealthQuery } from "../../api/queries/health";
import { useLedgerStatusQuery } from "../../api/queries/ledger";
import { formatDateTime } from "../../lib/format";
import { ledgerStatusMap } from "../../lib/statusMap";
import { StatusBadge } from "../status/StatusBadge";

export function TopSystemBar({ onMenu }: { onMenu: () => void }) {
  const [now, setNow] = useState(() => new Date());
  const health = useHealthQuery();
  const ledger = useLedgerStatusQuery();
  useEffect(() => { const timer = window.setInterval(() => setNow(new Date()), 1000); return () => window.clearInterval(timer); }, []);
  const ledgerDef = ledger.data ? ledgerStatusMap[ledger.data.ledger_status] : null;
  return (
    <header className="top-system-bar">
      <button className="icon-button mobile-menu" onClick={onMenu} aria-label="메뉴 열기"><Menu /></button>
      <div className="system-cell system-cell--clock"><span>시스템 시간</span><strong>{new Intl.DateTimeFormat("ko-KR", { dateStyle: "short", timeStyle: "medium" }).format(now)}</strong></div>
      <div className="system-cell"><span>API 연결</span><StatusBadge label={health.data?.database_ready ? "ONLINE" : health.isLoading ? "CONNECTING" : "DEGRADED"} tone={health.data?.database_ready ? "green" : health.isLoading ? "cyan" : "red"} /></div>
      <div className="system-cell system-cell--wide"><span>마지막 정산</span><strong>{formatDateTime(ledger.data?.last_reconciled_at)}</strong></div>
      <div className="system-cell"><span>레저 상태</span>{ledgerDef ? <StatusBadge label={ledgerDef.label} tone={ledgerDef.tone} /> : <RadioTower className="muted" size={18} />}</div>
    </header>
  );
}
