import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  TabList,
  Tab,
  Input,
  Label,
  Title3,
  makeStyles,
  tokens,
  type SelectTabData,
  type SelectTabEvent,
} from "@fluentui/react-components";
import { useTenant } from "./lib/tenant";
import SchemaList from "./pages/SchemaList";
import SchemaHistory from "./pages/SchemaHistory";
import SchemaImport from "./pages/SchemaImport";
import SelfApprovalDashboard from "./pages/SelfApprovalDashboard";

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
  tenant: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalS,
  },
  main: {
    padding: tokens.spacingHorizontalXL,
  },
});

const TABS = [
  { value: "/schemas", label: "スキーマ" },
  { value: "/history", label: "履歴" },
  { value: "/import", label: "一括インポート" },
  { value: "/self-approval", label: "自己承認 KPI" },
];

export default function App(): JSX.Element {
  const styles = useStyles();
  const [tenant, setTenant] = useTenant();
  const location = useLocation();
  const navigate = useNavigate();
  const active =
    TABS.find((t) => location.pathname.startsWith(t.value))?.value ??
    "/schemas";

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Title3>Dialogue Delta · Admin</Title3>
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
        <div className={styles.tenant}>
          <Label>sector</Label>
          <Input
            size="small"
            value={tenant.sector}
            onChange={(_, d) => setTenant({ ...tenant, sector: d.value })}
            style={{ width: 120 }}
          />
          <Label>unit</Label>
          <Input
            size="small"
            value={tenant.unit}
            onChange={(_, d) => setTenant({ ...tenant, unit: d.value })}
            style={{ width: 120 }}
          />
        </div>
      </header>
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<Navigate to="/schemas" replace />} />
          <Route path="/schemas" element={<SchemaList tenant={tenant} />} />
          <Route path="/history" element={<SchemaHistory tenant={tenant} />} />
          <Route path="/import" element={<SchemaImport target={tenant} />} />
          <Route
            path="/self-approval"
            element={<SelfApprovalDashboard tenant={tenant} />}
          />
        </Routes>
      </main>
    </div>
  );
}
