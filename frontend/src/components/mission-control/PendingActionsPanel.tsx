import { ClipboardCheck, FilePlus2, RefreshCw, ScrollText, TriangleAlert } from "lucide-react";
import { Link } from "react-router-dom";
import type { PostmortemTaskListResponse } from "../../api/types";

export function PendingActionsPanel({ postmortems }: { postmortems?: PostmortemTaskListResponse }) {
  const postmortemCount = postmortems?.count ?? 0;
  return (
    <section className="panel pending-actions">
      <div className="panel__header"><div><p className="eyebrow">PENDING ACTIONS</p><h2>빠른 작업</h2></div></div>
      <div className="action-stack">
        <button disabled title="Stage 3에서 구현"><RefreshCw aria-hidden="true" />정산 실행<span>Stage 3</span></button>
        <Link to="/risk"><FilePlus2 aria-hidden="true" />의도 생성<span>Risk Workspace</span></Link>
        <Link to="/tickets"><ClipboardCheck aria-hidden="true" />주문 티켓 검토<span>조회 / 승인</span></Link>
        <Link to="/executions"><ScrollText aria-hidden="true" />실행 기록 확인<span>정산 확정 대기</span></Link>
        <Link to="/overrides"><TriangleAlert aria-hidden="true" />오버라이드 선언<span>예외 감사 기록</span></Link>
        <Link to="/postmortems"><ScrollText aria-hidden="true" />복기 태스크<span>{postmortemCount} scheduled</span></Link>
      </div>
    </section>
  );
}
