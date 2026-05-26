import { useQuery } from "@tanstack/react-query";
import {
  Badge,
  Skeleton,
  SkeletonItem,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { History24Regular } from "@fluentui/react-icons";
import { getHistory } from "../api/schemas";
import { TenantSel } from "../lib/tenant";
import { formatJst } from "../lib/jst";

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
  tableCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow2,
    overflowX: "auto",
  },
  fieldCell: {
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
  },
  diffCell: {
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
    whiteSpace: "pre-wrap",
    maxWidth: "360px",
  },
  reasonCell: {
    color: tokens.colorNeutralForeground3,
    maxWidth: "200px",
    whiteSpace: "normal",
  },
  emptyState: {
    ...shorthands.padding(tokens.spacingVerticalXXL),
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  errorBar: {
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    backgroundColor: tokens.colorPaletteRedBackground1,
    color: tokens.colorPaletteRedForeground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: tokens.fontSizeBase200,
  },
  notice: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
});

function changeBadgeColor(
  changeType: string,
): "success" | "warning" | "danger" | "informative" {
  switch (changeType) {
    case "create":
      return "success";
    case "update":
      return "informative";
    case "deactivate":
      return "warning";
    case "reactivate":
      return "success";
    default:
      return "informative";
  }
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

export default function SchemaHistory({ tenant }: Props): JSX.Element {
  const styles = useStyles();
  const q = useQuery({
    queryKey: ["history", tenant],
    queryFn: () => getHistory({ ...tenant, limit: 200 }),
  });

  const rows = q.data ?? [];

  return (
    <section className={styles.root}>
      <div className={styles.headerRow}>
        <div className={styles.title}>
          <span className={styles.titleText}>変更履歴</span>
          <span className={styles.subtitle}>
            物理削除は不可。全リビジョンの監査ログを保持します。
          </span>
        </div>
        <span className={styles.tenantChip}>
          {tenant.sector}#{tenant.unit}
        </span>
      </div>

      {q.isError && (
        <div className={styles.errorBar}>取得失敗: {String(q.error)}</div>
      )}

      <div className={styles.tableCard}>
        {q.isLoading ? (
          <div style={{ padding: tokens.spacingVerticalL }}>
            <Skeleton>
              <SkeletonItem
                size={16}
                style={{ marginBottom: tokens.spacingVerticalS }}
              />
              <SkeletonItem
                size={16}
                style={{ marginBottom: tokens.spacingVerticalS }}
              />
              <SkeletonItem size={16} />
            </Skeleton>
          </div>
        ) : rows.length === 0 ? (
          <div className={styles.emptyState}>
            <History24Regular fontSize={32} />
            <div>このテナントには変更履歴がまだありません。</div>
          </div>
        ) : (
          <Table size="medium">
            <TableHeader>
              <TableRow>
                <TableHeaderCell>changed_at (JST)</TableHeaderCell>
                <TableHeaderCell>field_id</TableHeaderCell>
                <TableHeaderCell>rev</TableHeaderCell>
                <TableHeaderCell>change_type</TableHeaderCell>
                <TableHeaderCell>diff</TableHeaderCell>
                <TableHeaderCell>reason</TableHeaderCell>
                <TableHeaderCell>changed_by</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((e) => (
                <TableRow key={e.id}>
                  <TableCell>{formatJst(e.changed_at)}</TableCell>
                  <TableCell className={styles.fieldCell}>
                    {e.schema_field_id}
                  </TableCell>
                  <TableCell>
                    <Badge appearance="tint" color="brand">
                      rev{e.revision_id}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      appearance="filled"
                      color={changeBadgeColor(e.change_type)}
                    >
                      {e.change_type}
                    </Badge>
                  </TableCell>
                  <TableCell className={styles.diffCell}>
                    {renderDiff(e.diff)}
                  </TableCell>
                  <TableCell className={styles.reasonCell}>
                    {e.reason ?? ""}
                  </TableCell>
                  <TableCell className={styles.fieldCell}>
                    {e.changed_by}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </section>
  );
}
