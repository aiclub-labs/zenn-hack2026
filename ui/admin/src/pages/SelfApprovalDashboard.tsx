import { TenantSel } from "../lib/tenant";

interface Props {
  tenant: TenantSel;
}

// Req 9.9: 自己承認 KPI。今日はスタブ（明日 reviews API 接続）。
export default function SelfApprovalDashboard({ tenant }: Props): JSX.Element {
  const mock = {
    self_approval_rate: 0.18,
    avg_weight_final: 0.62,
    pending_count: 7,
    approved_24h: 14,
    rejected_24h: 2,
  };
  return (
    <section>
      <h2>
        自己承認ダッシュボード ({tenant.sector}#{tenant.unit})
      </h2>
      <p className="muted">Req 9.9 stub — reviews API 結線は 5/26 予定</p>
      <div className="row">
        <Kpi
          label="自己承認率"
          value={`${(mock.self_approval_rate * 100).toFixed(1)}%`}
        />
        <Kpi
          label="平均 weight_final"
          value={mock.avg_weight_final.toFixed(2)}
        />
        <Kpi label="pending" value={String(mock.pending_count)} />
        <Kpi label="承認 24h" value={String(mock.approved_24h)} />
        <Kpi label="却下 24h" value={String(mock.rejected_24h)} />
      </div>
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="card" style={{ minWidth: 140 }}>
      <div className="muted">{label}</div>
      <div style={{ fontSize: 22, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
