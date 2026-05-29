import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  Badge,
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Dropdown,
  Field,
  Input,
  Option,
  Skeleton,
  SkeletonItem,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Textarea,
  Tooltip,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  Add24Regular,
  ArrowSync20Regular,
  CheckmarkCircle20Filled,
  DismissCircle20Filled,
  Edit20Regular,
  PauseCircle20Regular,
  PlayCircle20Regular,
  Search20Regular,
} from "@fluentui/react-icons";
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
    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  kpiCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    boxShadow: tokens.shadow2,
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
  },
  kpiLabel: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  kpiValue: {
    fontSize: tokens.fontSizeBase600,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
    lineHeight: tokens.lineHeightBase600,
  },
  kpiHint: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  toolbarLeft: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  searchField: {
    minWidth: "240px",
  },
  tableCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow2,
    overflowX: "auto",
  },
  fieldName: {
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
  },
  descCell: {
    maxWidth: "320px",
    color: tokens.colorNeutralForeground2,
    whiteSpace: "normal",
    lineHeight: tokens.lineHeightBase200,
  },
  exampleCell: {
    maxWidth: "240px",
    color: tokens.colorNeutralForeground3,
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
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
  editorFields: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
});

export default function SchemaList({ tenant }: Props): JSX.Element {
  const s = useStyles();
  const qc = useQueryClient();
  const partition = pk(tenant);

  const listQ = useQuery({
    queryKey: ["schemas-list", tenant],
    queryFn: () => listSchemas({ ...tenant, active_only: false }),
  });

  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState<SchemaFieldDoc | null>(null);

  const all = listQ.data ?? [];
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const base = all
      .slice()
      .sort((a, b) => a.field_name.localeCompare(b.field_name));
    if (!q) return base;
    return base.filter(
      (d) =>
        d.field_name.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q) ||
        d.example.toLowerCase().includes(q),
    );
  }, [all, query]);

  const stats = useMemo(() => {
    const total = all.length;
    const active = all.filter((d) => d.is_active).length;
    const revised = all.filter((d) => d.revision_id > 1).length;
    const latest = all
      .slice()
      .sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      )[0];
    return {
      total,
      active,
      inactive: total - active,
      revised,
      lastUpdated: latest?.updated_at,
    };
  }, [all]);

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

  function openNew() {
    setDraft({
      ...EMPTY,
      id: crypto.randomUUID(),
      pk: partition,
      sector: tenant.sector,
      unit: tenant.unit,
    });
  }

  return (
    <section className={s.root}>
      <header className={s.headerRow}>
        <div className={s.title}>
          <span className={s.titleText}>スキーマ一覧</span>
          <span className={s.subtitle}>
            ライン暗黙知の定義域。1 つの欠落がそのまま Δ 検出の死角になる。
          </span>
        </div>
        <span className={s.tenantChip} title="現在のテナント">
          {tenant.sector} / {tenant.unit}
        </span>
      </header>

      <div className={s.kpiRow}>
        <KpiCard
          label="登録スキーマ"
          value={listQ.isLoading ? "—" : String(stats.total)}
          hint={`active ${stats.active} / inactive ${stats.inactive}`}
        />
        <KpiCard
          label="改訂済 (rev>1)"
          value={listQ.isLoading ? "—" : String(stats.revised)}
          hint="運用で磨かれた定義の数"
        />
        <KpiCard label="リジェクト率" value="12%" hint="直近7日 (mock)" />
        <KpiCard
          label="最終更新"
          value={
            listQ.isLoading
              ? "—"
              : stats.lastUpdated
                ? formatJst(stats.lastUpdated).replace(" JST", "")
                : "—"
          }
          hint="JST"
        />
      </div>

      <div className={s.toolbar}>
        <div className={s.toolbarLeft}>
          <Button
            appearance="primary"
            icon={<Add24Regular />}
            onClick={openNew}
          >
            新規追加
          </Button>
          <Tooltip content="再読み込み" relationship="label">
            <Button
              appearance="subtle"
              icon={<ArrowSync20Regular />}
              onClick={() =>
                qc.invalidateQueries({ queryKey: ["schemas-list"] })
              }
              disabled={listQ.isFetching}
            />
          </Tooltip>
          {listQ.isFetching && <Spinner size="tiny" />}
        </div>
        <Field>
          <Input
            className={s.searchField}
            value={query}
            onChange={(_, d) => setQuery(d.value)}
            placeholder="field_name / 説明 / 例で検索…"
            contentBefore={<Search20Regular />}
          />
        </Field>
      </div>

      {listQ.isError && (
        <div className={s.errorBar}>取得失敗: {String(listQ.error)}</div>
      )}

      <div className={s.tableCard}>
        {listQ.isLoading ? (
          <div style={{ padding: tokens.spacingVerticalL }}>
            <Skeleton>
              <SkeletonItem size={24} style={{ marginBottom: 12 }} />
              <SkeletonItem size={16} style={{ marginBottom: 8 }} />
              <SkeletonItem size={16} style={{ marginBottom: 8 }} />
              <SkeletonItem size={16} />
            </Skeleton>
          </div>
        ) : filtered.length === 0 ? (
          <div className={s.emptyState}>
            <span style={{ fontSize: 32 }}>📋</span>
            <strong>スキーマがまだ登録されていません</strong>
            <span>新規追加ボタンから定義域を 1 件設定してください。</span>
          </div>
        ) : (
          <div style={{ minWidth: "960px" }}>
            <Table aria-label="schema list" size="medium">
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>field_name</TableHeaderCell>
                  <TableHeaderCell>type</TableHeaderCell>
                  <TableHeaderCell>description</TableHeaderCell>
                  <TableHeaderCell>example</TableHeaderCell>
                  <TableHeaderCell>rev</TableHeaderCell>
                  <TableHeaderCell>status</TableHeaderCell>
                  <TableHeaderCell>updated (JST)</TableHeaderCell>
                  <TableHeaderCell>actions</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className={s.fieldName}>
                      {d.field_name}
                    </TableCell>
                    <TableCell>
                      <Badge appearance="tint" color="informative">
                        {d.expected_value_type}
                      </Badge>
                    </TableCell>
                    <TableCell className={s.descCell}>
                      {d.description}
                    </TableCell>
                    <TableCell className={s.exampleCell}>{d.example}</TableCell>
                    <TableCell>
                      <Badge
                        appearance={d.revision_id > 1 ? "filled" : "outline"}
                        color={d.revision_id > 1 ? "brand" : "subtle"}
                      >
                        r{d.revision_id}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {d.is_active ? (
                        <Badge
                          appearance="tint"
                          color="success"
                          icon={<CheckmarkCircle20Filled />}
                        >
                          active
                        </Badge>
                      ) : (
                        <Badge
                          appearance="tint"
                          color="danger"
                          icon={<DismissCircle20Filled />}
                        >
                          inactive
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {formatJst(d.updated_at).replace(" JST", "")}
                    </TableCell>
                    <TableCell>
                      <div style={{ display: "flex", gap: 4 }}>
                        <Tooltip content="編集" relationship="label">
                          <Button
                            size="small"
                            appearance="subtle"
                            icon={<Edit20Regular />}
                            onClick={() => setDraft(d)}
                          />
                        </Tooltip>
                        <Tooltip
                          content={d.is_active ? "無効化" : "再有効化"}
                          relationship="label"
                        >
                          <Button
                            size="small"
                            appearance="subtle"
                            icon={
                              d.is_active ? (
                                <PauseCircle20Regular />
                              ) : (
                                <PlayCircle20Regular />
                              )
                            }
                            onClick={() => toggleMut.mutate(d)}
                            disabled={toggleMut.isPending}
                          />
                        </Tooltip>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <Editor
        draft={draft}
        onCancel={() => setDraft(null)}
        onSave={(d) => upsertMut.mutate(d)}
        saving={upsertMut.isPending}
        error={upsertMut.error ? String(upsertMut.error) : null}
      />
    </section>
  );
}

function KpiCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}): JSX.Element {
  const s = useStyles();
  return (
    <div className={s.kpiCard}>
      <span className={s.kpiLabel}>{label}</span>
      <span className={s.kpiValue}>{value}</span>
      {hint && <span className={s.kpiHint}>{hint}</span>}
    </div>
  );
}

interface EditorProps {
  draft: SchemaFieldDoc | null;
  onCancel: () => void;
  onSave: (v: SchemaFieldDoc) => void;
  saving: boolean;
  error: string | null;
}

function Editor({
  draft,
  onCancel,
  onSave,
  saving,
  error,
}: EditorProps): JSX.Element | null {
  const s = useStyles();
  const [v, setV] = useState<SchemaFieldDoc | null>(draft);

  // Sync local state when draft changes (open with new value).
  if (v?.id !== draft?.id) {
    setV(draft);
  }

  if (!draft || !v) return null;

  const isNew = v.revision_id === 0;

  return (
    <Dialog
      open={!!draft}
      onOpenChange={(_, data) => {
        if (!data.open) onCancel();
      }}
    >
      <DialogSurface>
        <DialogBody>
          <DialogTitle>
            {isNew ? "新規スキーマを追加" : `編集: ${v.field_name}`}
          </DialogTitle>
          <DialogContent>
            <div className={s.editorFields}>
              <Field label="field_name" required>
                <Input
                  value={v.field_name}
                  onChange={(_, d) => setV({ ...v, field_name: d.value })}
                  placeholder="例) defect_root_cause"
                />
              </Field>
              <Field label="description" required>
                <Textarea
                  value={v.description}
                  onChange={(_, d) => setV({ ...v, description: d.value })}
                  rows={2}
                  placeholder="この欄が暗黙知のどの観点を捕まえるかを 1 文で"
                />
              </Field>
              <Field label="expected_value_type">
                <Dropdown
                  value={v.expected_value_type}
                  selectedOptions={[v.expected_value_type]}
                  onOptionSelect={(_, data) => {
                    if (data.optionValue) {
                      setV({
                        ...v,
                        expected_value_type:
                          data.optionValue as ExpectedValueType,
                      });
                    }
                  }}
                >
                  <Option value="string">string</Option>
                  <Option value="number">number</Option>
                  <Option value="enum">enum</Option>
                  <Option value="structured">structured</Option>
                </Dropdown>
              </Field>
              <Field label="example">
                <Input
                  value={v.example}
                  onChange={(_, d) => setV({ ...v, example: d.value })}
                  placeholder="現場の典型値"
                />
              </Field>
              <Field
                label="ai_baseline_assumption"
                hint="AI が暗黙に置いている前提。ここからズレた発話が Δ 候補になる"
              >
                <Textarea
                  value={v.ai_baseline_assumption}
                  onChange={(_, d) =>
                    setV({ ...v, ai_baseline_assumption: d.value })
                  }
                  rows={2}
                />
              </Field>
              {error && <div className={s.errorBar}>{error}</div>}
            </div>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={onCancel}>
              キャンセル
            </Button>
            <Button
              appearance="primary"
              disabled={saving || !v.field_name.trim()}
              onClick={() => onSave(v)}
            >
              {saving ? "保存中…" : "保存"}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}
