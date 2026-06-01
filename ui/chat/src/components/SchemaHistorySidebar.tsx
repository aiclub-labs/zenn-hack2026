import { useEffect, useState } from "react";
import { api } from "../api/client";

interface HistoryEntry {
  id: string;
  revision_id: number;
  change_type: string;
  changed_at: string;
}

interface Props {
  sector: string;
  unit: string;
}

export function SchemaHistorySidebar({ sector, unit }: Props) {
  const [items, setItems] = useState<HistoryEntry[]>([]);
  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get<HistoryEntry[]>("/schemas/history", {
          params: { sector, unit, limit: 20 },
        });
        setItems(data);
      } catch {
        setItems([]);
      }
    })();
  }, [sector, unit]);
  return (
    <aside
      style={{
        borderLeft: "1px solid #eee",
        padding: "0.75rem",
        minWidth: 220,
        fontSize: 13,
      }}
    >
      <h3 style={{ fontSize: 14, margin: "0 0 .5rem" }}>最近の schema 変更</h3>
      {items.length === 0 && <em>履歴なし</em>}
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {items.map((e) => (
          <li
            key={e.id}
            style={{ padding: "4px 0", borderBottom: "1px solid #f3f3f3" }}
          >
            <code>r{e.revision_id}</code> {e.change_type}
            <div style={{ color: "#666", fontSize: 11 }}>
              {new Date(e.changed_at).toLocaleString("ja-JP", {
                timeZone: "Asia/Tokyo",
              })}
            </div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
