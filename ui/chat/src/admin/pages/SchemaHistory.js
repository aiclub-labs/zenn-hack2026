import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useQuery } from "@tanstack/react-query";
import { getHistory } from "../api/schemas";
import { formatJst } from "../lib/jst";
// Req 2.6: read-only audit history.
export default function SchemaHistory({ tenant }) {
    const q = useQuery({
        queryKey: ["history", tenant],
        queryFn: () => getHistory({ ...tenant, limit: 200 }),
    });
    return (_jsxs("section", { children: [_jsxs("h2", { children: ["\u5909\u66F4\u5C65\u6B74 (", tenant.sector, "#", tenant.unit, ")"] }), _jsx("p", { className: "muted", children: "\u7269\u7406\u524A\u9664\u306F\u4E0D\u53EF\u3002\u3059\u3079\u3066\u306E\u904E\u53BB\u30EA\u30D3\u30B8\u30E7\u30F3\u3092\u4FDD\u6301\u3002" }), q.isLoading && _jsx("p", { children: "\u8AAD\u307F\u8FBC\u307F\u4E2D\u2026" }), q.isError && (_jsxs("p", { style: { color: "crimson" }, children: ["\u53D6\u5F97\u5931\u6557: ", String(q.error)] })), _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "changed_at (JST)" }), _jsx("th", { children: "field_id" }), _jsx("th", { children: "rev" }), _jsx("th", { children: "change_type" }), _jsx("th", { children: "diff" }), _jsx("th", { children: "reason" }), _jsx("th", { children: "changed_by" })] }) }), _jsx("tbody", { children: (q.data ?? []).map((e) => (_jsxs("tr", { children: [_jsx("td", { children: formatJst(e.changed_at) }), _jsx("td", { children: e.schema_field_id }), _jsx("td", { children: e.revision_id }), _jsx("td", { children: e.change_type }), _jsx("td", { className: "diff", children: renderDiff(e.diff) }), _jsx("td", { children: e.reason ?? "" }), _jsx("td", { children: e.changed_by })] }, e.id))) })] })] }));
}
function renderDiff(diff) {
    const lines = [];
    for (const [k, v] of Object.entries(diff)) {
        lines.push(`${k}: ${fmt(v.before)} → ${fmt(v.after)}`);
    }
    return lines.join("\n");
}
function fmt(v) {
    if (v === null || v === undefined)
        return "∅";
    if (typeof v === "string")
        return JSON.stringify(v);
    return String(v);
}
