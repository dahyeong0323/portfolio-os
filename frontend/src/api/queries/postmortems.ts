import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { PostmortemTaskListResponse } from "../types";

export function usePostmortemTasks(params: Record<string, string | number | null | undefined> = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== "") search.set(key, String(value));
  });
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return useQuery({
    queryKey: ["postmortems", params],
    queryFn: () => apiGet<PostmortemTaskListResponse>(`/api/v1/postmortems${suffix}`, "postmortems"),
    refetchInterval: 60_000,
  });
}
