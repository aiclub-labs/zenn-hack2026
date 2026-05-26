import { useState } from "react";

interface Props {
  conflicts: { schema_field_id: string; alt_count: number }[];
}

export function ConflictInline({ conflicts }: Props) {
  const [open, setOpen] = useState(false);
  if (conflicts.length === 0) return null;
  const total = conflicts.reduce((a, c) => a + c.alt_count, 0);
  return (
    <div
      style={{
        background: "#eef6ff",
        border: "1px dashed #5aa0e0",
        padding: "0.5rem 0.75rem",
        borderRadius: 6,
        margin: "0.25rem 0",
        fontSize: 13,
      }}
    >
      <button type="button" onClick={() => setOpen((v) => !v)}>
        他に {total} 件の異なる見解あり ({open ? "閉じる" : "詳細"})
      </button>
      {open && (
        <ul style={{ marginTop: 6, paddingLeft: 18 }}>
          {conflicts.map((c) => (
            <li key={c.schema_field_id}>
              {c.schema_field_id}: {c.alt_count} viewpoints
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
