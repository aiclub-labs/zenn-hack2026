import { useQuery } from "@tanstack/react-query";
import { getHistory } from "../api/schemas";
import { TenantSel } from "../lib/tenant";
import { formatJst } from "../lib/jst";

interface Props {
  tenant: TenantSel;
}

// Req 2.6: read-only audit history.
export default function SchemaHistory({ tenant }: Props): JSX.Element {
  const q = useQuery({
    queryKey: ["history", tenant],
    queryFn: () => getHistory({ ...tenant, limit: 200 }),
  });

  return (
    <section>
      <h2>
        変更履歴 ({tenant.sector}#{tenant.unit})
      </h2>
      <p className="muted">物理削除は不可。すべての過去リビジョンを保持。</p>

      {q.isLoading && <p>読み込み中…</p>}
      {q.isError && (
        <p style={{ color: "crimson" }}>取得失敗: {String(q.error)}</p>
      )}

      <table>
        <thead>
          <tr>
            <th>changed_at (JST)</th>
            <th>field_id</th>
            <th>rev</th>
            <th>change_type</th>
            <th>diff</th>
            <th>reason</th>
            <th>changed_by</th>
          </tr>
        </thead>
        <tbody>
          {(q.data ?? []).map((e) => (
            <tr key={e.id}>
              <td>{formatJst(e.changed_at)}</td>
              <td>{e.schema_field_id}</td>
              <td>{e.revision_id}</td>
              <td>{e.change_type}</td>
              <td className="diff">{renderDiff(e.diff)}</td>
              <td>{e.reason ?? ""}</td>
              <td>{e.changed_by}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function renderDiff(
  diff: Record<string, { before?: unknown; after?: unknown }>,
): string {
  const lines: string[] = [];
  for (const [k, v] of Object.entries(diff)) {
    lines.push(`${k}: ${fmt(v.before)} → ${fmt(v.after)}`);
  }
  return lines.join("\n");
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "∅";
  if (typeof v === "string") return JSON.stringify(v);
  return String(v);
}
