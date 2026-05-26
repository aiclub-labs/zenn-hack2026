import { z } from "zod";
// Mirror app/contracts/common.py + cosmos.py (SchemaFieldDoc / SchemaAuditEntry).
export const ExpectedValueType = z.enum([
    "string",
    "number",
    "enum",
    "structured",
]);
export const ChangeType = z.enum([
    "create",
    "update",
    "deactivate",
    "reactivate",
]);
export const TenantSchema = z.object({
    sector: z.string().min(1),
    unit: z.string().min(1),
});
export const SchemaFieldDocSchema = z.object({
    id: z.string(),
    pk: z.string(),
    sector: z.string(),
    unit: z.string(),
    field_name: z.string(),
    description: z.string(),
    expected_value_type: ExpectedValueType,
    example: z.string(),
    ai_baseline_assumption: z.string(),
    is_active: z.boolean(),
    revision_id: z.number().int(),
    updated_at: z.string(),
    updated_by: z.string(),
});
export const SchemaAuditEntrySchema = z.object({
    id: z.string(),
    pk: z.string(),
    schema_field_id: z.string(),
    revision_id: z.number().int(),
    change_type: ChangeType,
    diff: z.record(z.string(), z.object({ before: z.unknown(), after: z.unknown() })),
    reason: z.string().nullable().optional(),
    changed_by: z.string(),
    changed_at: z.string(),
});
export const BulkImportRequestSchema = z.object({
    source_sector: z.string(),
    source_unit: z.string(),
    target_sector: z.string(),
    target_unit: z.string(),
});
