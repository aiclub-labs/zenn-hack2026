import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { useState } from "react";
import {
  TabList,
  Tab,
  Title3,
  Caption1,
  Dropdown,
  Option,
  makeStyles,
  tokens,
  type SelectTabData,
  type SelectTabEvent,
  type OptionOnSelectData,
} from "@fluentui/react-components";
import { NormalQueue } from "./pages/NormalQueue";
import { ConflictQueue } from "./pages/ConflictQueue";
import { SelfApprovalDashboard } from "./pages/SelfApprovalDashboard";
import {
  REVIEWER_PROFILES,
  getReviewerId,
  setReviewerId,
  type ReviewerProfile,
} from "./api/client";

const qc = new QueryClient();

const useStyles = makeStyles({
  shell: {
    minHeight: "100vh",
    backgroundColor: tokens.colorNeutralBackground2,
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalL,
    padding: `${tokens.spacingVerticalM} ${tokens.spacingHorizontalXL}`,
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  main: {
    padding: tokens.spacingHorizontalXL,
  },
});

const TABS = [
  { value: "/", label: "キュー" },
  { value: "/conflict", label: "競合" },
  { value: "/self-approval", label: "自己承認率" },
];

function Shell() {
  const styles = useStyles();
  const location = useLocation();
  const navigate = useNavigate();
  const [reviewer, setReviewer] = useState<ReviewerProfile>(getReviewerId());
  const active =
    [...TABS]
      .sort((a, b) => b.value.length - a.value.length)
      .find((t) => location.pathname.startsWith(t.value))?.value ?? "/";

  const onReviewerChange = (_e: unknown, data: OptionOnSelectData) => {
    const next = data.optionValue as ReviewerProfile | undefined;
    if (next && (REVIEWER_PROFILES as readonly string[]).includes(next)) {
      setReviewerId(next);
      setReviewer(next);
      // Force a reload so cached queries refetch under the new identity.
      window.location.reload();
    }
  };

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Title3>Review</Title3>
        <Caption1>タケシ</Caption1>
        <Dropdown
          value={reviewer}
          selectedOptions={[reviewer]}
          onOptionSelect={onReviewerChange}
          aria-label="reviewer profile"
        >
          {REVIEWER_PROFILES.map((p) => (
            <Option key={p} value={p}>
              {p}
            </Option>
          ))}
        </Dropdown>
        <TabList
          selectedValue={active}
          onTabSelect={(_e: SelectTabEvent, d: SelectTabData) =>
            navigate(d.value as string)
          }
        >
          {TABS.map((t) => (
            <Tab key={t.value} value={t.value}>
              {t.label}
            </Tab>
          ))}
        </TabList>
      </header>
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<NormalQueue />} />
          <Route path="/conflict" element={<ConflictQueue />} />
          <Route path="/self-approval" element={<SelfApprovalDashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
