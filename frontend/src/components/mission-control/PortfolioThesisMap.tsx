import { Orbit } from "lucide-react";
import type { LedgerPosition } from "../../api/types";
import { formatDecimal, formatMoney } from "../../lib/format";

export function PortfolioThesisMap({ positions }: { positions: LedgerPosition[] }) {
  const visible = positions.slice(0, 6);
  return (
    <section className="panel thesis-map dashboard-thesis" aria-labelledby="thesis-title">
      <div className="panel__header"><div><p className="eyebrow">STRATEGY STRUCTURE</p><h2 id="thesis-title">포트폴리오 전략 지도</h2></div><span className="read-only-tag">READ ONLY</span></div>
      {visible.length === 0 ? <div className="empty-state empty-state--large"><Orbit aria-hidden="true" /><strong>표시할 포지션이 없습니다</strong><p>레저 스냅샷에 포지션이 생기면 전략 노드가 여기에 표시됩니다.</p></div> :
        <div className={`thesis-network thesis-network--${visible.length}`}>
          <div className="thesis-core"><Orbit aria-hidden="true" /><strong>PORTFOLIO</strong><span>{visible.length} ACTIVE NODES</span></div>
          {visible.map((position, index) => <article className={`thesis-node thesis-node--${index + 1}`} key={`${position.account_id}-${position.instrument_id}`}>
            <span className="thesis-node__index">0{index + 1}</span><strong>{position.symbol}</strong><span>{formatDecimal(position.quantity)} units</span><small>{position.average_cost ? `평균원가 ${formatMoney(position.average_cost, position.currency)}` : "평균원가 없음"}</small>
          </article>)}
        </div>}
      {positions.length > 6 && <p className="panel__note">상위 6개 노드만 표시 중 · 총 {positions.length}개 포지션</p>}
    </section>
  );
}
