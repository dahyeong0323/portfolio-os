import { AlertTriangle, Home, RotateCw } from "lucide-react";
import { Link, useRouteError } from "react-router-dom";
import { errorMessage } from "../../lib/guards";

export function RouteErrorPage() {
  const error = useRouteError();
  return (
    <div className="page route-error-page">
      <section className="panel empty-state empty-state--large route-fallback">
        <AlertTriangle aria-hidden="true" />
        <span>ROUTE ERROR</span>
        <h1>화면을 렌더링하지 못했습니다.</h1>
        <p>{errorMessage(error)}</p>
        <p>실제 API 오류는 숨기지 않습니다. mock fallback은 네트워크 실패일 때만 샘플 데이터로 표시됩니다.</p>
        <div className="route-fallback-actions">
          <button className="primary-action" type="button" onClick={() => window.location.reload()}><RotateCw aria-hidden="true" />Reload</button>
          <Link className="secondary-action" to="/"><Home aria-hidden="true" />Dashboard</Link>
        </div>
      </section>
    </div>
  );
}
