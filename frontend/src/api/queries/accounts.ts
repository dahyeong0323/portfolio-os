import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { AccountListResponse } from "../types";

export function useAccountsQuery() {
  return useQuery({ queryKey: ["accounts"], queryFn: () => apiGet<AccountListResponse>("/api/v1/accounts", "accounts"), staleTime: 300_000 });
}
