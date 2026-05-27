import { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Title3,
  Caption1,
  Input,
  Label,
  Badge,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import {
  Chat24Regular,
  Settings24Regular,
  TaskListSquareLtr24Regular,
} from "@fluentui/react-icons";
import { useTenantCtx } from "./TenantContext";

const NAV = [
  { to: "/chat", label: "Chat", icon: <Chat24Regular /> },
  { to: "/admin", label: "Admin", icon: <Settings24Regular /> },
  { to: "/review", label: "Review", icon: <TaskListSquareLtr24Regular /> },
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
    ...shorthands.padding(
      0,
      tokens.spacingHorizontalL,
      tokens.spacingVerticalL,
    ),
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
  disclosure: {
    ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalXL),
    backgroundColor: tokens.colorNeutralBackground3,
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase200,
    lineHeight: tokens.lineHeightBase200,
    textAlign: "center",
  },
});

export function AppShell({ children }: { children: ReactNode }) {
  const styles = useStyles();
  const { tenant, setTenant } = useTenantCtx();
  const location = useLocation();
  const activeLabel =
    NAV.find((n) => location.pathname.startsWith(n.to))?.label ?? "Dashboard";

  return (
    <div className={styles.root}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          Dialogue Delta
          <div className={styles.brandSub}>Tacit Knowledge Formalization</div>
        </div>
        <nav className={styles.nav}>
          {NAV.map((n) => {
            const active = location.pathname.startsWith(n.to);
            return (
              <NavLink
                key={n.to}
                to={n.to}
                className={`${styles.navItem} ${
                  active ? styles.navItemActive : ""
                }`}
              >
                {n.icon}
                {n.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <div className={styles.body}>
        <header className={styles.header}>
          <Title3>{activeLabel}</Title3>
          <Badge appearance="tint" color="brand">
            {tenant.sector} / {tenant.unit}
          </Badge>
          <div className={styles.tenant}>
            <Caption1>{tenant.user_id}</Caption1>
            <Label htmlFor="t-sector">sector</Label>
            <Input
              id="t-sector"
              size="small"
              value={tenant.sector}
              onChange={(_, d) => setTenant({ ...tenant, sector: d.value })}
              style={{ width: 160 }}
            />
            <Label htmlFor="t-unit">unit</Label>
            <Input
              id="t-unit"
              size="small"
              value={tenant.unit}
              onChange={(_, d) => setTenant({ ...tenant, unit: d.value })}
              style={{ width: 120 }}
            />
          </div>
        </header>
        <main className={styles.content}>{children}</main>
        <footer className={styles.disclosure}>
          この応答は AI が生成し、自己批評スコアで品質評価しています。機密情報は
          redact フラグでマスクしてください。 / 言語: 日本語 (ja-JP)
          固定、accessibility は Phase 2。
        </footer>
      </div>
    </div>
  );
}
