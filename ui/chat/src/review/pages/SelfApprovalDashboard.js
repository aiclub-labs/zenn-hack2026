import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { getSelfApproval } from "../api/reviews";
export function SelfApprovalDashboard() {
    const [info, setInfo] = useState(null);
    useEffect(() => {
        getSelfApproval()
            .then(setInfo)
            .catch(() => setInfo(null));
    }, []);
    if (!info)
        return _jsx("p", { style: { padding: "1rem" }, children: "\u8AAD\u307F\u8FBC\u307F\u4E2D\u2026" });
    const pct = (info.rate_7d * 100).toFixed(1);
    const thr = (info.threshold * 100).toFixed(0);
    return (_jsxs("div", { style: { padding: "1rem", fontFamily: "sans-serif" }, children: [_jsx("h2", { children: "\u81EA\u5DF1\u627F\u8A8D\u7387 (\u76F4\u8FD17\u65E5)" }), _jsxs("p", { style: { fontSize: 32, margin: 0 }, children: [pct, "%", info.warn && (_jsxs("span", { style: { color: "#b91c1c", fontSize: 14, marginLeft: 12 }, children: ["\u26A0 \u95BE\u5024 ", thr, "% \u3092\u8D85\u904E"] }))] }), _jsxs("p", { style: { color: "#666" }, children: ["reviewer: ", info.reviewer_id, " / \u95BE\u5024: ", thr, "%"] }), _jsxs("p", { style: { fontSize: 13 }, children: ["Req 9.9: \u81EA\u5DF1\u627F\u8A8D\u304C", thr, "% \u3092\u8D85\u3048\u305F\u5834\u5408\u306F\u5225\u30EC\u30D3\u30E5\u30A2\u30FC\u3078\u306E\u59D4\u4EFB\u3092\u691C\u8A0E\u3057\u3066\u304F\u3060\u3055\u3044\u3002"] })] }));
}
