import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useState } from "react";
import { getCitation } from "../api/citations";
export function CitationCard({ citation, sector, unit }) {
    const [detail, setDetail] = useState(null);
    const [open, setOpen] = useState(false);
    async function toggle() {
        if (!detail) {
            setDetail(await getCitation(citation.record_id, sector, unit));
        }
        setOpen((v) => !v);
    }
    const weightPct = Math.min(100, Math.max(0, citation.weight * 100));
    return (_jsxs("div", { style: {
            border: "1px solid #ddd",
            borderRadius: 6,
            padding: "0.5rem 0.75rem",
            margin: "0.25rem 0",
            background: citation.superseded_by ? "#fff4f4" : "#fafafa",
        }, children: [_jsxs("div", { style: { display: "flex", alignItems: "center", gap: 8 }, children: [_jsxs("button", { type: "button", onClick: toggle, style: { flex: 1, textAlign: "left" }, children: ["[", citation.schema_field_id, "] ", citation.record_id.slice(0, 8)] }), _jsx("div", { "aria-label": `weight ${weightPct.toFixed(0)}%`, style: {
                            width: 60,
                            height: 8,
                            background: "#eee",
                            borderRadius: 4,
                            overflow: "hidden",
                        }, children: _jsx("div", { style: {
                                width: `${weightPct}%`,
                                height: "100%",
                                background: "#3b82f6",
                            } }) })] }), detail?.superseded_banner && (_jsxs("div", { style: { color: "#b91c1c", fontSize: 12, marginTop: 4 }, children: ["\u26A0 ", detail.superseded_banner] })), open && detail && (_jsx("div", { style: { fontSize: 13, marginTop: 6, whiteSpace: "pre-wrap" }, children: detail.content }))] }));
}
