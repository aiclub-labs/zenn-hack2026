import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { ackBanner } from "../api/turn";
export function SchemaUpdateBannerView({ banner, turnId, sector, unit, userId, onAck, }) {
    return (_jsxs("div", { role: "status", style: {
            background: "#fff7e6",
            border: "1px solid #f0b73b",
            padding: "0.75rem 1rem",
            borderRadius: 6,
            margin: "0.5rem 0",
        }, children: [_jsxs("strong", { children: ["schema \u66F4\u65B0\u304C ", banner.unseen_revision_ids.length, " \u4EF6\u3042\u308A\u307E\u3059"] }), _jsx("div", { style: { fontSize: 13, margin: "0.25rem 0" }, children: banner.changed_fields_summary }), _jsx("a", { href: banner.history_url, target: "_blank", rel: "noreferrer", children: "\u5C65\u6B74\u3092\u898B\u308B" }), _jsx("button", { type: "button", style: { marginLeft: "1rem" }, onClick: async () => {
                    await ackBanner(turnId, sector, unit, userId);
                    onAck();
                }, children: "\u78BA\u8A8D" })] }));
}
