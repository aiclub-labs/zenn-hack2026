import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { setActive, updateSchema, createSchema, listSchemas, } from "../api/schemas";
import { pk } from "../lib/tenant";
import { formatJst } from "../lib/jst";
const EMPTY = {
    id: "",
    pk: "",
    sector: "",
    unit: "",
    field_name: "",
    description: "",
    expected_value_type: "string",
    example: "",
    ai_baseline_assumption: "",
    is_active: true,
    revision_id: 0,
    updated_at: new Date().toISOString(),
    updated_by: "shigeru.dev",
};
export default function SchemaList({ tenant }) {
    const qc = useQueryClient();
    const partition = pk(tenant);
    // M-7: GET /schemas?sector=&unit=&active_only=false returns the current set
    // directly — no need to replay /schemas/history.
    const listQ = useQuery({
        queryKey: ["schemas-list", tenant],
        queryFn: () => listSchemas({ ...tenant, active_only: false }),
    });
    const current = (listQ.data ?? [])
        .slice()
        .sort((a, b) => a.field_name.localeCompare(b.field_name));
    const [draft, setDraft] = useState(null);
    const upsertMut = useMutation({
        mutationFn: async (d) => {
            const filled = {
                ...d,
                pk: partition,
                sector: tenant.sector,
                unit: tenant.unit,
            };
            return filled.revision_id === 0
                ? createSchema(filled)
                : updateSchema(filled.id, filled);
        },
        onSuccess: () => {
            setDraft(null);
            qc.invalidateQueries({ queryKey: ["schemas-list"] });
            qc.invalidateQueries({ queryKey: ["history"] });
        },
    });
    const toggleMut = useMutation({
        mutationFn: (d) => setActive(d.id, d.pk, !d.is_active, "toggled via admin UI"),
        onSuccess: () => qc.invalidateQueries({ queryKey: ["schemas-list"] }),
    });
    return (_jsxs("section", { children: [_jsxs("h2", { children: ["\u30B9\u30AD\u30FC\u30DE\u4E00\u89A7 (", partition, ")"] }), _jsxs("div", { className: "row", children: [_jsx("button", { onClick: () => setDraft({
                            ...EMPTY,
                            id: crypto.randomUUID(),
                            pk: partition,
                            sector: tenant.sector,
                            unit: tenant.unit,
                        }), children: "\u65B0\u898F\u8FFD\u52A0" }), _jsxs("span", { className: "muted", children: ["\u30EA\u30B8\u30A7\u30AF\u30C8\u7387 (mock): ", _jsx("strong", { children: "12%" }), " / \u76F4\u8FD17\u65E5"] })] }), listQ.isLoading && _jsx("p", { children: "\u8AAD\u307F\u8FBC\u307F\u4E2D\u2026" }), listQ.isError && (_jsxs("p", { style: { color: "crimson" }, children: ["\u53D6\u5F97\u5931\u6557: ", String(listQ.error)] })), _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "field_name" }), _jsx("th", { children: "type" }), _jsx("th", { children: "description" }), _jsx("th", { children: "example" }), _jsx("th", { children: "rev" }), _jsx("th", { children: "is_active" }), _jsx("th", { children: "updated_at (JST)" }), _jsx("th", {})] }) }), _jsx("tbody", { children: current.map((d) => (_jsxs("tr", { children: [_jsx("td", { children: d.field_name }), _jsx("td", { children: d.expected_value_type }), _jsx("td", { children: d.description }), _jsx("td", { children: d.example }), _jsx("td", { children: d.revision_id }), _jsx("td", { children: _jsx("span", { className: `badge ${d.is_active ? "active" : "inactive"}`, children: d.is_active ? "active" : "inactive" }) }), _jsx("td", { children: formatJst(d.updated_at) }), _jsxs("td", { children: [_jsx("button", { onClick: () => setDraft(d), children: "\u7DE8\u96C6" }), " ", _jsx("button", { onClick: () => toggleMut.mutate(d), children: d.is_active ? "無効化" : "再有効化" })] })] }, d.id))) })] }), draft && (_jsx(Editor, { value: draft, onCancel: () => setDraft(null), onSave: (d) => upsertMut.mutate(d), saving: upsertMut.isPending }))] }));
}
function Editor({ value, onCancel, onSave, saving }) {
    const [v, setV] = useState(value);
    return (_jsxs("div", { className: "card", children: [_jsx("h3", { children: v.revision_id === 0 ? "新規スキーマ" : `編集: ${v.field_name}` }), _jsxs("div", { className: "col", children: [_jsxs("label", { children: ["field_name", _jsx("input", { value: v.field_name, onChange: (e) => setV({ ...v, field_name: e.target.value }) })] }), _jsxs("label", { children: ["description", _jsx("textarea", { value: v.description, onChange: (e) => setV({ ...v, description: e.target.value }) })] }), _jsxs("label", { children: ["expected_value_type", _jsxs("select", { value: v.expected_value_type, onChange: (e) => setV({
                                    ...v,
                                    expected_value_type: e.target.value,
                                }), children: [_jsx("option", { children: "string" }), _jsx("option", { children: "number" }), _jsx("option", { children: "enum" }), _jsx("option", { children: "structured" })] })] }), _jsxs("label", { children: ["example", _jsx("input", { value: v.example, onChange: (e) => setV({ ...v, example: e.target.value }) })] }), _jsxs("label", { children: ["ai_baseline_assumption", _jsx("textarea", { value: v.ai_baseline_assumption, onChange: (e) => setV({ ...v, ai_baseline_assumption: e.target.value }) })] })] }), _jsxs("div", { className: "row", children: [_jsx("button", { disabled: saving, onClick: () => onSave(v), children: "\u4FDD\u5B58" }), _jsx("button", { onClick: onCancel, children: "\u30AD\u30E3\u30F3\u30BB\u30EB" })] })] }));
}
