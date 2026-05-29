import { useEffect, useState } from "react";
import { FormalizationTicket } from "../types";
import { decideConflict, listConflictReviews } from "../api/reviews";
import { WeightBreakdown } from "../components/WeightBreakdown";

export function ConflictQueue() {
  const [tickets, setTickets] = useState<FormalizationTicket[]>([]);
  const [selected, setSelected] = useState<FormalizationTicket | null>(null);

  async function load() {
    setTickets(await listConflictReviews());
  }
  useEffect(() => {
    load();
  }, []);

  async function decide(
    t: FormalizationTicket,
    d: "adopt_new" | "keep_existing" | "coexist",
  ) {
    const [sector, unit] = t.pk.split("#");
    await decideConflict(t.id, sector ?? "", unit ?? "", d);
    setSelected(null);
    await load();
  }

  return (
    <div style={{ padding: "1rem", fontFamily: "sans-serif" }}>
      <h2>競合レビュー (conflict_pending)</h2>
      {tickets.length === 0 && <p>競合はありません。</p>}
      <ul style={{ listStyle: "none", padding: 0 }}>
        {tickets.map((t) => (
          <li
            key={t.id}
            style={{
              border: "1px solid #e5e7eb",
              padding: "0.75rem",
              borderRadius: 6,
              marginBottom: 8,
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            <span>{t.id.slice(0, 8)}</span>
            <WeightBreakdown
              a={t.weight_a}
              b={t.weight_b}
              c={t.weight_c}
              final={t.weight_final}
            />
            <button
              style={{ marginLeft: "auto" }}
              onClick={() => setSelected(t)}
            >
              比較
            </button>
          </li>
        ))}
      </ul>
      {selected && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              background: "#fff",
              padding: "1.5rem",
              borderRadius: 8,
              width: "min(720px, 92vw)",
              maxHeight: "92vh",
              overflowY: "auto",
            }}
          >
            <h3>並列比較: {selected.id.slice(0, 8)}</h3>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: 16,
              }}
            >
              <section
                style={{ background: "#eff6ff", padding: 12, borderRadius: 6 }}
              >
                <h4>新規候補</h4>
                <p>hearout: {selected.hearout_id.slice(0, 8)}</p>
                <p>weight: {selected.weight_final.toFixed(2)}</p>
              </section>
              <section
                style={{ background: "#fef3c7", padding: 12, borderRadius: 6 }}
              >
                <h4>既存 (WT-D 連携 TODO)</h4>
                <p>citation_audit_log preview …</p>
              </section>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button onClick={() => decide(selected, "adopt_new")}>
                新規採用
              </button>
              <button onClick={() => decide(selected, "keep_existing")}>
                既存維持
              </button>
              <button onClick={() => decide(selected, "coexist")}>
                両方残す
              </button>
              <button
                onClick={() => setSelected(null)}
                style={{ marginLeft: "auto" }}
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
