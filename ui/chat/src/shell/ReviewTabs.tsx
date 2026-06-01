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
  { value: "", label: "キュー" },
  { value: "conflict", label: "競合" },
  { value: "self-approval", label: "自己承認率" },
];

const useStyles = makeStyles({
  bar: {
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalXL),
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
});

export function ReviewTabs() {
  const styles = useStyles();
  const location = useLocation();
  const navigate = useNavigate();
  const segment = location.pathname.replace(/^\/review\/?/, "").split("/")[0];
  const active = TABS.find((t) => t.value === segment)?.value ?? "";

  return (
    <div className={styles.bar}>
      <TabList
        selectedValue={active}
        onTabSelect={(_e: SelectTabEvent, d: SelectTabData) => {
          const v = d.value as string;
          navigate(v ? `/review/${v}` : "/review");
        }}
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
