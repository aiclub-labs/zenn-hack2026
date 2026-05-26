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
  Warning20Filled,
} from "@fluentui/react-icons";
import { CitationRef, CitationDetail } from "../types";
import { getCitation } from "../api/citations";

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
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  toggle: {
    flex: 1,
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
    </div>
  );
}
