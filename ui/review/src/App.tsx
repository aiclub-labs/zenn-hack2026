import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  TabList,
  Tab,
  Title3,
  Caption1,
  makeStyles,
  tokens,
  type SelectTabData,
  type SelectTabEvent,
} from "@fluentui/react-components";
import { NormalQueue } from "./pages/NormalQueue";
import { ConflictQueue } from "./pages/ConflictQueue";
import { SelfApprovalDashboard } from "./pages/SelfApprovalDashboard";

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
  const active =
    [...TABS]
      .sort((a, b) => b.value.length - a.value.length)
      .find((t) => location.pathname.startsWith(t.value))?.value ?? "/";

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Title3>Review</Title3>
        <Caption1>タケシ</Caption1>
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
