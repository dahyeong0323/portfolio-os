import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPostForm, apiPostJson } from "../client";
import type {
  ExternalSnapshotImportResponse,
  LatestReconciliationResponse,
  ReconciliationReportResponse,
  ReconciliationSnapshot,
  RunReconciliationRequest,
  RunReconciliationResponse,
} from "../types";

export function useReconciliationQuery() {
  return useQuery({ queryKey: ["reconciliation", "latest"], queryFn: () => apiGet<LatestReconciliationResponse>("/api/v1/reconciliations/latest", "reconciliation"), refetchInterval: 30_000 });
}

export function useReconciliationById(reconciliationId: number | null) {
  return useQuery({
    queryKey: ["reconciliation", reconciliationId],
    queryFn: () => apiGet<ReconciliationSnapshot>(`/api/v1/reconciliations/${reconciliationId}`, "reconciliationById"),
    enabled: reconciliationId !== null,
  });
}

export function useReconciliationReport(reconciliationId: number | null, enabled: boolean) {
  return useQuery({
    queryKey: ["reconciliation", reconciliationId, "report"],
    queryFn: () => apiGet<ReconciliationReportResponse>(`/api/v1/reconciliations/${reconciliationId}/report`, "reconciliationReport"),
    enabled: reconciliationId !== null && enabled,
    retry: false,
  });
}

export function useImportExternalSnapshot() {
  return useMutation({
    mutationFn: (formData: FormData) => apiPostForm<ExternalSnapshotImportResponse>("/api/v1/snapshots/external-imports", formData),
  });
}

export function useRunReconciliation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RunReconciliationRequest) => apiPostJson<RunReconciliationResponse, RunReconciliationRequest>("/api/v1/reconciliations", payload),
    onSuccess: async (result) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reconciliation", "latest"] }),
        queryClient.invalidateQueries({ queryKey: ["reconciliation", result.reconciliation_id] }),
        queryClient.invalidateQueries({ queryKey: ["ledger"] }),
      ]);
    },
  });
}
