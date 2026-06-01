import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { bulkImport, getHistory } from "../api/schemas";
// Req 3: cross-tenant bulk import. Dry-run preview reuses history endpoint
// against the source tenant to list current active fields.
export default function SchemaImport({ target }) {
    const qc = useQueryClient();
    const [source, setSource] = useState({
        sector: "demo",
        unit: "team-b",
    });
    const [dryRun, setDryRun] = useState(true);
    const preview = useQuery({
        queryKey: ["history", source, "preview"],
        queryFn: () => getHistory({ ...source, limit: 500 }),
        enabled: dryRun,
    });
    const mut = useMutation({
        mutationFn: () => bulkImport({
            source_sector: source.sector,
            source_unit: source.unit,
            target_sector: target.sector,
            target_unit: target.unit,
        }),
        onSuccess: () => qc.invalidateQueries({ queryKey: ["history-as-list"] }),
    });
    const distinctFields = new Set((preview.data ?? []).map((e) => e.schema_field_id));
    return (_jsxs("section", { children: [_jsx("h2", { children: "\u4E00\u62EC\u30A4\u30F3\u30DD\u30FC\u30C8 (Req 3)" }), _jsxs("p", { className: "muted", children: ["\u30B3\u30D4\u30FC\u5143\u30C6\u30CA\u30F3\u30C8\u306E ", _jsx("code", { children: "is_active=true" }), " ", "\u306A\u30B9\u30AD\u30FC\u30DE\u306E\u307F\u3092\u5BFE\u8C61\u30C6\u30CA\u30F3\u30C8\u3078\u8907\u88FD\u3057\u307E\u3059\u3002", _jsx("br", {}), "revision_id=1 \u306B\u30EA\u30BB\u30C3\u30C8\u3001partition_key \u3092\u7F6E\u63DB\u3001\u76E3\u67FB\u30ED\u30B0\u306B", " ", _jsx("code", { children: "create" }), " \u3068\u3057\u3066\u8A18\u9332\u3002"] }), _jsxs("div", { className: "row", children: [_jsxs("div", { className: "col", children: [_jsxs("label", { children: ["\u30B3\u30D4\u30FC\u5143 sector", _jsx("input", { value: source.sector, onChange: (e) => setSource({ ...source, sector: e.target.value }) })] }), _jsxs("label", { children: ["\u30B3\u30D4\u30FC\u5143 unit", _jsx("input", { value: source.unit, onChange: (e) => setSource({ ...source, unit: e.target.value }) })] })] }), _jsxs("div", { className: "col", children: [_jsxs("label", { children: ["\u30B3\u30D4\u30FC\u5148 sector", _jsx("input", { value: target.sector, disabled: true })] }), _jsxs("label", { children: ["\u30B3\u30D4\u30FC\u5148 unit", _jsx("input", { value: target.unit, disabled: true })] }), _jsx("span", { className: "muted", children: "\u753B\u9762\u4E0A\u90E8\u306E\u9078\u629E\u3092\u5909\u66F4" })] }), _jsxs("div", { className: "col", children: [_jsxs("label", { children: [_jsx("input", { type: "checkbox", checked: dryRun, onChange: (e) => setDryRun(e.target.checked) }), " ", "Dry-run \u30D7\u30EC\u30D3\u30E5\u30FC"] }), _jsx("button", { disabled: mut.isPending, onClick: () => mut.mutate(), children: "\u5B9F\u884C" })] })] }), dryRun && (_jsxs("div", { className: "card", children: [_jsxs("strong", { children: ["\u30D7\u30EC\u30D3\u30E5\u30FC: \u5019\u88DC ", distinctFields.size, " \u4EF6"] }), _jsx("ul", { children: [...distinctFields].map((id) => (_jsx("li", { children: _jsx("code", { children: id }) }, id))) })] })), mut.isSuccess && (_jsxs("div", { className: "card", children: [_jsx("strong", { children: "\u30A4\u30F3\u30DD\u30FC\u30C8\u5B8C\u4E86:" }), " ", mut.data.length, " \u4EF6"] })), mut.isError && (_jsxs("p", { style: { color: "crimson" }, children: ["\u5931\u6557: ", String(mut.error)] }))] }));
}
