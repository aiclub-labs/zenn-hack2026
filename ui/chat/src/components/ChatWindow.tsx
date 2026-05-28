import { useEffect, useRef } from "react";
import {
  Badge,
  Tooltip,
  makeStyles,
  mergeClasses,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  Bot24Regular,
  Person24Regular,
  Sparkle16Regular,
} from "@fluentui/react-icons";
import { ChatMessage } from "../types";
import { CitationCard } from "./CitationCard";

interface Props {
  messages: ChatMessage[];
  sector: string;
  unit: string;
}

const useStyles = makeStyles({
  root: {
    flex: 1,
    overflowY: "auto",
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXL),
    backgroundColor: tokens.colorNeutralBackground2,
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    color: tokens.colorNeutralForeground3,
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  emptyIcon: {
    fontSize: "48px",
    color: tokens.colorBrandForeground1,
  },
  messageRow: {
    display: "flex",
    ...shorthands.gap(tokens.spacingHorizontalS),
    alignItems: "flex-start",
    maxWidth: "78%",
  },
  userRow: {
    alignSelf: "flex-end",
    flexDirection: "row-reverse",
  },
  assistantRow: {
    alignSelf: "flex-start",
  },
  avatar: {
    width: "32px",
    height: "32px",
    flexShrink: 0,
    ...shorthands.borderRadius("50%"),
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: tokens.colorNeutralForegroundOnBrand,
  },
  userAvatar: {
    backgroundColor: tokens.colorBrandBackground,
  },
  assistantAvatar: {
    backgroundColor: tokens.colorPaletteBlueBorderActive,
  },
  bubble: {
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    fontSize: tokens.fontSizeBase300,
    lineHeight: tokens.lineHeightBase300,
    whiteSpace: "pre-wrap",
    boxShadow: tokens.shadow2,
  },
  userBubble: {
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorNeutralForeground1,
    borderTopRightRadius: tokens.borderRadiusSmall,
  },
  assistantBubble: {
    backgroundColor: tokens.colorNeutralBackground1,
    color: tokens.colorNeutralForeground1,
    borderTopLeftRadius: tokens.borderRadiusSmall,
  },
  meta: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalXS),
    marginTop: tokens.spacingVerticalXS,
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  citations: {
    marginTop: tokens.spacingVerticalS,
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
  },
});

function scoreColor(score: number): "success" | "warning" | "danger" {
  if (score >= 7) return "success";
  if (score >= 4) return "warning";
  return "danger";
}

export function ChatWindow({ messages, sector, unit }: Props) {
  const styles = useStyles();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length]);

  if (messages.length === 0) {
    return (
      <div className={styles.root} ref={scrollRef}>
        <div className={styles.emptyState}>
          <Sparkle16Regular className={styles.emptyIcon} />
          <div>質問を入力すると、暗黙知ベースの応答が表示されます。</div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.root} ref={scrollRef}>
      {messages.map((m, i) => {
        const isUser = m.role === "user";
        return (
          <div
            key={i}
            className={mergeClasses(
              styles.messageRow,
              isUser ? styles.userRow : styles.assistantRow,
            )}
          >
            <div
              className={mergeClasses(
                styles.avatar,
                isUser ? styles.userAvatar : styles.assistantAvatar,
              )}
            >
              {isUser ? <Person24Regular /> : <Bot24Regular />}
            </div>
            <div>
              <div
                className={mergeClasses(
                  styles.bubble,
                  isUser ? styles.userBubble : styles.assistantBubble,
                )}
              >
                {m.content}
              </div>
              {typeof m.selfCriticScore === "number" && (
                <div className={styles.meta}>
                  {m.selfCriticScore < 5 && m.selfCriticReason ? (
                    <Tooltip
                      content={`判定理由: ${m.selfCriticReason}`}
                      relationship="description"
                      withArrow
                    >
                      <Badge
                        appearance="tint"
                        color={scoreColor(m.selfCriticScore)}
                        size="small"
                      >
                        self-critic {m.selfCriticScore.toFixed(1)} / 10 ⓘ
                      </Badge>
                    </Tooltip>
                  ) : (
                    <Badge
                      appearance="tint"
                      color={scoreColor(m.selfCriticScore)}
                      size="small"
                    >
                      self-critic {m.selfCriticScore.toFixed(1)} / 10
                    </Badge>
                  )}
                </div>
              )}
              {m.citations && m.citations.length > 0 && (
                <div className={styles.citations}>
                  {m.citations.map((c) => (
                    <CitationCard
                      key={c.record_id}
                      citation={c}
                      sector={sector}
                      unit={unit}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
