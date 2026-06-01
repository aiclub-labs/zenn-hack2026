import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./shell/AppShell";
import { useTenantCtx } from "./shell/TenantContext";
import { ChatPage } from "./pages/Chat";
import SchemaChangelog from "./pages/SchemaChangelog";
import RankingPage from "./pages/Ranking";
import RecordDetail from "./pages/RecordDetail";
import SchemaList from "./admin/pages/SchemaList";
import SchemaHistory from "./admin/pages/SchemaHistory";
import SchemaImport from "./admin/pages/SchemaImport";
import AdminSelfApprovalDashboard from "./admin/pages/SelfApprovalDashboard";
import { NormalQueue } from "./review/pages/NormalQueue";
import { ConflictQueue } from "./review/pages/ConflictQueue";
import { SelfApprovalDashboard as ReviewSelfApprovalDashboard } from "./review/pages/SelfApprovalDashboard";
import { AdminTabs } from "./shell/AdminTabs";
import { ReviewTabs } from "./shell/ReviewTabs";

function AdminRoutes() {
  const { tenant } = useTenantCtx();
  const t = { sector: tenant.sector, unit: tenant.unit };
  return (
    <>
      <AdminTabs />
      <Routes>
        <Route index element={<Navigate to="schemas" replace />} />
        <Route path="schemas" element={<SchemaList tenant={t} />} />
        <Route path="history" element={<SchemaHistory tenant={t} />} />
        <Route path="import" element={<SchemaImport target={t} />} />
        <Route
          path="self-approval"
          element={<AdminSelfApprovalDashboard tenant={t} />}
        />
        <Route path="*" element={<Navigate to="schemas" replace />} />
      </Routes>
    </>
  );
}

function ReviewRoutes() {
  return (
    <>
      <ReviewTabs />
      <Routes>
        <Route index element={<NormalQueue />} />
        <Route path="conflict" element={<ConflictQueue />} />
        <Route path="self-approval" element={<ReviewSelfApprovalDashboard />} />
        <Route path="*" element={<Navigate to="." replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/changelog" element={<SchemaChangelog />} />
        <Route path="/popular" element={<RankingPage />} />
        <Route path="/records/:id" element={<RecordDetail />} />
        <Route path="/admin/*" element={<AdminRoutes />} />
        <Route path="/review/*" element={<ReviewRoutes />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </AppShell>
  );
}
