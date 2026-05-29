import { useState } from "react";
import {
  Button,
  ProgressBar,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  ChevronDown20Regular,
  ChevronRight20Regular,
  DocumentText20Regular,
  Open20Regular,
  ThumbLike20Regular,
  ThumbDislike20Regular,
  Warning20Filled,
} from "@fluentui/react-icons";
import { CitationRef, CitationDetail } from "../types";
import { getCitation } from "../api/citations";
import { castVote } from "../api/votes";

interface Props {
  citation: CitationRef;
  sector: string;
  unit: string;
}

const useStyles = makeStyles({
  root: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
  },
  supersededRoot: {
    backgroundColor: tokens.colorPaletteRedBackground1,
    ...shorthands.border("1px", "solid", tokens.colorPaletteRedBorder1),
  },
  header: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  toggle: {
    flex: "1 1 auto",
    minWidth: 0,
    justifyContent: "flex-start",
  },
  fieldLabel: {
    fontWeight: tokens.fontWeightSemibold,
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
  },
  recordId: {
    fontFamily: tokens.fontFamilyMonospace,
    fontSize: tokens.fontSizeBase100,
    color: tokens.colorNeutralForeground3,
  },
  weightBox: {
    minWidth: "80px",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
    ...shorthands.gap("2px"),
  },
  weightLabel: {
    fontSize: tokens.fontSizeBase100,
    color: tokens.colorNeutralForeground3,
    fontFamily: tokens.fontFamilyMonospace,
  },
  weightBar: {
    width: "80px",
  },
  warning: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalXS),
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorPaletteRedForeground1,
  },
  body: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground1,
    whiteSpace: "pre-wrap",
    lineHeight: tokens.lineHeightBase200,
    ...shorthands.padding(tokens.spacingVerticalS),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
  },
});

export function CitationCard({ citation, sector, unit }: Props) {
  const styles = useStyles();
  const [detail, setDetail] = useState<CitationDetail | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [voteState, setVoteState] = useState<{
    score: number | null;
    voted: "up" | "down" | null;
    pending: boolean;
  }>({ score: null, voted: null, pending: false });

  async function vote(direction: "up" | "down") {
    if (voteState.pending || voteState.voted) return;
    setVoteState((s) => ({ ...s, pending: true }));
    try {
      const r = await castVote(citation.record_id, direction);
      setVoteState({ score: r.score, voted: direction, pending: false });
    } catch {
      setVoteState((s) => ({ ...s, pending: false }));
    }
  }

  async function toggle() {
    if (!detail && !loading) {
      setLoading(true);
      try {
        const d = await getCitation(citation.record_id, sector, unit);
        setDetail(d);
      } finally {
        setLoading(false);
      }
    }
    setOpen((v) => !v);
  }

  const weightPct = Math.min(100, Math.max(0, citation.weight * 100));
  const rootClass = citation.superseded_by
    ? `${styles.root} ${styles.supersededRoot}`
    : styles.root;

  return (
    <div className={rootClass}>
      <div className={styles.header}>
        <Button
          appearance="subtle"
          size="small"
          icon={open ? <ChevronDown20Regular /> : <ChevronRight20Regular />}
          className={styles.toggle}
          onClick={toggle}
        >
          <DocumentText20Regular />
          <span className={styles.fieldLabel}>{citation.schema_field_id}</span>
          <span className={styles.recordId}>
            {citation.record_id.slice(0, 8)}
          </span>
        </Button>
        <div className={styles.weightBox}>
          <span className={styles.weightLabel}>w={weightPct.toFixed(0)}%</span>
          <ProgressBar
            className={styles.weightBar}
            value={citation.weight}
            thickness="medium"
          />
        </div>
        <Button
          appearance="subtle"
          size="small"
          icon={<Open20Regular />}
          onClick={() =>
            window.open(
              `/records/${encodeURIComponent(citation.record_id)}`,
              "_blank",
              "noopener,noreferrer",
            )
          }
          aria-label="詳細を新規タブで開く"
        >
          詳細
        </Button>
      </div>
      {detail?.superseded_banner && (
        <div className={styles.warning}>
          <Warning20Filled />
          {detail.superseded_banner}
        </div>
      )}
      {open && (
        <div className={styles.body}>
          {loading ? "読み込み中…" : (detail?.content ?? "(本文取得失敗)")}
        </div>
      )}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: tokens.spacingHorizontalS,
          paddingTop: tokens.spacingVerticalXS,
        }}
      >
        <Button
          appearance={voteState.voted === "up" ? "primary" : "subtle"}
          size="small"
          icon={<ThumbLike20Regular />}
          disabled={voteState.pending || voteState.voted !== null}
          onClick={() => vote("up")}
          aria-label="役に立った"
        >
          Good
        </Button>
        <Button
          appearance={voteState.voted === "down" ? "primary" : "subtle"}
          size="small"
          icon={<ThumbDislike20Regular />}
          disabled={voteState.pending || voteState.voted !== null}
          onClick={() => vote("down")}
          aria-label="役に立たなかった"
        >
          Bad
        </Button>
        {voteState.score !== null && (
          <span
            style={{
              fontSize: tokens.fontSizeBase200,
              color: tokens.colorNeutralForeground3,
              fontFamily: tokens.fontFamilyMonospace,
            }}
          >
            score={voteState.score}
          </span>
        )}
      </div>
    </div>
  );
}
