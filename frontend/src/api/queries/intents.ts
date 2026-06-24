import { useMutation } from "@tanstack/react-query";
import { apiPostJson } from "../client";
import type { CreateIntentRequest, CreateIntentResponse, ValidateIntentRequest, ValidateIntentResponse } from "../types";

export function useCreateIntent() {
  return useMutation({
    mutationFn: (payload: CreateIntentRequest) => apiPostJson<CreateIntentResponse, CreateIntentRequest>("/api/v1/intents", payload),
  });
}

export function useValidateIntent() {
  return useMutation({
    mutationFn: ({ intentId, payload }: { intentId: number; payload: ValidateIntentRequest }) =>
      apiPostJson<ValidateIntentResponse, ValidateIntentRequest>(`/api/v1/intents/${intentId}/validate`, payload),
  });
}
