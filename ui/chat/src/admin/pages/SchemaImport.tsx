import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { bulkImport, getHistory } from "../api/schemas";
import { TenantSel } from "../lib/tenant";

interface Props {
  target: TenantSel;
}

// Req 3: cross-tenant bulk import. Dry-run preview reuses history endpoint
// against the source tenant to list current active fields.
export default function SchemaImport({ target }: Props): JSX.Element {
  const qc = useQueryClient();
  const [source, setSource] = useState<TenantSel>({
    sector: "demo",
    unit: "team-b",
  });
  const [dryRun, setDryRun] = useState(true);

  const preview = useQuery({
    queryKey: ["history", source, "preview"],
    queryFn: () => getHistory({ ...source, limit: 500 }),
    enabled: dryRun,
  });

  const mut = useMutation({
    mutationFn: () =>
      bulkImport({
        source_sector: source.sector,
        source_unit: source.unit,
        target_sector: target.sector,
        target_unit: target.unit,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["history-as-list"] }),
  });

  const distinctFields = new Set(
    (preview.data ?? []).map((e) => e.schema_field_id),
  );

  return (
    <section>
      <h2>一括インポート (Req 3)</h2>
      <p className="muted">
        コピー元テナントの <code>is_active=true</code>{" "}
        なスキーマのみを対象テナントへ複製します。
        <br />
        revision_id=1 にリセット、partition_key を置換、監査ログに{" "}
        <code>create</code> として記録。
      </p>

      <div className="row">
        <div className="col">
          <label>
            コピー元 sector
            <input
              value={source.sector}
              onChange={(e) => setSource({ ...source, sector: e.target.value })}
            />
          </label>
          <label>
            コピー元 unit
            <input
              value={source.unit}
              onChange={(e) => setSource({ ...source, unit: e.target.value })}
            />
          </label>
        </div>
        <div className="col">
          <label>
            コピー先 sector
            <input value={target.sector} disabled />
          </label>
          <label>
            コピー先 unit
            <input value={target.unit} disabled />
          </label>
          <span className="muted">画面上部の選択を変更</span>
        </div>
        <div className="col">
          <label>
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
            />{" "}
            Dry-run プレビュー
          </label>
          <button disabled={mut.isPending} onClick={() => mut.mutate()}>
            実行
          </button>
        </div>
      </div>

      {dryRun && (
        <div className="card">
          <strong>プレビュー: 候補 {distinctFields.size} 件</strong>
          <ul>
            {[...distinctFields].map((id) => (
              <li key={id}>
                <code>{id}</code>
              </li>
            ))}
          </ul>
        </div>
      )}

      {mut.isSuccess && (
        <div className="card">
          <strong>インポート完了:</strong> {mut.data.length} 件
        </div>
      )}
      {mut.isError && (
        <p style={{ color: "crimson" }}>失敗: {String(mut.error)}</p>
      )}
    </section>
  );
}
