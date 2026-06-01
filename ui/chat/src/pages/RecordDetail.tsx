// Consultant-tacit pivot (2026-05-29): per-record detail page.
// Reached from chat citation header or ranking list item — gives a
// shareable URL for a single piece of know-how.
import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Badge,
  Button,
  Skeleton,
  SkeletonItem,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  ArrowLeft20Regular,
  ThumbLike20Regular,
  ThumbDislike20Regular,
  Warning20Filled,
} from "@fluentui/react-icons";
import { useQuery } from "@tanstack/react-query";
import { castVote, getRecord } from "../api/votes";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXL),
    maxWidth: "880px",
  },
  back: {
    alignSelf: "flex-start",
  },
  header: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
  },
  meta: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  scoreRow: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  scoreVal: {
    fontSize: tokens.fontSizeBase600,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorBrandForeground1,
  },
  body: {
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalL),
    whiteSpace: "pre-wrap",
    lineHeight: tokens.lineHeightBase300,
    color: tokens.colorNeutralForeground1,
  },
  section: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  sectionTitle: {
    fontSize: tokens.fontSizeBase300,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground2,
  },
  claimList: {
    margin: 0,
    paddingLeft: tokens.spacingHorizontalXL,
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
    color: tokens.colorNeutralForeground1,
  },
  superseded: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalXS),
    color: tokens.colorPaletteRedForeground1,
    backgroundColor: tokens.colorPaletteRedBackground1,
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
  },
  voteRow: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
});

export default function RecordDetail(): JSX.Element {
  const styles = useStyles();
  const { id = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const q = useQuery({
    queryKey: ["record", id],
    queryFn: () => getRecord(id),
    enabled: !!id,
  });
  const [voteState, setVoteState] = useState<{
    score: number | null;
    voted: "up" | "down" | null;
    pending: boolean;
  }>({ score: null, voted: null, pending: false });

  async function vote(direction: "up" | "down") {
    if (voteState.pending || voteState.voted) return;
    setVoteState((s) => ({ ...s, pending: true }));
    try {
      const r = await castVote(id, direction);
      setVoteState({ score: r.score, voted: direction, pending: false });
    } catch {
      setVoteState((s) => ({ ...s, pending: false }));
    }
  }

  const data = q.data;
  const score = voteState.score ?? data?.score ?? 0;

  return (
    <section className={styles.root}>
      <Button
        appearance="subtle"
        size="small"
        icon={<ArrowLeft20Regular />}
        className={styles.back}
        onClick={() => navigate(-1)}
      >
        戻る
      </Button>

      {q.isLoading ? (
        <Skeleton>
          <SkeletonItem size={32} style={{ marginBottom: 12 }} />
          <SkeletonItem size={120} />
        </Skeleton>
      ) : q.isError || !data ? (
        <div>レコードが見つかりませんでした。</div>
      ) : (
        <>
          <div className={styles.header}>
            <div className={styles.meta}>
              <Badge appearance="tint" color="informative">
                {data.schema_field_id}
              </Badge>
              <span>{data.record_id}</span>
            </div>
            <div className={styles.scoreRow}>
              <span className={styles.scoreVal}>score {score}</span>
              <span className={styles.meta}>
                👍 {data.upvotes} 👎 {data.downvotes} · 引用{" "}
                {data.referenced_count}
              </span>
            </div>
          </div>

          {data.superseded_by && (
            <div className={styles.superseded}>
              <Warning20Filled />
              このレコードは {data.superseded_by} に置き換え済み
            </div>
          )}

          <div className={styles.body}>{data.content}</div>

          {data.atomic_claims.length > 0 && (
            <div className={styles.section}>
              <span className={styles.sectionTitle}>Atomic claims</span>
              <ul className={styles.claimList}>
                {data.atomic_claims.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          <div className={styles.voteRow}>
            <Button
              appearance={voteState.voted === "up" ? "primary" : "subtle"}
              icon={<ThumbLike20Regular />}
              disabled={voteState.pending || voteState.voted !== null}
              onClick={() => vote("up")}
            >
              Good
            </Button>
            <Button
              appearance={voteState.voted === "down" ? "primary" : "subtle"}
              icon={<ThumbDislike20Regular />}
              disabled={voteState.pending || voteState.voted !== null}
              onClick={() => vote("down")}
            >
              Bad
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
