import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
export function PriorityModeBanner({ active, medianSec, thresholdSec, priorityOnly, onToggle, }) {
    if (!active)
        return null;
    return (_jsxs("div", { style: {
            background: "#fee2e2",
            border: "1px solid #fca5a5",
            padding: "0.5rem 0.75rem",
            borderRadius: 6,
            margin: "0.5rem 0",
            display: "flex",
            alignItems: "center",
            gap: 12,
        }, children: [_jsxs("strong", { children: ["\u30EC\u30D3\u30E5\u30FC\u4E2D\u592E\u5024 ", (medianSec / 60).toFixed(1), " \u5206"] }), _jsxs("span", { style: { fontSize: 12 }, children: ["(\u95BE\u5024 ", (thresholdSec / 60).toFixed(0), " \u5206)"] }), _jsxs("label", { style: { marginLeft: "auto" }, children: [_jsx("input", { type: "checkbox", checked: priorityOnly, onChange: (e) => onToggle(e.target.checked) }), "\u512A\u5148 3 \u4EF6\u306E\u307F\u8868\u793A"] })] }));
}
