import { z } from "zod";
export const FormalizationTicket = z.object({
    id: z.string(),
    pk: z.string(),
    hearout_id: z.string(),
    weight_a: z.number(),
    weight_b: z.number(),
    weight_c: z.number(),
    weight_final: z.number(),
    tj_verdict: z.enum(["supported", "novel", "conflict"]).nullable().optional(),
    status: z.enum([
        "pending_review",
        "in_review",
        "approved",
        "rejected",
        "expired",
        "conflict_pending",
    ]),
    locked_by: z.string().nullable().optional(),
    lock_expires_at: z.string().nullable().optional(),
    reviewer_id: z.string().nullable().optional(),
    created_at: z.string(),
});
