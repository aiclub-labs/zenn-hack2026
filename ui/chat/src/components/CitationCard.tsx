import { useState } from "react";
import { CitationRef, CitationDetail } from "../types";
import { getCitation } from "../api/citations";

interface Props {
  citation: CitationRef;
  sector: string;
  unit: string;
}

export function CitationCard({ citation, sector, unit }: Props) {
  const [detail, setDetail] = useState<CitationDetail | null>(null);
  const [open, setOpen] = useState(false);

  async function toggle() {
    if (!detail) {
      setDetail(await getCitation(citation.record_id, sector, unit));
    }
    setOpen((v) => !v);
  }

  const weightPct = Math.min(100, Math.max(0, citation.weight * 100));

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 6,
        padding: "0.5rem 0.75rem",
        margin: "0.25rem 0",
        background: citation.superseded_by ? "#fff4f4" : "#fafafa",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <button
          type="button"
          onClick={toggle}
          style={{ flex: 1, textAlign: "left" }}
        >
          [{citation.schema_field_id}] {citation.record_id.slice(0, 8)}
        </button>
        <div
          aria-label={`weight ${weightPct.toFixed(0)}%`}
          style={{
            width: 60,
            height: 8,
            background: "#eee",
            borderRadius: 4,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${weightPct}%`,
              height: "100%",
              background: "#3b82f6",
            }}
          />
        </div>
      </div>
      {detail?.superseded_banner && (
        <div style={{ color: "#b91c1c", fontSize: 12, marginTop: 4 }}>
          ⚠ {detail.superseded_banner}
        </div>
      )}
      {open && detail && (
        <div style={{ fontSize: 13, marginTop: 6, whiteSpace: "pre-wrap" }}>
          {detail.content}
        </div>
      )}
    </div>
  );
}
