import { api } from "./client";
import {
  FormalizationTicket,
  PriorityModeInfo,
  SelfApprovalInfo,
} from "../types";

export async function listReviews(
  priorityOnly = false,
  sector?: string,
  unit?: string,
): Promise<FormalizationTicket[]> {
  const { data } = await api.get("/reviews", {
    params: { priority_only: priorityOnly, sector, unit },
  });
  return (data as unknown[]).map((x) => FormalizationTicket.parse(x));
}

export async function listConflictReviews(
  sector?: string,
  unit?: string,
): Promise<FormalizationTicket[]> {
  const { data } = await api.get("/reviews/conflict", {
    params: { sector, unit },
  });
  return (data as unknown[]).map((x) => FormalizationTicket.parse(x));
}

export async function lockReview(
  id: string,
): Promise<{ locked_until: string }> {
  const { data } = await api.post(`/reviews/${encodeURIComponent(id)}/lock`);
  return data;
}

export async function unlockReview(id: string): Promise<void> {
  await api.post(`/reviews/${encodeURIComponent(id)}/unlock`);
}

export async function decideReview(
  id: string,
  sector: string,
  unit: string,
  decision: "approve" | "edit" | "reject",
): Promise<unknown> {
  const { data } = await api.post(
    `/reviews/${encodeURIComponent(id)}/decision`,
    { decision },
    { params: { sector, unit } },
  );
  return data;
}

export async function decideConflict(
  id: string,
  sector: string,
  unit: string,
  decision: "adopt_new" | "keep_existing" | "coexist",
): Promise<unknown> {
  const { data } = await api.post(
    `/reviews/${encodeURIComponent(id)}/conflict`,
    { decision },
    { params: { sector, unit } },
  );
  return data;
}

export async function getSelfApproval(): Promise<SelfApprovalInfo> {
  const { data } = await api.get<SelfApprovalInfo>("/reviews/self-approval");
  return data;
}

export async function getPriorityMode(): Promise<PriorityModeInfo> {
  const { data } = await api.get<PriorityModeInfo>("/reviews/priority-mode");
  return data;
}
