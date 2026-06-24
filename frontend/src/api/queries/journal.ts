import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { DecisionJournalEntry, DecisionJournalListResponse } from "../types";

export function useJournalEntries(params: Record<string, string | number | null | undefined> = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== "") search.set(key, String(value));
  });
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return useQuery({
    queryKey: ["journal", params],
    queryFn: () => apiGet<DecisionJournalListResponse>(`/api/v1/journal${suffix}`, "journal"),
    refetchInterval: 30_000,
  });
}

export function useJournalEntryById(journalId: number | null) {
  return useQuery({
    queryKey: ["journal", journalId],
    queryFn: () => apiGet<DecisionJournalEntry>(`/api/v1/journal/${journalId}`, "journalDetail"),
    enabled: journalId != null,
  });
}
