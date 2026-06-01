interface Props {
  active: boolean;
  medianSec: number;
  thresholdSec: number;
  priorityOnly: boolean;
  onToggle: (v: boolean) => void;
}

export function PriorityModeBanner({
  active,
  medianSec,
  thresholdSec,
  priorityOnly,
  onToggle,
}: Props) {
  if (!active) return null;
  return (
    <div
      style={{
        background: "#fee2e2",
        border: "1px solid #fca5a5",
        padding: "0.5rem 0.75rem",
        borderRadius: 6,
        margin: "0.5rem 0",
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      <strong>レビュー中央値 {(medianSec / 60).toFixed(1)} 分</strong>
      <span style={{ fontSize: 12 }}>
        (閾値 {(thresholdSec / 60).toFixed(0)} 分)
      </span>
      <label style={{ marginLeft: "auto" }}>
        <input
          type="checkbox"
          checked={priorityOnly}
          onChange={(e) => onToggle(e.target.checked)}
        />
        優先 3 件のみ表示
      </label>
    </div>
  );
}
