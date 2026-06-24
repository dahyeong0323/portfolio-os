import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPostJson } from "../client";
import type { DeclareOverrideRequest, OverrideActionRequest, OverrideListResponse, OverrideResponse } from "../types";

export function useOverrides() {
  return useQuery({
    queryKey: ["overrides"],
    queryFn: () => apiGet<OverrideListResponse>("/api/v1/overrides", "overrides"),
    refetchInterval: 20_000,
  });
}

export function useOverrideById(overrideId: number | null) {
  return useQuery({
    queryKey: ["overrides", overrideId],
    queryFn: () => apiGet<OverrideResponse>(`/api/v1/overrides/${overrideId}`, "overrideDetail"),
    enabled: overrideId != null,
    refetchInterval: 20_000,
  });
}

export function useDeclareOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DeclareOverrideRequest) => apiPostJson<OverrideResponse, DeclareOverrideRequest>("/api/v1/overrides", payload),
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["overrides"] }),
        queryClient.invalidateQueries({ queryKey: ["overrides", data.override.override_id] }),
        queryClient.invalidateQueries({ queryKey: ["journal"] }),
        queryClient.invalidateQueries({ queryKey: ["postmortems"] }),
      ]);
    },
  });
}

export function useConfirmOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ overrideId, payload }: { overrideId: number; payload: OverrideActionRequest }) =>
      apiPostJson<OverrideResponse, OverrideActionRequest>(`/api/v1/overrides/${overrideId}/confirm`, payload),
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["overrides"] }),
        queryClient.invalidateQueries({ queryKey: ["overrides", data.override.override_id] }),
        queryClient.invalidateQueries({ queryKey: ["journal"] }),
      ]);
    },
  });
}

export function useCancelOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ overrideId, payload }: { overrideId: number; payload: OverrideActionRequest }) =>
      apiPostJson<OverrideResponse, OverrideActionRequest>(`/api/v1/overrides/${overrideId}/cancel`, payload),
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["overrides"] }),
        queryClient.invalidateQueries({ queryKey: ["overrides", data.override.override_id] }),
        queryClient.invalidateQueries({ queryKey: ["journal"] }),
      ]);
    },
  });
}
