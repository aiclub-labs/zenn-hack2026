import { useLocation, useNavigate } from "react-router-dom";
import {
  TabList,
  Tab,
  makeStyles,
  tokens,
  shorthands,
  type SelectTabData,
  type SelectTabEvent,
} from "@fluentui/react-components";

const TABS = [
  { value: "schemas", label: "スキーマ" },
  { value: "history", label: "履歴" },
  { value: "import", label: "一括インポート" },
  { value: "self-approval", label: "自己承認 KPI" },
];

const useStyles = makeStyles({
  bar: {
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalXL),
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
});

export function AdminTabs() {
  const styles = useStyles();
  const location = useLocation();
  const navigate = useNavigate();
  const segment = location.pathname.replace(/^\/admin\/?/, "").split("/")[0];
  const active = TABS.find((t) => t.value === segment)?.value ?? "schemas";

  return (
    <div className={styles.bar}>
      <TabList
        selectedValue={active}
        onTabSelect={(_e: SelectTabEvent, d: SelectTabData) =>
          navigate(`/admin/${d.value}`)
        }
      >
        {TABS.map((t) => (
          <Tab key={t.value} value={t.value}>
            {t.label}
          </Tab>
        ))}
      </TabList>
    </div>
  );
}
