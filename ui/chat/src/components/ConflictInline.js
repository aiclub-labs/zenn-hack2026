import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useState } from "react";
export function ConflictInline({ conflicts }) {
    const [open, setOpen] = useState(false);
    if (conflicts.length === 0)
        return null;
    const total = conflicts.reduce((a, c) => a + c.alt_count, 0);
    return (_jsxs("div", { style: {
            background: "#eef6ff",
            border: "1px dashed #5aa0e0",
            padding: "0.5rem 0.75rem",
            borderRadius: 6,
            margin: "0.25rem 0",
            fontSize: 13,
        }, children: [_jsxs("button", { type: "button", onClick: () => setOpen((v) => !v), children: ["\u4ED6\u306B ", total, " \u4EF6\u306E\u7570\u306A\u308B\u898B\u89E3\u3042\u308A (", open ? "閉じる" : "詳細", ")"] }), open && (_jsx("ul", { style: { marginTop: 6, paddingLeft: 18 }, children: conflicts.map((c) => (_jsxs("li", { children: [c.schema_field_id, ": ", c.alt_count, " viewpoints"] }, c.schema_field_id))) }))] }));
}
