import { api } from "./client";
import { SchemaAuditEntrySchema, SchemaFieldDocSchema, } from "../types";
import { z } from "zod";
export async function createSchema(body) {
    const r = await api.post("/schemas", body);
    return SchemaFieldDocSchema.parse(r.data);
}
export async function updateSchema(id, body) {
    const r = await api.patch(`/schemas/${encodeURIComponent(id)}`, body);
    return SchemaFieldDocSchema.parse(r.data);
}
export async function setActive(id, pk, is_active, reason) {
    const body = { is_active, reason: reason ?? null };
    const r = await api.post(`/schemas/${encodeURIComponent(id)}/active`, body, {
        params: { pk },
    });
    return SchemaAuditEntrySchema.parse(r.data);
}
export async function listSchemas(q) {
    const r = await api.get("/schemas", {
        params: { active_only: true, ...q },
    });
    return z.array(SchemaFieldDocSchema).parse(r.data);
}
export async function bulkImport(body) {
    const r = await api.post("/schemas/bulk-import", body);
    return z.array(SchemaFieldDocSchema).parse(r.data);
}
export async function getHistory(q) {
    const r = await api.get("/schemas/history", { params: q });
    return z.array(SchemaAuditEntrySchema).parse(r.data);
}
