import { useState } from "react";
import {
  Badge,
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  ProgressBar,
  Textarea,
  Tooltip,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  ArrowRight24Regular,
  Dismiss24Regular,
  QuestionCircle24Regular,
} from "@fluentui/react-icons";
import { respondHearout, skipHearout } from "../api/hearout";
import { HearoutTurn } from "../types";

interface Props {
  sessionId: string;
  initialQuestion: string;
  onClose: () => void;
}

const MAX_TURNS = 5;

const useStyles = makeStyles({
  body: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
    minWidth: "420px",
    "@media (max-width: 768px)": {
      minWidth: 0,
    },
  },
  progressRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  progressLabel: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  questionCard: {
    display: "flex",
    alignItems: "flex-start",
    ...shorthands.gap(tokens.spacingHorizontalS),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorNeutralForeground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: tokens.fontSizeBase300,
    lineHeight: tokens.lineHeightBase300,
  },
  history: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
    maxHeight: "180px",
    overflowY: "auto",
    ...shorthands.padding(tokens.spacingVerticalS),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
  },
  historyItem: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
    lineHeight: tokens.lineHeightBase200,
  },
  historyQ: {
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground3,
  },
  errorBar: {
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    backgroundColor: tokens.colorPaletteRedBackground1,
    color: tokens.colorPaletteRedForeground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontSize: tokens.fontSizeBase200,
  },
});

interface HistoryItem {
  question: string;
  answer: string;
}

export function HearoutModal({ sessionId, initialQuestion, onClose }: Props) {
  const styles = useStyles();
  const [question, setQuestion] = useState(initialQuestion);
  const [turnCount, setTurnCount] = useState(1);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [confirmSkip, setConfirmSkip] = useState(false);

  async function submit() {
    if (!answer.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const t: HearoutTurn = await respondHearout(sessionId, answer);
      setHistory((h) => [...h, { question, answer }]);
      setTurnCount(t.turn_count);
      setAnswer("");
      if (t.status !== "in_progress" || !t.next_question) {
        onClose();
      } else {
        setQuestion(t.next_question);
      }
    } catch (err) {
      setError(`回答送信に失敗しました: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  async function skip() {
    setBusy(true);
    try {
      await skipHearout(sessionId);
      onClose();
    } catch (err) {
      setError(`スキップに失敗しました: ${String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  const progress = Math.min(turnCount / MAX_TURNS, 1);

  return (
    <Dialog open modalType="non-modal" onOpenChange={() => undefined}>
      <DialogSurface
        style={{
          position: "fixed",
          right: "min(24px, 2vw)",
          bottom: "min(24px, 2vw)",
          left: "min(24px, 2vw)",
          maxWidth: "480px",
          marginLeft: "auto",
        }}
      >
        <DialogBody>
          <DialogTitle
            action={
              <Tooltip
                content="閉じる (回答は保存されません)"
                relationship="label"
              >
                <Button
                  appearance="subtle"
                  icon={<Dismiss24Regular />}
                  onClick={onClose}
                  aria-label="close"
                />
              </Tooltip>
            }
          >
            5W1H 確認ヒアリング
          </DialogTitle>
          <DialogContent>
            <div className={styles.body}>
              <div className={styles.progressRow}>
                <Badge appearance="tint" color="brand">
                  {turnCount} / {MAX_TURNS}
                </Badge>
                <span className={styles.progressLabel}>
                  対話で暗黙知を構造化します
                </span>
              </div>
              <ProgressBar value={progress} thickness="medium" />

              {history.length > 0 && (
                <div className={styles.history}>
                  {history.map((h, i) => (
                    <div key={i} className={styles.historyItem}>
                      <div className={styles.historyQ}>
                        Q{i + 1}: {h.question}
                      </div>
                      <div>→ {h.answer}</div>
                    </div>
                  ))}
                </div>
              )}

              <div className={styles.questionCard}>
                <QuestionCircle24Regular />
                <div>{question}</div>
              </div>

              <Textarea
                value={answer}
                onChange={(_, d) => setAnswer(d.value)}
                rows={3}
                placeholder="自由回答…"
                resize="vertical"
                disabled={busy}
              />

              {error && <div className={styles.errorBar}>{error}</div>}

              {confirmSkip && (
                <div className={styles.errorBar}>
                  ヒアリングをスキップすると暗黙知は記録されません。本当に閉じますか?
                </div>
              )}
            </div>
          </DialogContent>
          <DialogActions>
            {confirmSkip ? (
              <>
                <Button
                  appearance="subtle"
                  onClick={() => setConfirmSkip(false)}
                >
                  キャンセル
                </Button>
                <Button appearance="secondary" onClick={skip} disabled={busy}>
                  スキップを確定
                </Button>
              </>
            ) : (
              <>
                <Button
                  appearance="subtle"
                  onClick={() => setConfirmSkip(true)}
                  disabled={busy}
                >
                  スキップ
                </Button>
                <Button
                  appearance="primary"
                  icon={<ArrowRight24Regular />}
                  iconPosition="after"
                  onClick={submit}
                  disabled={busy || !answer.trim()}
                >
                  {busy ? "送信中…" : "次へ"}
                </Button>
              </>
            )}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}
