import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  setActive,
  updateSchema,
  createSchema,
  listSchemas,
} from "../api/schemas";
import { ExpectedValueType, SchemaFieldDoc } from "../types";
import { pk, TenantSel } from "../lib/tenant";
import { formatJst } from "../lib/jst";

interface Props {
  tenant: TenantSel;
}

const EMPTY: SchemaFieldDoc = {
  id: "",
  pk: "",
  sector: "",
  unit: "",
  field_name: "",
  description: "",
  expected_value_type: "string",
  example: "",
  ai_baseline_assumption: "",
  is_active: true,
  revision_id: 0,
  updated_at: new Date().toISOString(),
  updated_by: "shigeru.dev",
};

export default function SchemaList({ tenant }: Props): JSX.Element {
  const qc = useQueryClient();
  const partition = pk(tenant);

  // M-7: GET /schemas?sector=&unit=&active_only=false returns the current set
  // directly — no need to replay /schemas/history.
  const listQ = useQuery({
    queryKey: ["schemas-list", tenant],
    queryFn: () => listSchemas({ ...tenant, active_only: false }),
  });

  const current = (listQ.data ?? [])
    .slice()
    .sort((a, b) => a.field_name.localeCompare(b.field_name));

  const [draft, setDraft] = useState<SchemaFieldDoc | null>(null);

  const upsertMut = useMutation({
    mutationFn: async (d: SchemaFieldDoc) => {
      const filled: SchemaFieldDoc = {
        ...d,
        pk: partition,
        sector: tenant.sector,
        unit: tenant.unit,
      };
      return filled.revision_id === 0
        ? createSchema(filled)
        : updateSchema(filled.id, filled);
    },
    onSuccess: () => {
      setDraft(null);
      qc.invalidateQueries({ queryKey: ["schemas-list"] });
      qc.invalidateQueries({ queryKey: ["history"] });
    },
  });

  const toggleMut = useMutation({
    mutationFn: (d: SchemaFieldDoc) =>
      setActive(d.id, d.pk, !d.is_active, "toggled via admin UI"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schemas-list"] }),
  });

  return (
    <section>
      <h2>スキーマ一覧 ({partition})</h2>
      <div className="row">
        <button
          onClick={() =>
            setDraft({
              ...EMPTY,
              id: crypto.randomUUID(),
              pk: partition,
              sector: tenant.sector,
              unit: tenant.unit,
            })
          }
        >
          新規追加
        </button>
        <span className="muted">
          リジェクト率 (mock): <strong>12%</strong> / 直近7日
        </span>
      </div>

      {listQ.isLoading && <p>読み込み中…</p>}
      {listQ.isError && (
        <p style={{ color: "crimson" }}>取得失敗: {String(listQ.error)}</p>
      )}

      <table>
        <thead>
          <tr>
            <th>field_name</th>
            <th>type</th>
            <th>description</th>
            <th>example</th>
            <th>rev</th>
            <th>is_active</th>
            <th>updated_at (JST)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {current.map((d) => (
            <tr key={d.id}>
              <td>{d.field_name}</td>
              <td>{d.expected_value_type}</td>
              <td>{d.description}</td>
              <td>{d.example}</td>
              <td>{d.revision_id}</td>
              <td>
                <span
                  className={`badge ${d.is_active ? "active" : "inactive"}`}
                >
                  {d.is_active ? "active" : "inactive"}
                </span>
              </td>
              <td>{formatJst(d.updated_at)}</td>
              <td>
                <button onClick={() => setDraft(d)}>編集</button>{" "}
                <button onClick={() => toggleMut.mutate(d)}>
                  {d.is_active ? "無効化" : "再有効化"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {draft && (
        <Editor
          value={draft}
          onCancel={() => setDraft(null)}
          onSave={(d) => upsertMut.mutate(d)}
          saving={upsertMut.isPending}
        />
      )}
    </section>
  );
}

interface EditorProps {
  value: SchemaFieldDoc;
  onCancel: () => void;
  onSave: (v: SchemaFieldDoc) => void;
  saving: boolean;
}

function Editor({ value, onCancel, onSave, saving }: EditorProps): JSX.Element {
  const [v, setV] = useState<SchemaFieldDoc>(value);
  return (
    <div className="card">
      <h3>{v.revision_id === 0 ? "新規スキーマ" : `編集: ${v.field_name}`}</h3>
      <div className="col">
        <label>
          field_name
          <input
            value={v.field_name}
            onChange={(e) => setV({ ...v, field_name: e.target.value })}
          />
        </label>
        <label>
          description
          <textarea
            value={v.description}
            onChange={(e) => setV({ ...v, description: e.target.value })}
          />
        </label>
        <label>
          expected_value_type
          <select
            value={v.expected_value_type}
            onChange={(e) =>
              setV({
                ...v,
                expected_value_type: e.target.value as ExpectedValueType,
              })
            }
          >
            <option>string</option>
            <option>number</option>
            <option>enum</option>
            <option>structured</option>
          </select>
        </label>
        <label>
          example
          <input
            value={v.example}
            onChange={(e) => setV({ ...v, example: e.target.value })}
          />
        </label>
        <label>
          ai_baseline_assumption
          <textarea
            value={v.ai_baseline_assumption}
            onChange={(e) =>
              setV({ ...v, ai_baseline_assumption: e.target.value })
            }
          />
        </label>
      </div>
      <div className="row">
        <button disabled={saving} onClick={() => onSave(v)}>
          保存
        </button>
        <button onClick={onCancel}>キャンセル</button>
      </div>
    </div>
  );
}
