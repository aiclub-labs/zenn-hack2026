import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { NavLink, useLocation } from "react-router-dom";
import { Title3, Caption1, Input, Label, Badge, makeStyles, tokens, shorthands, } from "@fluentui/react-components";
import { Chat24Regular, Settings24Regular, TaskListSquareLtr24Regular, } from "@fluentui/react-icons";
import { useTenantCtx } from "./TenantContext";
const NAV = [
    { to: "/chat", label: "Chat", icon: _jsx(Chat24Regular, {}) },
    { to: "/admin", label: "Admin", icon: _jsx(Settings24Regular, {}) },
    { to: "/review", label: "Review", icon: _jsx(TaskListSquareLtr24Regular, {}) },
];
const useStyles = makeStyles({
    root: {
        display: "grid",
        gridTemplateColumns: "240px 1fr",
        minHeight: "100vh",
        backgroundColor: tokens.colorNeutralBackground2,
    },
    sidebar: {
        backgroundColor: tokens.colorBrandBackground,
        color: tokens.colorNeutralForegroundOnBrand,
        display: "flex",
        flexDirection: "column",
        ...shorthands.padding(tokens.spacingVerticalL, 0),
    },
    brand: {
        ...shorthands.padding(0, tokens.spacingHorizontalL, tokens.spacingVerticalL),
        fontWeight: 700,
        fontSize: tokens.fontSizeBase500,
        letterSpacing: "0.02em",
        color: tokens.colorNeutralForegroundOnBrand,
    },
    brandSub: {
        fontSize: tokens.fontSizeBase200,
        fontWeight: 400,
        opacity: 0.75,
        marginTop: "2px",
    },
    nav: {
        display: "flex",
        flexDirection: "column",
        gap: "2px",
    },
    navItem: {
        display: "flex",
        alignItems: "center",
        gap: tokens.spacingHorizontalM,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
        color: tokens.colorNeutralForegroundOnBrand,
        textDecoration: "none",
        fontSize: tokens.fontSizeBase300,
        cursor: "pointer",
        transition: "background-color 80ms ease-in",
        ":hover": {
            backgroundColor: "rgba(255,255,255,0.08)",
        },
    },
    navItemActive: {
        backgroundColor: "rgba(255,255,255,0.16)",
        borderLeft: `3px solid ${tokens.colorPaletteRedForeground1}`,
        paddingLeft: `calc(${tokens.spacingHorizontalL} - 3px)`,
    },
    body: {
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
    },
    header: {
        display: "flex",
        alignItems: "center",
        gap: tokens.spacingHorizontalL,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalXL),
        backgroundColor: tokens.colorNeutralBackground1,
        borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    },
    tenant: {
        marginLeft: "auto",
        display: "flex",
        alignItems: "center",
        gap: tokens.spacingHorizontalS,
    },
    content: {
        flex: 1,
        minWidth: 0,
    },
});
export function AppShell({ children }) {
    const styles = useStyles();
    const { tenant, setTenant } = useTenantCtx();
    const location = useLocation();
    const activeLabel = NAV.find((n) => location.pathname.startsWith(n.to))?.label ?? "Dashboard";
    return (_jsxs("div", { className: styles.root, children: [_jsxs("aside", { className: styles.sidebar, children: [_jsxs("div", { className: styles.brand, children: ["Dialogue Delta", _jsx("div", { className: styles.brandSub, children: "Tacit Knowledge Formalization" })] }), _jsx("nav", { className: styles.nav, children: NAV.map((n) => {
                            const active = location.pathname.startsWith(n.to);
                            return (_jsxs(NavLink, { to: n.to, className: `${styles.navItem} ${active ? styles.navItemActive : ""}`, children: [n.icon, n.label] }, n.to));
                        }) })] }), _jsxs("div", { className: styles.body, children: [_jsxs("header", { className: styles.header, children: [_jsx(Title3, { children: activeLabel }), _jsxs(Badge, { appearance: "tint", color: "brand", children: [tenant.sector, " / ", tenant.unit] }), _jsxs("div", { className: styles.tenant, children: [_jsx(Caption1, { children: tenant.user_id }), _jsx(Label, { htmlFor: "t-sector", children: "sector" }), _jsx(Input, { id: "t-sector", size: "small", value: tenant.sector, onChange: (_, d) => setTenant({ ...tenant, sector: d.value }), style: { width: 160 } }), _jsx(Label, { htmlFor: "t-unit", children: "unit" }), _jsx(Input, { id: "t-unit", size: "small", value: tenant.unit, onChange: (_, d) => setTenant({ ...tenant, unit: d.value }), style: { width: 120 } })] })] }), _jsx("main", { className: styles.content, children: children })] })] }));
}
