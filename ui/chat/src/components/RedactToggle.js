import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function RedactToggle({ value, onChange }) {
    return (_jsxs("label", { style: {
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 13,
            color: value ? "#b91c1c" : "#374151",
        }, children: [_jsx("input", { type: "checkbox", checked: value, onChange: (e) => onChange(e.target.checked) }), "Redact \u6A5F\u5BC6 (\u672C\u6587\u3092\u4FDD\u5B58\u3057\u306A\u3044)", value && _jsx("span", { "aria-label": "redact-on", children: "\uD83D\uDD12" })] }));
}
