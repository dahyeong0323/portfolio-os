import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type {
  GovernanceEventListResponse,
  GovernanceOverviewResponse,
  MacroDetailResponse,
  MacroListResponse,
  ResearchDetailResponse,
  ResearchListResponse,
  SeniorMemoDetailResponse,
  SeniorMemoListResponse,
} from "../types";

export function useResearchItems() {
  return useQuery({
    queryKey: ["context-explorer", "research"],
    queryFn: () => apiGet<ResearchListResponse>("/api/v1/research", "researchItems"),
    refetchInterval: 30_000,
  });
}

export function useResearchDetail(researchId: number | string | null) {
  return useQuery({
    queryKey: ["context-explorer", "research", researchId],
    queryFn: () => apiGet<ResearchDetailResponse>(`/api/v1/research/${encodeURIComponent(String(researchId ?? ""))}`, "researchDetail"),
    enabled: researchId != null && researchId !== "",
  });
}

export function useMacroItems() {
  return useQuery({
    queryKey: ["context-explorer", "macro"],
    queryFn: () => apiGet<MacroListResponse>("/api/v1/macro", "macroItems"),
    refetchInterval: 30_000,
  });
}

export function useMacroDetail(macroId: number | string | null) {
  return useQuery({
    queryKey: ["context-explorer", "macro", macroId],
    queryFn: () => apiGet<MacroDetailResponse>(`/api/v1/macro/${encodeURIComponent(String(macroId ?? ""))}`, "macroDetail"),
    enabled: macroId != null && macroId !== "",
  });
}

export function useSeniorMemos() {
  return useQuery({
    queryKey: ["context-explorer", "senior-memos"],
    queryFn: () => apiGet<SeniorMemoListResponse>("/api/v1/senior-memos", "seniorMemos"),
    refetchInterval: 30_000,
  });
}

export function useSeniorMemoDetail(memoId: number | string | null) {
  return useQuery({
    queryKey: ["context-explorer", "senior-memos", memoId],
    queryFn: () => apiGet<SeniorMemoDetailResponse>(`/api/v1/senior-memos/${encodeURIComponent(String(memoId ?? ""))}`, "seniorMemoDetail"),
    enabled: memoId != null && memoId !== "",
  });
}

export function useGovernanceOverview() {
  return useQuery({
    queryKey: ["context-explorer", "governance"],
    queryFn: () => apiGet<GovernanceOverviewResponse>("/api/v1/governance", "governanceOverview"),
    refetchInterval: 30_000,
  });
}

export function useGovernanceEvents() {
  return useQuery({
    queryKey: ["context-explorer", "governance", "events"],
    queryFn: () => apiGet<GovernanceEventListResponse>("/api/v1/governance/events", "governanceEvents"),
    refetchInterval: 30_000,
  });
}
