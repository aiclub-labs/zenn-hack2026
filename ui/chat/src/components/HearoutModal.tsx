import { useState } from "react";
import { respondHearout, skipHearout } from "../api/hearout";
import { HearoutTurn } from "../types";

interface Props {
  sessionId: string;
  initialQuestion: string;
  onClose: () => void;
}

export function HearoutModal({ sessionId, initialQuestion, onClose }: Props) {
  const [question, setQuestion] = useState(initialQuestion);
  const [turnCount, setTurnCount] = useState(1);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!answer.trim()) return;
    setBusy(true);
    try {
      const t: HearoutTurn = await respondHearout(sessionId, answer);
      setTurnCount(t.turn_count);
      setAnswer("");
      if (t.status !== "in_progress" || !t.next_question) {
        onClose();
      } else {
        setQuestion(t.next_question);
      }
    } finally {
      setBusy(false);
    }
  }

  async function skip() {
    setBusy(true);
    try {
      await skipHearout(sessionId);
      onClose();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-label="hearout-5w1h"
      style={{
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
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
        }}
      >
        <strong>5W1H 確認 ({turnCount}/5)</strong>
        <button type="button" onClick={onClose} aria-label="close">
          ×
        </button>
      </div>
      <p style={{ margin: "0.5rem 0" }}>{question}</p>
      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        rows={3}
        style={{ width: "100%" }}
        placeholder="自由回答…"
      />
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: 8,
          marginTop: 8,
        }}
      >
        <button type="button" onClick={skip} disabled={busy}>
          スキップ
        </button>
        <button
          type="button"
          onClick={submit}
          disabled={busy || !answer.trim()}
        >
          送信
        </button>
      </div>
    </div>
  );
}
