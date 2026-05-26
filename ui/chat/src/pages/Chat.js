import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useCallback, useMemo } from "react";
import { Button, Textarea, makeStyles, tokens, shorthands, } from "@fluentui/react-components";
import { Send24Regular } from "@fluentui/react-icons";
import { ChatWindow } from "../components/ChatWindow";
import { SchemaUpdateBannerView } from "../components/SchemaUpdateBanner";
import { HearoutModal } from "../components/HearoutModal";
import { ConflictInline } from "../components/ConflictInline";
import { SchemaHistorySidebar } from "../components/SchemaHistorySidebar";
import { RedactToggle } from "../components/RedactToggle";
import { postTurn } from "../api/turn";
import { retrieve } from "../api/retrieval";
import { useTenantCtx } from "../shell/TenantContext";
const useStyles = makeStyles({
    root: {
        display: "flex",
        height: "calc(100vh - 60px)",
    },
    main: {
        display: "flex",
        flexDirection: "column",
        flex: 1,
        minWidth: 0,
    },
    toolbar: {
        display: "flex",
        justifyContent: "flex-end",
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalXL),
        backgroundColor: tokens.colorNeutralBackground1,
        borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    },
    composer: {
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalXL),
        backgroundColor: tokens.colorNeutralBackground1,
        borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
        display: "flex",
        flexDirection: "column",
        gap: tokens.spacingVerticalS,
    },
    composerRow: {
        display: "flex",
        justifyContent: "flex-end",
    },
});
export function ChatPage() {
    const styles = useStyles();
    const { tenant, sessionId } = useTenantCtx();
    const ctx = useMemo(() => ({
        user_id: tenant.user_id,
        sector: tenant.sector,
        unit: tenant.unit,
        session_id: sessionId,
    }), [tenant, sessionId]);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [redact, setRedact] = useState(false);
    const [banner, setBanner] = useState(null);
    const [lastTurnId, setLastTurnId] = useState(null);
    const [conflicts, setConflicts] = useState([]);
    const [hearoutOpen, setHearoutOpen] = useState(false);
    const [busy, setBusy] = useState(false);
    const send = useCallback(async () => {
        if (!input.trim() || busy)
            return;
        const userMsg = { role: "user", content: input };
        setMessages((m) => [...m, userMsg]);
        setBusy(true);
        try {
            const [res, ret] = await Promise.all([
                postTurn(ctx, input, redact),
                retrieve(ctx.sector, ctx.unit, input, ctx.user_id),
            ]);
            setBanner(res.schema_update_banner ?? null);
            setLastTurnId(res.turn_id);
            setConflicts(ret.conflicts);
            setMessages((m) => [
                ...m,
                {
                    role: "assistant",
                    content: res.ai_response,
                    turnId: res.turn_id,
                    citations: res.citations,
                    selfCriticScore: res.self_critic_score,
                },
            ]);
            if (res.gap_detected)
                setHearoutOpen(true);
            setInput("");
        }
        finally {
            setBusy(false);
        }
    }, [ctx, input, redact, busy]);
    return (_jsxs("div", { className: styles.root, children: [_jsxs("div", { className: styles.main, children: [_jsx("div", { className: styles.toolbar, children: _jsx(RedactToggle, { value: redact, onChange: setRedact }) }), banner && lastTurnId && (_jsx(SchemaUpdateBannerView, { banner: banner, turnId: lastTurnId, sector: ctx.sector, unit: ctx.unit, userId: ctx.user_id, onAck: () => setBanner(null) })), _jsx(ConflictInline, { conflicts: conflicts }), _jsx(ChatWindow, { messages: messages, sector: ctx.sector, unit: ctx.unit }), _jsxs("div", { className: styles.composer, children: [_jsx(Textarea, { value: input, onChange: (_, data) => setInput(data.value), rows: 2, placeholder: "\u8CEA\u554F\u30FB\u78BA\u8A8D\u3057\u305F\u3044\u5185\u5BB9\u3092\u66F8\u3044\u3066\u304F\u3060\u3055\u3044\u2026", resize: "vertical" }), _jsx("div", { className: styles.composerRow, children: _jsx(Button, { appearance: "primary", icon: _jsx(Send24Regular, {}), onClick: send, disabled: busy || !input.trim(), children: busy ? "送信中…" : "送信" }) })] })] }), _jsx(SchemaHistorySidebar, { sector: ctx.sector, unit: ctx.unit }), hearoutOpen && (_jsx(HearoutModal, { sessionId: ctx.session_id, initialQuestion: "\u3053\u306E\u4E8B\u8C61\u306B\u3064\u3044\u3066 5W1H \u3067\u6559\u3048\u3066\u304F\u3060\u3055\u3044\u3002\u307E\u305A who: \u8AB0\u304C\u95A2\u308F\u308A\u307E\u3057\u305F\u304B?", onClose: () => setHearoutOpen(false) }))] }));
}
