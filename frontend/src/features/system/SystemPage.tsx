import { Ban, Database, FileWarning, LockKeyhole, RadioTower, ShieldCheck, Terminal, Workflow } from "lucide-react";
import { useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import { apiRuntime } from "../../api/client";
import { useHealthQuery } from "../../api/queries/health";
import { StatusBadge } from "../../components/status/StatusBadge";
import { errorMessage } from "../../lib/guards";

const boundaries = [
  { icon: Ban, title: "No broker integration", detail: "프론트엔드는 브로커 쓰기 API나 주문 전송 기능을 제공하지 않습니다." },
  { icon: RadioTower, title: "No automatic trading", detail: "자동매매, 자동 승인, 자동 실행 흐름은 Stage 10에 추가되지 않았습니다." },
  { icon: Database, title: "No frontend SQLite access", detail: "React는 FastAPI를 통해서만 데이터를 읽고 SQLite 파일에 직접 접근하지 않습니다." },
  { icon: Terminal, title: "No CLI invocation", detail: "React 또는 API가 로컬 명령 출력에 의존하는 경로를 만들지 않았습니다." },
  { icon: ShieldCheck, title: "Risk Engine remains authority", detail: "공식 주문 티켓은 Stage 2 Risk Engine 경로를 유지합니다." },
  { icon: LockKeyhole, title: "Reconciliation remains boundary", detail: "수동 실행은 정산 증거를 통해서만 확정됩니다." },
  { icon: Workflow, title: "Override is an exception", detail: "오버라이드는 공식 risk validation이 아니라 선언된 예외 감사 기록입니다." },
  { icon: FileWarning, title: "Context is read-only", detail: "Research, macro, senior memo, governance는 판단 보조 컨텍스트입니다." },
];

export function SystemPage() {
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const health = useHealthQuery();
  return (
    <div className="page system-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">SYSTEM BOUNDARIES</p>
          <h1>Safety & Packaging Readiness</h1>
          <p>Portfolio OS Mission Control의 권한 경계와 로컬 앱 실행 상태를 읽기 전용으로 확인합니다.</p>
        </div>
        <span className="read-only-tag">READ ONLY</span>
      </header>

      {health.error ? <div className="inline-error" role="alert">{errorMessage(health.error)}</div> : null}

      <section className="panel system-status-panel">
        <div className="panel__header"><div><p className="eyebrow">RUNTIME</p><h2>API source and readiness</h2></div><StatusBadge label={runtime.source === "mock" ? "MOCK" : "LIVE"} tone={runtime.source === "mock" ? "amber" : "green"} /></div>
        <dl className="detail-list">
          <div><dt>Source</dt><dd>{runtime.source === "mock" ? "Mock fallback sample data" : "Live FastAPI"}</dd></div>
          <div><dt>Reason</dt><dd>{runtime.reason ?? "-"}</dd></div>
          <div><dt>Database ready</dt><dd>{health.data?.database_ready ? "yes" : "unknown / unavailable"}</dd></div>
          <div><dt>App mode</dt><dd>{health.data?.app_mode ?? "-"}</dd></div>
          <div><dt>Backend helper</dt><dd><code>python -m uvicorn portfolio_os.api.app:app --host 127.0.0.1 --port 8000</code></dd></div>
        </dl>
      </section>

      <section className="system-boundary-grid" aria-label="System safety boundaries">
        {boundaries.map(({ icon: Icon, title, detail }) => (
          <article className="panel boundary-card" key={title}>
            <Icon aria-hidden="true" />
            <div><h2>{title}</h2><p>{detail}</p></div>
          </article>
        ))}
      </section>

      <section className="panel read-only-notice">
        <strong>Desktop packaging readiness</strong>
        <p>현재 Stage 10은 Tauri를 설치하거나 native 권한을 추가하지 않습니다. 패키징은 별도 단계에서 shell plugin, arbitrary filesystem access, broker credential storage 없이 local FastAPI 통신만 허용하는 방식으로 진행해야 합니다.</p>
        <p><Link className="table-link" to="/reports">Reports Center</Link>와 <Link className="table-link" to="/governance">Governance Context</Link>는 동일한 읽기 전용 경계를 공유합니다.</p>
      </section>
    </div>
  );
}
