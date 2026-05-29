import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  Input,
  Skeleton,
  SkeletonItem,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Tooltip,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  ArrowSync20Regular,
  CheckmarkCircle20Regular,
  ClipboardTaskListLtr24Regular,
  Dismiss20Regular,
  DismissCircle20Regular,
  Edit20Regular,
  LockClosed20Regular,
  LockOpen20Regular,
  Search20Regular,
} from "@fluentui/react-icons";
import { FormalizationTicket } from "../types";
import {
  decideReview,
  getPriorityMode,
  listReviews,
  lockReview,
  unlockReview,
} from "../api/reviews";
import { WeightBreakdown } from "../components/WeightBreakdown";
import { LockBadge } from "../components/LockBadge";
import { PriorityModeBanner } from "../components/PriorityModeBanner";
import { useTenantCtx } from "../../shell/TenantContext";

function ageMin(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
}

function ageText(min: number): string {
  if (min < 60) return `${min} 分`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} 時間`;
  return `${Math.floor(h / 24)} 日`;
}

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXL),
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
    ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
    backgroundColor: tokens.colorNeutralBackground3,
    color: tokens.colorNeutralForeground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
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
  idCell: {
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
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
  drawerSection: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  drawerRow: {
    display: "flex",
    justifyContent: "space-between",
    ...shorthands.gap(tokens.spacingHorizontalS),
    fontSize: tokens.fontSizeBase300,
  },
  drawerLabel: {
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase200,
  },
  drawerActions: {
    display: "flex",
    ...shorthands.gap(tokens.spacingHorizontalS),
    marginTop: tokens.spacingVerticalL,
  },
});

type SortKey = "weight" | "age";

export function NormalQueue() {
  const styles = useStyles();
  const { tenant } = useTenantCtx();
  const [tickets, setTickets] = useState<FormalizationTicket[]>([]);
  const [selected, setSelected] = useState<FormalizationTicket | null>(null);
  const [priorityOnly, setPriorityOnly] = useState(false);
  const [pmActive, setPmActive] = useState(false);
  const [pmMedian, setPmMedian] = useState(0);
  const [pmThreshold, setPmThreshold] = useState(180);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("weight");

  async function load() {
    setLoading(true);
    try {
      setTickets(await listReviews(priorityOnly, tenant.sector, tenant.unit));
      const pm = await getPriorityMode();
      setPmActive(pm.active);
      setPmMedian(pm.median_sec);
      setPmThreshold(pm.threshold_sec);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [priorityOnly, tenant.sector, tenant.unit]);

  async function onLock(t: FormalizationTicket) {
    await lockReview(t.id);
    await load();
  }
  async function onUnlock(t: FormalizationTicket) {
    await unlockReview(t.id);
    await load();
  }
  async function onDecide(
    t: FormalizationTicket,
    decision: "approve" | "edit" | "reject",
  ) {
    const [sector, unit] = t.pk.split("#");
    await decideReview(t.id, sector ?? "", unit ?? "", decision);
    setSelected(null);
    await load();
  }

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    const rows = q
      ? tickets.filter(
          (t) =>
            t.id.toLowerCase().includes(q) ||
            t.hearout_id.toLowerCase().includes(q) ||
            t.pk.toLowerCase().includes(q),
        )
      : tickets;
    return [...rows].sort((a, b) => {
      if (sortKey === "weight") return b.weight_final - a.weight_final;
      return (
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
    });
  }, [tickets, filter, sortKey]);

  return (
    <div className={styles.root}>
      <div className={styles.headerRow}>
        <div className={styles.title}>
          <span className={styles.titleText}>レビュー待ちキュー</span>
          <span className={styles.subtitle}>
            weight_final 順で並ぶ pending_review
            チケット。ロックを取得してから判定。
          </span>
        </div>
        <span className={styles.tenantChip}>
          {tenant.sector}#{tenant.unit}
        </span>
      </div>

      <PriorityModeBanner
        active={pmActive}
        medianSec={pmMedian}
        thresholdSec={pmThreshold}
        priorityOnly={priorityOnly}
        onToggle={setPriorityOnly}
      />

      <div className={styles.toolbar}>
        <div className={styles.toolbarLeft}>
          <Tooltip content="再読み込み" relationship="label">
            <Button
              appearance="subtle"
              icon={loading ? <Spinner size="tiny" /> : <ArrowSync20Regular />}
              onClick={load}
              disabled={loading}
              aria-label="refresh"
            />
          </Tooltip>
          <Button
            appearance={sortKey === "weight" ? "primary" : "secondary"}
            size="small"
            onClick={() => setSortKey("weight")}
          >
            weight 順
          </Button>
          <Button
            appearance={sortKey === "age" ? "primary" : "secondary"}
            size="small"
            onClick={() => setSortKey("age")}
          >
            古い順
          </Button>
        </div>
        <Input
          className={styles.searchField}
          contentBefore={<Search20Regular />}
          placeholder="id / hearout_id / pk で検索…"
          value={filter}
          onChange={(_, d) => setFilter(d.value)}
        />
      </div>

      <div className={styles.tableCard}>
        {loading && tickets.length === 0 ? (
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
        ) : visible.length === 0 ? (
          <div className={styles.emptyState}>
            <ClipboardTaskListLtr24Regular fontSize={32} />
            <div>
              キューは空です。新しい hearout が完了するとここに表示されます。
            </div>
          </div>
        ) : (
          <div style={{ minWidth: "840px" }}>
            <Table size="medium">
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>ID</TableHeaderCell>
                  <TableHeaderCell>hearout</TableHeaderCell>
                  <TableHeaderCell>weight</TableHeaderCell>
                  <TableHeaderCell>TJ</TableHeaderCell>
                  <TableHeaderCell>lock</TableHeaderCell>
                  <TableHeaderCell>age</TableHeaderCell>
                  <TableHeaderCell>actions</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visible.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell className={styles.idCell}>
                      <Tooltip content={t.id} relationship="label">
                        <span>{t.id.slice(0, 8)}</span>
                      </Tooltip>
                    </TableCell>
                    <TableCell className={styles.idCell}>
                      {t.hearout_id.slice(0, 8)}
                    </TableCell>
                    <TableCell>
                      <WeightBreakdown
                        a={t.weight_a}
                        b={t.weight_b}
                        c={t.weight_c}
                        final={t.weight_final}
                      />
                    </TableCell>
                    <TableCell>
                      {t.tj_verdict && (
                        <Badge
                          appearance="filled"
                          color={
                            t.tj_verdict === "supported"
                              ? "success"
                              : t.tj_verdict === "conflict"
                                ? "danger"
                                : "warning"
                          }
                        >
                          {t.tj_verdict}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <LockBadge
                        lockedBy={t.locked_by}
                        lockExpiresAt={t.lock_expires_at}
                      />
                    </TableCell>
                    <TableCell>{ageText(ageMin(t.created_at))}</TableCell>
                    <TableCell>
                      <Button
                        appearance="primary"
                        size="small"
                        onClick={() => setSelected(t)}
                      >
                        開く
                      </Button>{" "}
                      {!t.locked_by ? (
                        <Tooltip content="ロック取得" relationship="label">
                          <Button
                            appearance="subtle"
                            size="small"
                            icon={<LockClosed20Regular />}
                            onClick={() => onLock(t)}
                            aria-label="lock"
                          />
                        </Tooltip>
                      ) : (
                        <Tooltip content="ロック解除" relationship="label">
                          <Button
                            appearance="subtle"
                            size="small"
                            icon={<LockOpen20Regular />}
                            onClick={() => onUnlock(t)}
                            aria-label="unlock"
                          />
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <Drawer
        type="overlay"
        position="end"
        open={selected !== null}
        onOpenChange={(_, d) => !d.open && setSelected(null)}
        size="medium"
      >
        {selected && (
          <>
            <DrawerHeader>
              <DrawerHeaderTitle
                action={
                  <Button
                    appearance="subtle"
                    icon={<Dismiss20Regular />}
                    onClick={() => setSelected(null)}
                    aria-label="close"
                  />
                }
              >
                ticket {selected.id.slice(0, 8)}
              </DrawerHeaderTitle>
            </DrawerHeader>
            <DrawerBody>
              <div className={styles.drawerSection}>
                <div className={styles.drawerRow}>
                  <span className={styles.drawerLabel}>full id</span>
                  <span className={styles.idCell}>{selected.id}</span>
                </div>
                <div className={styles.drawerRow}>
                  <span className={styles.drawerLabel}>hearout</span>
                  <span className={styles.idCell}>{selected.hearout_id}</span>
                </div>
                <div className={styles.drawerRow}>
                  <span className={styles.drawerLabel}>pk</span>
                  <span className={styles.idCell}>{selected.pk}</span>
                </div>
                <div className={styles.drawerRow}>
                  <span className={styles.drawerLabel}>weight</span>
                  <WeightBreakdown
                    a={selected.weight_a}
                    b={selected.weight_b}
                    c={selected.weight_c}
                    final={selected.weight_final}
                  />
                </div>
                <div className={styles.drawerRow}>
                  <span className={styles.drawerLabel}>TJ verdict</span>
                  <span>{selected.tj_verdict ?? "n/a"}</span>
                </div>
                <div className={styles.drawerRow}>
                  <span className={styles.drawerLabel}>age</span>
                  <span>{ageText(ageMin(selected.created_at))}</span>
                </div>
                <div className={styles.drawerRow}>
                  <span className={styles.drawerLabel}>関連 turn</span>
                  <span className={styles.subtitle}>
                    hearout から辿る (WT-D連携 TODO)
                  </span>
                </div>
                <div className={styles.drawerActions}>
                  <Button
                    appearance="primary"
                    icon={<CheckmarkCircle20Regular />}
                    onClick={() => onDecide(selected, "approve")}
                  >
                    承認
                  </Button>
                  <Button
                    appearance="secondary"
                    icon={<Edit20Regular />}
                    onClick={() => onDecide(selected, "edit")}
                  >
                    編集
                  </Button>
                  <Button
                    appearance="outline"
                    icon={<DismissCircle20Regular />}
                    onClick={() => onDecide(selected, "reject")}
                  >
                    却下
                  </Button>
                </div>
              </div>
            </DrawerBody>
          </>
        )}
      </Drawer>
    </div>
  );
}
