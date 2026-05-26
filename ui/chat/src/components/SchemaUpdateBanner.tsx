import { SchemaUpdateBanner } from "../types";
import { ackBanner } from "../api/turn";

interface Props {
  banner: SchemaUpdateBanner;
  turnId: string;
  sector: string;
  unit: string;
  userId: string;
  onAck: () => void;
}

export function SchemaUpdateBannerView({
  banner,
  turnId,
  sector,
  unit,
  userId,
  onAck,
}: Props) {
  return (
    <div
      role="status"
      style={{
        background: "#fff7e6",
        border: "1px solid #f0b73b",
        padding: "0.75rem 1rem",
        borderRadius: 6,
        margin: "0.5rem 0",
      }}
    >
      <strong>
        schema 更新が {banner.unseen_revision_ids.length} 件あります
      </strong>
      <div style={{ fontSize: 13, margin: "0.25rem 0" }}>
        {banner.changed_fields_summary}
      </div>
      <a href={banner.history_url} target="_blank" rel="noreferrer">
        履歴を見る
      </a>
      <button
        type="button"
        style={{ marginLeft: "1rem" }}
        onClick={async () => {
          await ackBanner(turnId, sector, unit, userId);
          onAck();
        }}
      >
        確認
      </button>
    </div>
  );
}
