import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { InstrumentListResponse } from "../types";

export function useInstrumentsQuery() {
  return useQuery({ queryKey: ["instruments"], queryFn: () => apiGet<InstrumentListResponse>("/api/v1/instruments", "instruments"), staleTime: 300_000 });
}
