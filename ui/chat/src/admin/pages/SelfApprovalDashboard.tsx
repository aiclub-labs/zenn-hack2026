import {
  Badge,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  CheckmarkCircle24Filled,
  ClockArrowDownload24Regular,
  HourglassHalf24Regular,
  ShieldCheckmark24Regular,
  Warning24Regular,
} from "@fluentui/react-icons";
import { TenantSel } from "../lib/tenant";

interface Props {
  tenant: TenantSel;
}

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  headerRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  title: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXXS),
  },
  titleText: {
    fontSize: tokens.fontSizeBase600,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
    lineHeight: tokens.lineHeightBase600,
  },
  subtitle: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  tenantChip: {
    display: "inline-flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalXS),
    ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
    backgroundColor: tokens.colorNeutralBackground3,
    color: tokens.colorNeutralForeground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
  },
  kpiRow: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  kpiCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalL),
    boxShadow: tokens.shadow2,
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  kpiHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  kpiLabel: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  kpiValue: {
    fontSize: tokens.fontSizeHero700,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
    lineHeight: tokens.lineHeightHero700,
  },
  kpiHint: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  primaryCard: {
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
  },
  notice: {
    display: "flex",
    alignItems: "flex-start",
    ...shorthands.gap(tokens.spacingHorizontalS),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    backgroundColor: tokens.colorPaletteYellowBackground1,
    color: tokens.colorPaletteYellowForeground1,
    ...shorthands.border("1px", "solid", tokens.colorPaletteYellowBorderActive),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: tokens.fontSizeBase200,
  },
});

interface KpiProps {
  label: string;
  value: string;
  hint?: string;
  icon: JSX.Element;
  tone?: "brand" | "neutral";
  badge?: { text: string; appearance: "filled" | "tint" | "outline" };
}

function Kpi({
  label,
  value,
  hint,
  icon,
  tone = "neutral",
  badge,
}: KpiProps): JSX.Element {
  const styles = useStyles();
  const className =
    tone === "brand"
      ? `${styles.kpiCard} ${styles.primaryCard}`
      : styles.kpiCard;
  return (
    <div className={className}>
      <div className={styles.kpiHeader}>
        <span className={styles.kpiLabel}>{label}</span>
        {icon}
      </div>
      <div className={styles.kpiValue}>{value}</div>
      {hint && <div className={styles.kpiHint}>{hint}</div>}
      {badge && (
        <Badge appearance={badge.appearance} color="informative">
          {badge.text}
        </Badge>
      )}
    </div>
  );
}

export default function SelfApprovalDashboard({ tenant }: Props): JSX.Element {
  const styles = useStyles();
  const mock = {
    self_approval_rate: 0.18,
    avg_weight_final: 0.62,
    pending_count: 7,
    approved_24h: 14,
    rejected_24h: 2,
  };
  return (
    <section className={styles.root}>
      <div className={styles.headerRow}>
        <div className={styles.title}>
          <span className={styles.titleText}>自己承認ダッシュボード</span>
          <span className={styles.subtitle}>
            Req 9.9 — 自己承認率と直近24h のレビュー処理量
          </span>
        </div>
        <span className={styles.tenantChip}>
          {tenant.sector}#{tenant.unit}
        </span>
      </div>

      <div className={styles.notice}>
        <Warning24Regular />
        <div>
          現在表示中の数値は <code>mock</code> 値です。reviews API
          結線完了後に実集計値へ切替わります。
        </div>
      </div>

      <div className={styles.kpiRow}>
        <Kpi
          label="自己承認率"
          value={`${(mock.self_approval_rate * 100).toFixed(1)}%`}
          hint="weight_final ≥ 自動承認 threshold"
          icon={<ShieldCheckmark24Regular />}
          tone="brand"
        />
        <Kpi
          label="平均 weight_final"
          value={mock.avg_weight_final.toFixed(2)}
          hint="A×B×C の合成スコア"
          icon={<CheckmarkCircle24Filled />}
        />
        <Kpi
          label="pending"
          value={String(mock.pending_count)}
          hint="現在キュー滞留中"
          icon={<HourglassHalf24Regular />}
        />
        <Kpi
          label="承認 24h"
          value={String(mock.approved_24h)}
          hint="直近 24 時間に approve"
          icon={<CheckmarkCircle24Filled />}
        />
        <Kpi
          label="却下 24h"
          value={String(mock.rejected_24h)}
          hint="直近 24 時間に reject"
          icon={<ClockArrowDownload24Regular />}
        />
      </div>
    </section>
  );
}
