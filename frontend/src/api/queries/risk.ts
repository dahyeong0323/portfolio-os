import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { RiskValidationDetailResponse } from "../types";

export function useRiskValidationById(riskValidationId: number | null) {
  return useQuery({
    queryKey: ["risk-validations", riskValidationId],
    queryFn: () => apiGet<RiskValidationDetailResponse>(`/api/v1/risk/validations/${riskValidationId}`, "riskValidation"),
    enabled: riskValidationId != null,
    refetchInterval: 15_000,
  });
}
