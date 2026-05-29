import { useState, useCallback, useMemo } from "react";
import {
  Button,
  Textarea,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import { Send24Regular } from "@fluentui/react-icons";
import { ChatWindow } from "../components/ChatWindow";
import { SchemaUpdateBannerView } from "../components/SchemaUpdateBanner";
import { HearoutModal } from "../components/HearoutModal";
import { ConflictInline } from "../components/ConflictInline";
import { SchemaHistorySidebar } from "../components/SchemaHistorySidebar";
import { RedactToggle } from "../components/RedactToggle";
import { ChatMessage, SchemaUpdateBanner, TenantCtx } from "../types";
import { postTurn } from "../api/turn";
import { retrieve } from "../api/retrieval";
import { startHearout } from "../api/hearout";
import { useTenantCtx } from "../shell/TenantContext";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flex: 1,
    minHeight: 0,
  },
  main: {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    minWidth: 0,
  },
  sidebarWrap: {
    "@media (max-width: 768px)": {
      display: "none",
    },
  },
  toolbar: {
    display: "flex",
    justifyContent: "flex-end",
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalXL),
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    "@media (max-width: 768px)": {
      ...shorthands.padding(
        tokens.spacingVerticalXS,
        tokens.spacingHorizontalM,
      ),
    },
  },
  composer: {
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalXL),
    backgroundColor: tokens.colorNeutralBackground1,
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalS,
    "@media (max-width: 768px)": {
      ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
  },
  composerRow: {
    display: "flex",
    justifyContent: "flex-end",
  },
});

export function ChatPage() {
  const styles = useStyles();
  const { tenant, sessionId } = useTenantCtx();
  const ctx = useMemo<TenantCtx>(
    () => ({
      user_id: tenant.user_id,
      sector: tenant.sector,
      unit: tenant.unit,
      session_id: sessionId,
    }),
    [tenant, sessionId],
  );

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [redact, setRedact] = useState(false);
  const [banner, setBanner] = useState<SchemaUpdateBanner | null>(null);
  const [lastTurnId, setLastTurnId] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<
    { schema_field_id: string; alt_count: number }[]
  >([]);
  const [hearoutOpen, setHearoutOpen] = useState(false);
  const [hearoutSessionId, setHearoutSessionId] = useState<string | null>(null);
  const [hearoutInitialQuestion, setHearoutInitialQuestion] = useState<string>(
    "この事象について 5W1H で教えてください。まず who: 誰が関わりましたか?",
  );
  const [busy, setBusy] = useState(false);

  const send = useCallback(async () => {
    if (!input.trim() || busy) return;
    const userMsg: ChatMessage = { role: "user", content: input };
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
          selfCriticReason: res.self_critic_reason ?? null,
        },
      ]);
      if (res.gap_detected && res.gap_event_id) {
        try {
          const ho = await startHearout({
            gap_event_id: res.gap_event_id,
            user_id: ctx.user_id,
            sector: ctx.sector,
            unit: ctx.unit,
          });
          setHearoutSessionId(ho.session_id);
          if (ho.next_question) setHearoutInitialQuestion(ho.next_question);
          setHearoutOpen(true);
        } catch (err) {
          console.error("hearout start failed", err);
        }
      }
      setInput("");
    } finally {
      setBusy(false);
    }
  }, [ctx, input, redact, busy]);

  return (
    <div className={styles.root}>
      <div className={styles.main}>
        <div className={styles.toolbar}>
          <RedactToggle value={redact} onChange={setRedact} />
        </div>
        {banner && lastTurnId && (
          <SchemaUpdateBannerView
            banner={banner}
            turnId={lastTurnId}
            sector={ctx.sector}
            unit={ctx.unit}
            userId={ctx.user_id}
            onAck={() => setBanner(null)}
          />
        )}
        <ConflictInline conflicts={conflicts} />
        <ChatWindow messages={messages} sector={ctx.sector} unit={ctx.unit} />
        <div className={styles.composer}>
          <Textarea
            value={input}
            onChange={(_, data) => setInput(data.value)}
            onKeyDown={(ev) => {
              if (
                ev.key === "Enter" &&
                !ev.shiftKey &&
                !ev.nativeEvent.isComposing
              ) {
                ev.preventDefault();
                if (!busy && input.trim()) void send();
              }
            }}
            rows={2}
            placeholder="質問・確認したい内容 (Enter で送信 / Shift+Enter で改行)"
            resize="vertical"
          />
          <div className={styles.composerRow}>
            <Button
              appearance="primary"
              icon={<Send24Regular />}
              onClick={send}
              disabled={busy || !input.trim()}
            >
              {busy ? "送信中…" : "送信"}
            </Button>
          </div>
        </div>
      </div>
      <div className={styles.sidebarWrap}>
        <SchemaHistorySidebar sector={ctx.sector} unit={ctx.unit} />
      </div>
      {hearoutOpen && hearoutSessionId && (
        <HearoutModal
          sessionId={hearoutSessionId}
          initialQuestion={hearoutInitialQuestion}
          onClose={() => {
            setHearoutOpen(false);
            setHearoutSessionId(null);
          }}
        />
      )}
    </div>
  );
}
