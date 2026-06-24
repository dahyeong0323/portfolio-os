import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPostJson } from "../client";
import type { CreateTicketRequest, CreateTicketResponse, OrderTicketDetailResponse, OrderTicketListResponse, TicketActionResponse, TicketDecisionRequest } from "../types";

export function useTicketsQuery() {
  return useQuery({ queryKey: ["tickets"], queryFn: () => apiGet<OrderTicketListResponse>("/api/v1/tickets", "tickets"), refetchInterval: 15_000 });
}

export function useTicketById(ticketId: number | null) {
  return useQuery({
    queryKey: ["tickets", ticketId],
    queryFn: () => apiGet<OrderTicketDetailResponse>(`/api/v1/tickets/${ticketId}`, "ticketDetail"),
    enabled: ticketId != null,
    refetchInterval: 15_000,
  });
}

export function useCreateTicketFromValidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateTicketRequest) => apiPostJson<CreateTicketResponse, CreateTicketRequest>("/api/v1/tickets", payload),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["tickets"] });
      await queryClient.invalidateQueries({ queryKey: ["tickets", data.ticket.order_ticket_id] });
    },
  });
}

export function useApproveTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ticketId, payload }: { ticketId: number; payload: TicketDecisionRequest }) =>
      apiPostJson<TicketActionResponse, TicketDecisionRequest>(`/api/v1/tickets/${ticketId}/approve`, payload),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["tickets"] });
      await queryClient.invalidateQueries({ queryKey: ["tickets", data.ticket_id] });
    },
  });
}

export function useRejectTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ticketId, payload }: { ticketId: number; payload: TicketDecisionRequest }) =>
      apiPostJson<TicketActionResponse, TicketDecisionRequest>(`/api/v1/tickets/${ticketId}/reject`, payload),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["tickets"] });
      await queryClient.invalidateQueries({ queryKey: ["tickets", data.ticket_id] });
    },
  });
}
