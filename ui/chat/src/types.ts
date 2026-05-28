import { z } from "zod";

export const CitationRef = z.object({
  record_id: z.string(),
  schema_field_id: z.string(),
  weight: z.number(),
  superseded_by: z.string().nullable().optional(),
});
export type CitationRef = z.infer<typeof CitationRef>;

export const SchemaUpdateBanner = z.object({
  unseen_revision_ids: z.array(z.number()),
  changed_fields_summary: z.string(),
  history_url: z.string(),
});
export type SchemaUpdateBanner = z.infer<typeof SchemaUpdateBanner>;

export const TurnResponse = z.object({
  turn_id: z.string(),
  ai_response: z.string(),
  self_critic_score: z.number(),
  citations: z.array(CitationRef),
  schema_update_banner: SchemaUpdateBanner.nullable().optional(),
  gap_detected: z.boolean(),
  gap_event_id: z.string().nullable().optional(),
});
export type TurnResponse = z.infer<typeof TurnResponse>;

export const RetrieveResponse = z.object({
  records: z.array(CitationRef),
  conflicts: z.array(
    z.object({ schema_field_id: z.string(), alt_count: z.number() }),
  ),
});
export type RetrieveResponse = z.infer<typeof RetrieveResponse>;

export const CitationDetail = z.object({
  record_id: z.string(),
  content: z.string(),
  schema_field_id: z.string(),
  superseded_by: z.string().nullable().optional(),
  superseded_banner: z.string().nullable().optional(),
});
export type CitationDetail = z.infer<typeof CitationDetail>;

export const HearoutTurn = z.object({
  session_id: z.string(),
  status: z.enum(["in_progress", "completed", "skipped", "expired"]),
  next_question: z.string().nullable().optional(),
  final_record: z.unknown().nullable().optional(),
  turn_count: z.number(),
});
export type HearoutTurn = z.infer<typeof HearoutTurn>;

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  turnId?: string;
  citations?: CitationRef[];
  selfCriticScore?: number;
}

export interface TenantCtx {
  user_id: string;
  sector: string;
  unit: string;
  session_id: string;
}
