import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { decideConflict, listConflictReviews } from "../api/reviews";
import { WeightBreakdown } from "../components/WeightBreakdown";
export function ConflictQueue() {
    const [tickets, setTickets] = useState([]);
    const [selected, setSelected] = useState(null);
    async function load() {
        setTickets(await listConflictReviews());
    }
    useEffect(() => {
        load();
    }, []);
    async function decide(t, d) {
        const [sector, unit] = t.pk.split("#");
        await decideConflict(t.id, sector ?? "", unit ?? "", d);
        setSelected(null);
        await load();
    }
    return (_jsxs("div", { style: { padding: "1rem", fontFamily: "sans-serif" }, children: [_jsx("h2", { children: "\u7AF6\u5408\u30EC\u30D3\u30E5\u30FC (conflict_pending)" }), tickets.length === 0 && _jsx("p", { children: "\u7AF6\u5408\u306F\u3042\u308A\u307E\u305B\u3093\u3002" }), _jsx("ul", { style: { listStyle: "none", padding: 0 }, children: tickets.map((t) => (_jsxs("li", { style: {
                        border: "1px solid #e5e7eb",
                        padding: "0.75rem",
                        borderRadius: 6,
                        marginBottom: 8,
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                    }, children: [_jsx("span", { children: t.id.slice(0, 8) }), _jsx(WeightBreakdown, { a: t.weight_a, b: t.weight_b, c: t.weight_c, final: t.weight_final }), _jsx("button", { style: { marginLeft: "auto" }, onClick: () => setSelected(t), children: "\u6BD4\u8F03" })] }, t.id))) }), selected && (_jsx("div", { style: {
                    position: "fixed",
                    inset: 0,
                    background: "rgba(0,0,0,0.4)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                }, children: _jsxs("div", { style: {
                        background: "#fff",
                        padding: "1.5rem",
                        borderRadius: 8,
                        minWidth: 720,
                    }, children: [_jsxs("h3", { children: ["\u4E26\u5217\u6BD4\u8F03: ", selected.id.slice(0, 8)] }), _jsxs("div", { style: {
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: 16,
                            }, children: [_jsxs("section", { style: { background: "#eff6ff", padding: 12, borderRadius: 6 }, children: [_jsx("h4", { children: "\u65B0\u898F\u5019\u88DC" }), _jsxs("p", { children: ["hearout: ", selected.hearout_id.slice(0, 8)] }), _jsxs("p", { children: ["weight: ", selected.weight_final.toFixed(2)] })] }), _jsxs("section", { style: { background: "#fef3c7", padding: 12, borderRadius: 6 }, children: [_jsx("h4", { children: "\u65E2\u5B58 (WT-D \u9023\u643A TODO)" }), _jsx("p", { children: "citation_audit_log preview \u2026" })] })] }), _jsxs("div", { style: { display: "flex", gap: 8, marginTop: 16 }, children: [_jsx("button", { onClick: () => decide(selected, "adopt_new"), children: "\u65B0\u898F\u63A1\u7528" }), _jsx("button", { onClick: () => decide(selected, "keep_existing"), children: "\u65E2\u5B58\u7DAD\u6301" }), _jsx("button", { onClick: () => decide(selected, "coexist"), children: "\u4E21\u65B9\u6B8B\u3059" }), _jsx("button", { onClick: () => setSelected(null), style: { marginLeft: "auto" }, children: "\u30AD\u30E3\u30F3\u30BB\u30EB" })] })] }) }))] }));
}
