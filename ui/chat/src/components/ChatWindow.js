import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { CitationCard } from "./CitationCard";
export function ChatWindow({ messages, sector, unit }) {
    return (_jsx("div", { style: {
            flex: 1,
            overflowY: "auto",
            padding: "1rem",
            background: "#fff",
        }, children: messages.map((m, i) => (_jsx("div", { style: {
                margin: "0.75rem 0",
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
            }, children: _jsxs("div", { style: {
                    maxWidth: "75%",
                    background: m.role === "user" ? "#e0f2fe" : "#f3f4f6",
                    padding: "0.5rem 0.75rem",
                    borderRadius: 8,
                }, children: [_jsx("div", { style: { whiteSpace: "pre-wrap" }, children: m.content }), typeof m.selfCriticScore === "number" && (_jsxs("div", { style: { fontSize: 11, color: "#666", marginTop: 4 }, children: ["self-critic: ", m.selfCriticScore.toFixed(1), " / 10"] })), m.citations && m.citations.length > 0 && (_jsx("div", { style: { marginTop: 6 }, children: m.citations.map((c) => (_jsx(CitationCard, { citation: c, sector: sector, unit: unit }, c.record_id))) }))] }) }, i))) }));
}
