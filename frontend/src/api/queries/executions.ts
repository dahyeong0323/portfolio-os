import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPostJson } from "../client";
import type { ConfirmExecutionsRequest, ConfirmExecutionsResponse, LogManualExecutionRequest, ManualExecutionResponse, PendingExecutionListResponse } from "../types";

export function useExecutionsQuery() {
  return useQuery({ queryKey: ["executions", "pending"], queryFn: () => apiGet<PendingExecutionListResponse>("/api/v1/executions/pending", "executions"), refetchInterval: 15_000 });
}

export function useExecutionById(executionId: number | null) {
  return useQuery({
    queryKey: ["executions", executionId],
    queryFn: () => apiGet<ManualExecutionResponse>(`/api/v1/executions/${executionId}`, "executionDetail"),
    enabled: executionId != null,
    refetchInterval: 15_000,
  });
}

export function useLogManualExecution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LogManualExecutionRequest) =>
      apiPostJson<ManualExecutionResponse, LogManualExecutionRequest>("/api/v1/executions", payload),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["executions", "pending"] });
      await queryClient.invalidateQueries({ queryKey: ["executions", data.execution_id] });
      if (data.linked_ticket_id != null) {
        await queryClient.invalidateQueries({ queryKey: ["tickets"] });
        await queryClient.invalidateQueries({ queryKey: ["tickets", data.linked_ticket_id] });
      }
    },
  });
}

export function useConfirmExecutionsAfterReconciliation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ConfirmExecutionsRequest) =>
      apiPostJson<ConfirmExecutionsResponse, ConfirmExecutionsRequest>("/api/v1/executions/confirm-after-reconciliation", payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["executions"] }),
        queryClient.invalidateQueries({ queryKey: ["tickets"] }),
        queryClient.invalidateQueries({ queryKey: ["ledger"] }),
        queryClient.invalidateQueries({ queryKey: ["reconciliation"] }),
      ]);
    },
  });
}
