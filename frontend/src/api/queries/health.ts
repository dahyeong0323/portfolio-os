import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { HealthResponse } from "../types";

export const healthQueryKey = ["health"] as const;
export function useHealthQuery() {
  return useQuery({ queryKey: healthQueryKey, queryFn: () => apiGet<HealthResponse>("/api/v1/health", "health"), refetchInterval: 10_000 });
}
