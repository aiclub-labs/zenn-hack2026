import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
// Req 9.9: 自己承認 KPI。今日はスタブ（明日 reviews API 接続）。
export default function SelfApprovalDashboard({ tenant }) {
    const mock = {
        self_approval_rate: 0.18,
        avg_weight_final: 0.62,
        pending_count: 7,
        approved_24h: 14,
        rejected_24h: 2,
    };
    return (_jsxs("section", { children: [_jsxs("h2", { children: ["\u81EA\u5DF1\u627F\u8A8D\u30C0\u30C3\u30B7\u30E5\u30DC\u30FC\u30C9 (", tenant.sector, "#", tenant.unit, ")"] }), _jsx("p", { className: "muted", children: "Req 9.9 stub \u2014 reviews API \u7D50\u7DDA\u306F 5/26 \u4E88\u5B9A" }), _jsxs("div", { className: "row", children: [_jsx(Kpi, { label: "\u81EA\u5DF1\u627F\u8A8D\u7387", value: `${(mock.self_approval_rate * 100).toFixed(1)}%` }), _jsx(Kpi, { label: "\u5E73\u5747 weight_final", value: mock.avg_weight_final.toFixed(2) }), _jsx(Kpi, { label: "pending", value: String(mock.pending_count) }), _jsx(Kpi, { label: "\u627F\u8A8D 24h", value: String(mock.approved_24h) }), _jsx(Kpi, { label: "\u5374\u4E0B 24h", value: String(mock.rejected_24h) })] })] }));
}
function Kpi({ label, value }) {
    return (_jsxs("div", { className: "card", style: { minWidth: 140 }, children: [_jsx("div", { className: "muted", children: label }), _jsx("div", { style: { fontSize: 22, fontWeight: 600 }, children: value })] }));
}
