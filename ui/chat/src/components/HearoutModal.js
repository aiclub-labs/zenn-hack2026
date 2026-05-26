import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useState } from "react";
import { respondHearout, skipHearout } from "../api/hearout";
export function HearoutModal({ sessionId, initialQuestion, onClose }) {
    const [question, setQuestion] = useState(initialQuestion);
    const [turnCount, setTurnCount] = useState(1);
    const [answer, setAnswer] = useState("");
    const [busy, setBusy] = useState(false);
    async function submit() {
        if (!answer.trim())
            return;
        setBusy(true);
        try {
            const t = await respondHearout(sessionId, answer);
            setTurnCount(t.turn_count);
            setAnswer("");
            if (t.status !== "in_progress" || !t.next_question) {
                onClose();
            }
            else {
                setQuestion(t.next_question);
            }
        }
        finally {
            setBusy(false);
        }
    }
    async function skip() {
        setBusy(true);
        try {
            await skipHearout(sessionId);
            onClose();
        }
        finally {
            setBusy(false);
        }
    }
    return (_jsxs("div", { role: "dialog", "aria-label": "hearout-5w1h", style: {
            position: "fixed",
            right: 16,
            bottom: 16,
            width: 360,
            background: "#fff",
            border: "1px solid #ccc",
            borderRadius: 8,
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            padding: "1rem",
            zIndex: 50,
        }, children: [_jsxs("div", { style: {
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 12,
                }, children: [_jsxs("strong", { children: ["5W1H \u78BA\u8A8D (", turnCount, "/5)"] }), _jsx("button", { type: "button", onClick: onClose, "aria-label": "close", children: "\u00D7" })] }), _jsx("p", { style: { margin: "0.5rem 0" }, children: question }), _jsx("textarea", { value: answer, onChange: (e) => setAnswer(e.target.value), rows: 3, style: { width: "100%" }, placeholder: "\u81EA\u7531\u56DE\u7B54\u2026" }), _jsxs("div", { style: {
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: 8,
                    marginTop: 8,
                }, children: [_jsx("button", { type: "button", onClick: skip, disabled: busy, children: "\u30B9\u30AD\u30C3\u30D7" }), _jsx("button", { type: "button", onClick: submit, disabled: busy || !answer.trim(), children: "\u9001\u4FE1" })] })] }));
}
