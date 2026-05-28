import { api } from "./client";
import {
  BulkImportRequest,
  SchemaAuditEntry,
  SchemaAuditEntrySchema,
  SchemaFieldDoc,
  SchemaFieldDocSchema,
} from "../types";
import { z } from "zod";

export async function createSchema(
  body: SchemaFieldDoc,
): Promise<SchemaFieldDoc> {
  const r = await api.post("/schemas", body);
  return SchemaFieldDocSchema.parse(r.data);
}

export async function updateSchema(
  id: string,
  body: SchemaFieldDoc,
): Promise<SchemaFieldDoc> {
  const r = await api.patch(`/schemas/${encodeURIComponent(id)}`, body);
  return SchemaFieldDocSchema.parse(r.data);
}

// Mirrors app.contracts.http.SetActiveRequest (M-8).
export interface SetActiveRequest {
  is_active: boolean;
  reason: string | null;
}

export async function setActive(
  id: string,
  pk: string,
  is_active: boolean,
  reason?: string,
): Promise<SchemaAuditEntry> {
  const body: SetActiveRequest = { is_active, reason: reason ?? null };
  const r = await api.post(`/schemas/${encodeURIComponent(id)}/active`, body, {
    params: { pk },
  });
  return SchemaAuditEntrySchema.parse(r.data);
}

export interface ListSchemasQuery {
  sector: string;
  unit: string;
  active_only?: boolean;
}

export async function listSchemas(
  q: ListSchemasQuery,
): Promise<SchemaFieldDoc[]> {
  const r = await api.get("/schemas", {
    params: { active_only: true, ...q },
  });
  return z.array(SchemaFieldDocSchema).parse(r.data);
}

export async function bulkImport(
  body: BulkImportRequest,
): Promise<SchemaFieldDoc[]> {
  const r = await api.post("/schemas/bulk-import", body);
  return z.array(SchemaFieldDocSchema).parse(r.data);
}

export interface HistoryQuery {
  sector: string;
  unit: string;
  limit?: number;
  since?: string;
}

export async function getHistory(q: HistoryQuery): Promise<SchemaAuditEntry[]> {
  const r = await api.get("/schemas/history", { params: q });
  return z.array(SchemaAuditEntrySchema).parse(r.data);
}

// Issue #31: business-user-facing read-only changelog. No admin role
// required; `changed_by` is masked to "reviewer" server-side.
export async function getHistoryPublic(
  q: HistoryQuery,
): Promise<SchemaAuditEntry[]> {
  const r = await api.get("/schemas/history/public", { params: q });
  return z.array(SchemaAuditEntrySchema).parse(r.data);
}
