import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../client";
import type { ReportCategoryListResponse, ReportDetailResponse, ReportFormat, ReportListResponse } from "../types";

interface ReportListParams {
  category?: string | null;
  format?: ReportFormat | null;
  limit?: number;
  offset?: number;
}

export function useReportCategories() {
  return useQuery({
    queryKey: ["reports", "categories"],
    queryFn: () => apiGet<ReportCategoryListResponse>("/api/v1/reports/categories", "reportCategories"),
    refetchInterval: 30_000,
  });
}

export function useReports(params: ReportListParams = {}) {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.format) search.set("format", params.format);
  if (params.limit != null) search.set("limit", String(params.limit));
  if (params.offset != null) search.set("offset", String(params.offset));
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return useQuery({
    queryKey: ["reports", params],
    queryFn: () => apiGet<ReportListResponse>(`/api/v1/reports${suffix}`, "reports"),
    refetchInterval: 30_000,
  });
}

export function useReportByReference(reportReference: string | null) {
  return useQuery({
    queryKey: ["reports", reportReference],
    queryFn: () => apiGet<ReportDetailResponse>(`/api/v1/reports/${encodeURIComponent(reportReference ?? "")}`, "reportDetail"),
    enabled: Boolean(reportReference),
  });
}

export function reportDownloadUrl(reportReference: string): string {
  return `/api/v1/reports/${encodeURIComponent(reportReference)}/download`;
}

export function useReportDownload(reportReference: string | null) {
  return {
    href: reportReference ? reportDownloadUrl(reportReference) : null,
    available: Boolean(reportReference),
  };
}
