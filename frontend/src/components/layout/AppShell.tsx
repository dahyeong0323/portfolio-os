import { AlertTriangle, RotateCw } from "lucide-react";
import { useState, useSyncExternalStore } from "react";
import { Outlet } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { apiRuntime } from "../../api/client";
import { Sidebar } from "./Sidebar";
import { TopSystemBar } from "./TopSystemBar";

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const runtime = useSyncExternalStore(apiRuntime.subscribe, apiRuntime.getSnapshot, apiRuntime.getSnapshot);
  const queryClient = useQueryClient();
  const retry = async () => { apiRuntime.retryLive(); await queryClient.invalidateQueries(); };
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">본문으로 건너뛰기</a>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="app-shell__main">
        <TopSystemBar onMenu={() => setSidebarOpen(true)} />
        {runtime.source === "mock" && <div className="mode-banner" role="status"><AlertTriangle aria-hidden="true" /><strong>MOCK MODE · 샘플 데이터</strong><span>{runtime.reason ?? "명시적 mock 모드"} · 실제 포트폴리오 상태가 아닙니다.</span><button onClick={retry}><RotateCw aria-hidden="true" />재연결 시도</button></div>}
        <main id="main-content" tabIndex={-1}><Outlet /></main>
      </div>
    </div>
  );
}
