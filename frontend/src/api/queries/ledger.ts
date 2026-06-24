import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { LedgerSnapshotResponse, LedgerStatusResponse } from "../types";

export function useLedgerStatusQuery() {
  return useQuery({ queryKey: ["ledger", "status"], queryFn: () => apiGet<LedgerStatusResponse>("/api/v1/ledger/status", "ledgerStatus"), refetchInterval: 15_000 });
}

export function useLedgerSnapshotQuery() {
  return useQuery({ queryKey: ["ledger", "snapshot"], queryFn: () => apiGet<LedgerSnapshotResponse>("/api/v1/ledger/snapshot", "ledgerSnapshot"), refetchInterval: 15_000 });
}
