import { Compass, Home, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="page not-found-page">
      <section className="panel empty-state empty-state--large route-fallback">
        <Compass aria-hidden="true" />
        <span>404 ROUTE</span>
        <h1>요청한 Mission Control 화면을 찾을 수 없습니다.</h1>
        <p>라우트가 이동했거나 아직 제공되지 않는 화면입니다. 새 금융 권한은 이 fallback에서 열리지 않습니다.</p>
        <div className="route-fallback-actions">
          <Link className="primary-action" to="/"><Home aria-hidden="true" />Dashboard</Link>
          <Link className="secondary-action" to="/system"><ShieldCheck aria-hidden="true" />System boundaries</Link>
        </div>
      </section>
    </div>
  );
}
