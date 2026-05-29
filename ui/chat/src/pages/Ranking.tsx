// Consultant-tacit pivot (2026-05-29): community-vote ranking page.
// Sorted by `score = upvotes - downvotes` server-side via AI Search.
import { useQuery } from "@tanstack/react-query";
import {
  Badge,
  Skeleton,
  SkeletonItem,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { Trophy24Regular } from "@fluentui/react-icons";
import { getRanking } from "../api/votes";
import { useTenantCtx } from "../shell/TenantContext";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXL),
  },
  header: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXXS),
  },
  title: {
    fontSize: tokens.fontSizeBase600,
    fontWeight: tokens.fontWeightSemibold,
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  subtitle: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  list: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    display: "grid",
    gridTemplateColumns: "48px 1fr auto",
    ...shorthands.gap(tokens.spacingHorizontalM),
    alignItems: "center",
    cursor: "pointer",
    ":hover": {
      backgroundColor: tokens.colorNeutralBackground1Hover,
      ...shorthands.border("1px", "solid", tokens.colorBrandStroke1),
    },
  },
  rank: {
    fontSize: tokens.fontSizeBase600,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorBrandForeground1,
    textAlign: "center",
  },
  body: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
    minWidth: 0,
  },
  contentLine: {
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    color: tokens.colorNeutralForeground1,
  },
  meta: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    fontFamily: tokens.fontFamilyMonospace,
  },
  scoreBox: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  scoreVal: {
    fontSize: tokens.fontSizeBase500,
    fontWeight: tokens.fontWeightSemibold,
  },
  scoreLabel: {
    fontSize: tokens.fontSizeBase100,
    color: tokens.colorNeutralForeground3,
  },
});

export default function RankingPage(): JSX.Element {
  const styles = useStyles();
  const { tenant } = useTenantCtx();
  const q = useQuery({
    queryKey: ["ranking", tenant],
    queryFn: () => getRanking(tenant.sector, tenant.unit, 30),
  });

  const entries = q.data?.entries ?? [];

  return (
    <section className={styles.root}>
      <div className={styles.header}>
        <span className={styles.title}>
          <Trophy24Regular />
          ノウハウランキング
        </span>
        <span className={styles.subtitle}>
          Good / Bad 投票で並ぶ「効いた個人ワザ」トップリスト。
        </span>
      </div>
      {q.isLoading ? (
        <Skeleton>
          <SkeletonItem size={48} style={{ marginBottom: 8 }} />
          <SkeletonItem size={48} style={{ marginBottom: 8 }} />
          <SkeletonItem size={48} />
        </Skeleton>
      ) : entries.length === 0 ? (
        <div className={styles.subtitle}>まだ投票がありません。</div>
      ) : (
        <div className={styles.list}>
          {entries.map((e, i) => (
            <div
              key={e.record_id}
              className={styles.card}
              role="button"
              tabIndex={0}
              onClick={() =>
                window.open(
                  `/records/${encodeURIComponent(e.record_id)}`,
                  "_blank",
                  "noopener,noreferrer",
                )
              }
              onKeyDown={(ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                  ev.preventDefault();
                  window.open(
                    `/records/${encodeURIComponent(e.record_id)}`,
                    "_blank",
                    "noopener,noreferrer",
                  );
                }
              }}
            >
              <div className={styles.rank}>#{i + 1}</div>
              <div className={styles.body}>
                <div className={styles.contentLine}>
                  {e.content.split("\n")[0]}
                </div>
                <div className={styles.meta}>
                  <Badge appearance="tint" color="informative">
                    {e.schema_field_id}
                  </Badge>
                  <span>👍 {e.upvotes}</span>
                  <span>👎 {e.downvotes}</span>
                </div>
              </div>
              <div className={styles.scoreBox}>
                <span className={styles.scoreVal}>{e.score}</span>
                <span className={styles.scoreLabel}>score</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
