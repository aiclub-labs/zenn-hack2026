import { useNavigate } from "react-router-dom";
import {
  Badge,
  Button,
  MessageBar,
  MessageBarActions,
  MessageBarBody,
  MessageBarTitle,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { History20Regular } from "@fluentui/react-icons";
import { SchemaUpdateBanner } from "../types";
import { ackBanner } from "../api/turn";

interface Props {
  banner: SchemaUpdateBanner;
  turnId: string;
  sector: string;
  unit: string;
  userId: string;
  onAck: () => void;
}

const useStyles = makeStyles({
  wrapper: {
    ...shorthands.margin(
      tokens.spacingVerticalS,
      tokens.spacingHorizontalXL,
      0,
      tokens.spacingHorizontalXL,
    ),
  },
  summary: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
    marginTop: tokens.spacingVerticalXS,
  },
});

export function SchemaUpdateBannerView({
  banner,
  turnId,
  sector,
  unit,
  userId,
  onAck,
}: Props) {
  const styles = useStyles();
  const navigate = useNavigate();
  const count = banner.unseen_revision_ids.length;

  async function handleAck() {
    await ackBanner(turnId, sector, unit, userId);
    onAck();
  }

  return (
    <div className={styles.wrapper}>
      <MessageBar intent="warning" politeness="polite">
        <MessageBarBody>
          <MessageBarTitle>
            schema 更新があります{" "}
            <Badge appearance="tint" color="warning">
              {count} 件
            </Badge>
          </MessageBarTitle>
          <div className={styles.summary}>{banner.changed_fields_summary}</div>
        </MessageBarBody>
        <MessageBarActions>
          <Button
            appearance="subtle"
            icon={<History20Regular />}
            onClick={() => navigate("/changelog")}
          >
            履歴を見る
          </Button>
          <Button appearance="primary" onClick={handleAck}>
            確認しました
          </Button>
        </MessageBarActions>
      </MessageBar>
    </div>
  );
}
