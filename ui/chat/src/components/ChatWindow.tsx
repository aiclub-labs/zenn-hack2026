import { ChatMessage } from "../types";
import { CitationCard } from "./CitationCard";

interface Props {
  messages: ChatMessage[];
  sector: string;
  unit: string;
}

export function ChatWindow({ messages, sector, unit }: Props) {
  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "1rem",
        background: "#fff",
      }}
    >
      {messages.map((m, i) => (
        <div
          key={i}
          style={{
            margin: "0.75rem 0",
            display: "flex",
            justifyContent: m.role === "user" ? "flex-end" : "flex-start",
          }}
        >
          <div
            style={{
              maxWidth: "75%",
              background: m.role === "user" ? "#e0f2fe" : "#f3f4f6",
              padding: "0.5rem 0.75rem",
              borderRadius: 8,
            }}
          >
            <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
            {typeof m.selfCriticScore === "number" && (
              <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>
                self-critic: {m.selfCriticScore.toFixed(1)} / 10
              </div>
            )}
            {m.citations && m.citations.length > 0 && (
              <div style={{ marginTop: 6 }}>
                {m.citations.map((c) => (
                  <CitationCard
                    key={c.record_id}
                    citation={c}
                    sector={sector}
                    unit={unit}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
