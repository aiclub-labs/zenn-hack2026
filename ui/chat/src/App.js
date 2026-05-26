import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./shell/AppShell";
import { useTenantCtx } from "./shell/TenantContext";
import { ChatPage } from "./pages/Chat";
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
    return (_jsxs(_Fragment, { children: [_jsx(AdminTabs, {}), _jsxs(Routes, { children: [_jsx(Route, { index: true, element: _jsx(Navigate, { to: "schemas", replace: true }) }), _jsx(Route, { path: "schemas", element: _jsx(SchemaList, { tenant: t }) }), _jsx(Route, { path: "history", element: _jsx(SchemaHistory, { tenant: t }) }), _jsx(Route, { path: "import", element: _jsx(SchemaImport, { target: t }) }), _jsx(Route, { path: "self-approval", element: _jsx(AdminSelfApprovalDashboard, { tenant: t }) }), _jsx(Route, { path: "*", element: _jsx(Navigate, { to: "schemas", replace: true }) })] })] }));
}
function ReviewRoutes() {
    return (_jsxs(_Fragment, { children: [_jsx(ReviewTabs, {}), _jsxs(Routes, { children: [_jsx(Route, { index: true, element: _jsx(NormalQueue, {}) }), _jsx(Route, { path: "conflict", element: _jsx(ConflictQueue, {}) }), _jsx(Route, { path: "self-approval", element: _jsx(ReviewSelfApprovalDashboard, {}) }), _jsx(Route, { path: "*", element: _jsx(Navigate, { to: ".", replace: true }) })] })] }));
}
export default function App() {
    return (_jsx(AppShell, { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Navigate, { to: "/chat", replace: true }) }), _jsx(Route, { path: "/chat", element: _jsx(ChatPage, {}) }), _jsx(Route, { path: "/admin/*", element: _jsx(AdminRoutes, {}) }), _jsx(Route, { path: "/review/*", element: _jsx(ReviewRoutes, {}) }), _jsx(Route, { path: "*", element: _jsx(Navigate, { to: "/chat", replace: true }) })] }) }));
}
