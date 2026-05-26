import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { api } from "../api/client";
export function SchemaHistorySidebar({ sector, unit }) {
    const [items, setItems] = useState([]);
    useEffect(() => {
        (async () => {
            try {
                const { data } = await api.get("/schemas/history", {
                    params: { sector, unit, limit: 20 },
                });
                setItems(data);
            }
            catch {
                setItems([]);
            }
        })();
    }, [sector, unit]);
    return (_jsxs("aside", { style: {
            borderLeft: "1px solid #eee",
            padding: "0.75rem",
            minWidth: 220,
            fontSize: 13,
        }, children: [_jsx("h3", { style: { fontSize: 14, margin: "0 0 .5rem" }, children: "\u6700\u8FD1\u306E schema \u5909\u66F4" }), items.length === 0 && _jsx("em", { children: "\u5C65\u6B74\u306A\u3057" }), _jsx("ul", { style: { listStyle: "none", padding: 0, margin: 0 }, children: items.map((e) => (_jsxs("li", { style: { padding: "4px 0", borderBottom: "1px solid #f3f3f3" }, children: [_jsxs("code", { children: ["r", e.revision_id] }), " ", e.change_type, _jsx("div", { style: { color: "#666", fontSize: 11 }, children: new Date(e.changed_at).toLocaleString("ja-JP", {
                                timeZone: "Asia/Tokyo",
                            }) })] }, e.id))) })] }));
}
