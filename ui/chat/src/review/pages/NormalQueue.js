import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { decideReview, getPriorityMode, listReviews, lockReview, unlockReview, } from "../api/reviews";
import { WeightBreakdown } from "../components/WeightBreakdown";
import { LockBadge } from "../components/LockBadge";
import { PriorityModeBanner } from "../components/PriorityModeBanner";
function ageMin(iso) {
    return Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
}
export function NormalQueue() {
    const [tickets, setTickets] = useState([]);
    const [selected, setSelected] = useState(null);
    const [priorityOnly, setPriorityOnly] = useState(false);
    const [pmActive, setPmActive] = useState(false);
    const [pmMedian, setPmMedian] = useState(0);
    const [pmThreshold, setPmThreshold] = useState(180);
    async function load() {
        setTickets(await listReviews(priorityOnly));
        const pm = await getPriorityMode();
        setPmActive(pm.active);
        setPmMedian(pm.median_sec);
        setPmThreshold(pm.threshold_sec);
    }
    useEffect(() => {
        load();
    }, [priorityOnly]);
    async function onLock(t) {
        await lockReview(t.id);
        await load();
    }
    async function onUnlock(t) {
        await unlockReview(t.id);
        await load();
    }
    async function onDecide(t, decision) {
        const [sector, unit] = t.pk.split("#");
        await decideReview(t.id, sector ?? "", unit ?? "", decision);
        setSelected(null);
        await load();
    }
    return (_jsxs("div", { style: { padding: "1rem", fontFamily: "sans-serif" }, children: [_jsx("h2", { children: "\u30EC\u30D3\u30E5\u30FC\u5F85\u3061\u30AD\u30E5\u30FC" }), _jsx(PriorityModeBanner, { active: pmActive, medianSec: pmMedian, thresholdSec: pmThreshold, priorityOnly: priorityOnly, onToggle: setPriorityOnly }), tickets.length === 0 && _jsx("p", { children: "\u30AD\u30E5\u30FC\u306F\u7A7A\u3067\u3059\u3002" }), _jsxs("table", { style: { width: "100%", borderCollapse: "collapse", fontSize: 14 }, children: [_jsx("thead", { children: _jsxs("tr", { style: { background: "#f3f4f6" }, children: [_jsx("th", { style: { textAlign: "left", padding: 6 }, children: "ID" }), _jsx("th", { children: "5W1H \u6982\u8981" }), _jsx("th", { children: "weight" }), _jsx("th", { children: "TJ" }), _jsx("th", { children: "lock" }), _jsx("th", { children: "age" }), _jsx("th", {})] }) }), _jsx("tbody", { children: tickets.map((t) => (_jsxs("tr", { style: { borderTop: "1px solid #eee" }, children: [_jsx("td", { style: { padding: 6 }, children: t.id.slice(0, 8) }), _jsxs("td", { children: ["hearout: ", t.hearout_id.slice(0, 8)] }), _jsx("td", { children: _jsx(WeightBreakdown, { a: t.weight_a, b: t.weight_b, c: t.weight_c, final: t.weight_final }) }), _jsx("td", { children: t.tj_verdict && (_jsx("span", { style: {
                                            padding: "2px 6px",
                                            borderRadius: 4,
                                            background: t.tj_verdict === "supported" ? "#bbf7d0" : "#fde68a",
                                            fontSize: 12,
                                        }, children: t.tj_verdict })) }), _jsx("td", { children: _jsx(LockBadge, { lockedBy: t.locked_by, lockExpiresAt: t.lock_expires_at }) }), _jsxs("td", { children: [ageMin(t.created_at), "\u5206"] }), _jsxs("td", { children: [_jsx("button", { onClick: () => setSelected(t), children: "\u958B\u304F" }), !t.locked_by ? (_jsx("button", { onClick: () => onLock(t), children: "\u30ED\u30C3\u30AF" })) : (_jsx("button", { onClick: () => onUnlock(t), children: "\u89E3\u9664" }))] })] }, t.id))) })] }), selected && (_jsxs("aside", { style: {
                    position: "fixed",
                    right: 0,
                    top: 0,
                    bottom: 0,
                    width: 360,
                    background: "#fff",
                    borderLeft: "1px solid #ccc",
                    padding: "1rem",
                    overflowY: "auto",
                }, children: [_jsxs("h3", { children: ["ticket ", selected.id.slice(0, 8)] }), _jsxs("p", { children: ["hearout: ", selected.hearout_id] }), _jsxs("p", { children: ["weight: A=", selected.weight_a.toFixed(2), " B=", selected.weight_b.toFixed(2), " C=", selected.weight_c.toFixed(2), " \u2192", " ", selected.weight_final.toFixed(2)] }), _jsxs("p", { children: ["TJ: ", selected.tj_verdict ?? "n/a"] }), _jsxs("p", { children: ["\u95A2\u9023 turn: ", _jsx("code", { children: "(hearout\u304B\u3089\u8FBF\u308B \u2014 WT-D\u9023\u643ATODO)" })] }), _jsxs("div", { style: { display: "flex", gap: 8, marginTop: 12 }, children: [_jsx("button", { onClick: () => onDecide(selected, "approve"), children: "\u627F\u8A8D" }), _jsx("button", { onClick: () => onDecide(selected, "edit"), children: "\u7DE8\u96C6" }), _jsx("button", { onClick: () => onDecide(selected, "reject"), children: "\u5374\u4E0B" }), _jsx("button", { onClick: () => setSelected(null), style: { marginLeft: "auto" }, children: "\u9589\u3058\u308B" })] })] }))] }));
}
