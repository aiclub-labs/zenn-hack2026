import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  Badge,
  Button,
  Checkbox,
  Field,
  Input,
  Spinner,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  ArrowImport24Regular,
  CheckmarkCircle20Filled,
  DocumentMultiple24Regular,
  Warning24Regular,
} from "@fluentui/react-icons";
import { bulkImport, getHistory } from "../api/schemas";
import { TenantSel } from "../lib/tenant";

interface Props {
  target: TenantSel;
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
  notice: {
    display: "flex",
    alignItems: "flex-start",
    ...shorthands.gap(tokens.spacingHorizontalS),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    backgroundColor: tokens.colorNeutralBackground2,
    color: tokens.colorNeutralForeground2,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: tokens.fontSizeBase200,
    lineHeight: tokens.lineHeightBase300,
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalL),
    boxShadow: tokens.shadow2,
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  cardTitle: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  formGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    ...shorthands.gap(tokens.spacingHorizontalL),
  },
  formGroup: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  formGroupLabel: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    fontWeight: tokens.fontWeightSemibold,
  },
  actionsRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  previewList: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
    listStyleType: "none",
    paddingInlineStart: 0,
    marginBlock: 0,
    maxHeight: "240px",
    overflowY: "auto",
  },
  previewItem: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
    ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
  },
  successBar: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    backgroundColor: tokens.colorPaletteGreenBackground1,
    color: tokens.colorPaletteGreenForeground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: tokens.fontSizeBase300,
  },
  errorBar: {
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    backgroundColor: tokens.colorPaletteRedBackground1,
    color: tokens.colorPaletteRedForeground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: tokens.fontSizeBase200,
  },
});

export default function SchemaImport({ target }: Props): JSX.Element {
  const styles = useStyles();
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

  const distinctFields = Array.from(
    new Set((preview.data ?? []).map((e) => e.schema_field_id)),
  );

  return (
    <section className={styles.root}>
      <div className={styles.headerRow}>
        <div className={styles.title}>
          <span className={styles.titleText}>一括インポート</span>
          <span className={styles.subtitle}>
            Req 3 — 既存テナントのスキーマを横展開
          </span>
        </div>
        <span className={styles.tenantChip}>
          → {target.sector}#{target.unit}
        </span>
      </div>

      <div className={styles.notice}>
        <Warning24Regular />
        <div>
          コピー元テナントの <code>is_active=true</code>{" "}
          のスキーマのみを対象テナントへ複製します。 revision_id=1
          にリセット、partition_key を置換、監査ログに <code>create</code>{" "}
          として記録されます。
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardTitle}>
          <ArrowImport24Regular /> インポート設定
        </div>
        <div className={styles.formGrid}>
          <div className={styles.formGroup}>
            <span className={styles.formGroupLabel}>コピー元</span>
            <Field label="sector">
              <Input
                value={source.sector}
                onChange={(_, d) => setSource({ ...source, sector: d.value })}
              />
            </Field>
            <Field label="unit">
              <Input
                value={source.unit}
                onChange={(_, d) => setSource({ ...source, unit: d.value })}
              />
            </Field>
          </div>
          <div className={styles.formGroup}>
            <span className={styles.formGroupLabel}>コピー先</span>
            <Field label="sector" hint="画面上部のテナント選択で変更">
              <Input value={target.sector} disabled />
            </Field>
            <Field label="unit">
              <Input value={target.unit} disabled />
            </Field>
          </div>
          <div className={styles.formGroup}>
            <span className={styles.formGroupLabel}>オプション</span>
            <Checkbox
              checked={dryRun}
              onChange={(_, d) => setDryRun(d.checked === true)}
              label="Dry-run プレビュー (実際には書き込まない)"
            />
          </div>
        </div>
        <div className={styles.actionsRow}>
          <span className={styles.subtitle}>
            実行ボタンで実インポート (dry-run でも有効)。
          </span>
          <Button
            appearance="primary"
            icon={
              mut.isPending ? <Spinner size="tiny" /> : <ArrowImport24Regular />
            }
            disabled={mut.isPending}
            onClick={() => mut.mutate()}
          >
            {mut.isPending ? "インポート中…" : "実行"}
          </Button>
        </div>
      </div>

      {dryRun && (
        <div className={styles.card}>
          <div className={styles.cardTitle}>
            <DocumentMultiple24Regular />
            プレビュー
            <Badge appearance="tint" color="brand">
              候補 {distinctFields.length} 件
            </Badge>
          </div>
          {preview.isLoading ? (
            <Spinner size="small" label="読み込み中…" />
          ) : distinctFields.length === 0 ? (
            <span className={styles.subtitle}>
              コピー元テナントにアクティブなスキーマが見つかりません。
            </span>
          ) : (
            <ul className={styles.previewList}>
              {distinctFields.map((id) => (
                <li key={id} className={styles.previewItem}>
                  <CheckmarkCircle20Filled
                    color={tokens.colorPaletteGreenForeground2}
                  />
                  <code>{id}</code>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {mut.isSuccess && (
        <div className={styles.successBar}>
          <CheckmarkCircle20Filled />
          インポート完了: {mut.data.length} 件
        </div>
      )}
      {mut.isError && (
        <div className={styles.errorBar}>失敗: {String(mut.error)}</div>
      )}
    </section>
  );
}
