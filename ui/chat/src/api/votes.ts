import { z } from "zod";
import { api } from "./client";

export const VoteResponseSchema = z.object({
  record_id: z.string(),
  upvotes: z.number(),
  downvotes: z.number(),
  score: z.number(),
});
export type VoteResponse = z.infer<typeof VoteResponseSchema>;

export const RankingEntrySchema = z.object({
  record_id: z.string(),
  schema_field_id: z.string(),
  content: z.string(),
  upvotes: z.number(),
  downvotes: z.number(),
  score: z.number(),
});
export type RankingEntry = z.infer<typeof RankingEntrySchema>;

export const RankingResponseSchema = z.object({
  entries: z.array(RankingEntrySchema),
});
export type RankingResponse = z.infer<typeof RankingResponseSchema>;

export async function castVote(
  recordId: string,
  direction: "up" | "down",
): Promise<VoteResponse> {
  const r = await api.post(`/records/${encodeURIComponent(recordId)}/vote`, {
    direction,
  });
  return VoteResponseSchema.parse(r.data);
}

export const RecordDetailSchema = z.object({
  record_id: z.string(),
  schema_field_id: z.string(),
  content: z.string(),
  atomic_claims: z.array(z.string()),
  upvotes: z.number(),
  downvotes: z.number(),
  score: z.number(),
  referenced_count: z.number(),
  superseded_by: z.string().nullable().optional(),
});
export type RecordDetail = z.infer<typeof RecordDetailSchema>;

export async function getRecord(recordId: string): Promise<RecordDetail> {
  const r = await api.get(`/records/${encodeURIComponent(recordId)}`);
  return RecordDetailSchema.parse(r.data);
}

export async function getRanking(
  sector: string,
  unit: string,
  limit: number = 20,
): Promise<RankingResponse> {
  const r = await api.get("/ranking", { params: { sector, unit, limit } });
  return RankingResponseSchema.parse(r.data);
}
