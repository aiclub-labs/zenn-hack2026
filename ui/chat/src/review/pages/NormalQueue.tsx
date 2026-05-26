import { useEffect, useState } from "react";
import { FormalizationTicket } from "../types";
import {
  decideReview,
  getPriorityMode,
  listReviews,
  lockReview,
  unlockReview,
} from "../api/reviews";
import { WeightBreakdown } from "../components/WeightBreakdown";
import { LockBadge } from "../components/LockBadge";
import { PriorityModeBanner } from "../components/PriorityModeBanner";

function ageMin(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
}

export function NormalQueue() {
  const [tickets, setTickets] = useState<FormalizationTicket[]>([]);
  const [selected, setSelected] = useState<FormalizationTicket | null>(null);
  const [priorityOnly, setPriorityOnly] = useState(false);
  const [pmActive, setPmActive] = useState(false);
  const [pmMedian, setPmMedian] = useState(0);
  const [pmThreshold, setPmThreshold] = useState(180);

  async function load() {
    setTickets(await listReviews(priorityOnly));
    const pm = await getPriorityMode();
    setPmActive(pm.active);
    setPmMedian(pm.median_sec);
    setPmThreshold(pm.threshold_sec);
  }

  useEffect(() => {
    load();
  }, [priorityOnly]);

  async function onLock(t: FormalizationTicket) {
    await lockReview(t.id);
    await load();
  }
  async function onUnlock(t: FormalizationTicket) {
    await unlockReview(t.id);
    await load();
  }
  async function onDecide(
    t: FormalizationTicket,
    decision: "approve" | "edit" | "reject",
  ) {
    const [sector, unit] = t.pk.split("#");
    await decideReview(t.id, sector ?? "", unit ?? "", decision);
    setSelected(null);
    await load();
  }

  return (
    <div style={{ padding: "1rem", fontFamily: "sans-serif" }}>
      <h2>レビュー待ちキュー</h2>
      <PriorityModeBanner
        active={pmActive}
        medianSec={pmMedian}
        thresholdSec={pmThreshold}
        priorityOnly={priorityOnly}
        onToggle={setPriorityOnly}
      />
      {tickets.length === 0 && <p>キューは空です。</p>}
      <table
        style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}
      >
        <thead>
          <tr style={{ background: "#f3f4f6" }}>
            <th style={{ textAlign: "left", padding: 6 }}>ID</th>
            <th>5W1H 概要</th>
            <th>weight</th>
            <th>TJ</th>
            <th>lock</th>
            <th>age</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.id} style={{ borderTop: "1px solid #eee" }}>
              <td style={{ padding: 6 }}>{t.id.slice(0, 8)}</td>
              <td>hearout: {t.hearout_id.slice(0, 8)}</td>
              <td>
                <WeightBreakdown
                  a={t.weight_a}
                  b={t.weight_b}
                  c={t.weight_c}
                  final={t.weight_final}
                />
              </td>
              <td>
                {t.tj_verdict && (
                  <span
                    style={{
                      padding: "2px 6px",
                      borderRadius: 4,
                      background:
                        t.tj_verdict === "supported" ? "#bbf7d0" : "#fde68a",
                      fontSize: 12,
                    }}
                  >
                    {t.tj_verdict}
                  </span>
                )}
              </td>
              <td>
                <LockBadge
                  lockedBy={t.locked_by}
                  lockExpiresAt={t.lock_expires_at}
                />
              </td>
              <td>{ageMin(t.created_at)}分</td>
              <td>
                <button onClick={() => setSelected(t)}>開く</button>
                {!t.locked_by ? (
                  <button onClick={() => onLock(t)}>ロック</button>
                ) : (
                  <button onClick={() => onUnlock(t)}>解除</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {selected && (
        <aside
          style={{
            position: "fixed",
            right: 0,
            top: 0,
            bottom: 0,
            width: 360,
            background: "#fff",
            borderLeft: "1px solid #ccc",
            padding: "1rem",
            overflowY: "auto",
          }}
        >
          <h3>ticket {selected.id.slice(0, 8)}</h3>
          <p>hearout: {selected.hearout_id}</p>
          <p>
            weight: A={selected.weight_a.toFixed(2)} B=
            {selected.weight_b.toFixed(2)} C={selected.weight_c.toFixed(2)} →{" "}
            {selected.weight_final.toFixed(2)}
          </p>
          <p>TJ: {selected.tj_verdict ?? "n/a"}</p>
          <p>
            関連 turn: <code>(hearoutから辿る — WT-D連携TODO)</code>
          </p>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button onClick={() => onDecide(selected, "approve")}>承認</button>
            <button onClick={() => onDecide(selected, "edit")}>編集</button>
            <button onClick={() => onDecide(selected, "reject")}>却下</button>
            <button
              onClick={() => setSelected(null)}
              style={{ marginLeft: "auto" }}
            >
              閉じる
            </button>
          </div>
        </aside>
      )}
    </div>
  );
}
