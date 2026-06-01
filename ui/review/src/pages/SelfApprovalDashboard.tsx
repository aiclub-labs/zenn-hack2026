import { useEffect, useState } from "react";
import { SelfApprovalInfo } from "../types";
import { getSelfApproval } from "../api/reviews";

export function SelfApprovalDashboard() {
  const [info, setInfo] = useState<SelfApprovalInfo | null>(null);
  useEffect(() => {
    getSelfApproval()
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);
  if (!info) return <p style={{ padding: "1rem" }}>読み込み中…</p>;
  const pct = (info.rate_7d * 100).toFixed(1);
  const thr = (info.threshold * 100).toFixed(0);
  return (
    <div style={{ padding: "1rem", fontFamily: "sans-serif" }}>
      <h2>自己承認率 (直近7日)</h2>
      <p style={{ fontSize: 32, margin: 0 }}>
        {pct}%
        {info.warn && (
          <span style={{ color: "#b91c1c", fontSize: 14, marginLeft: 12 }}>
            ⚠ 閾値 {thr}% を超過
          </span>
        )}
      </p>
      <p style={{ color: "#666" }}>
        reviewer: {info.reviewer_id} / 閾値: {thr}%
      </p>
      <p style={{ fontSize: 13 }}>
        Req 9.9: 自己承認が
        {thr}% を超えた場合は別レビュアーへの委任を検討してください。
      </p>
    </div>
  );
}
