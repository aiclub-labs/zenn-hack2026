import { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Title3,
  Combobox,
  Option,
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
  Trophy24Regular,
} from "@fluentui/react-icons";
import { useTenantCtx } from "./TenantContext";

const SECTOR_OPTIONS = ["manufacturing-s8b", "strategy-poc", "fintech-poc"];
const UNIT_OPTIONS = ["line-A", "line-B", "auto-mfg", "retail-bank"];
const USER_OPTIONS = ["haruka@example.com", "shigeru.dev", "takeshi.dev"];

const NAV = [
  { to: "/chat", label: "Chat", icon: <Chat24Regular /> },
  { to: "/popular", label: "Ranking", icon: <Trophy24Regular /> },
  { to: "/admin", label: "Admin", icon: <Settings24Regular /> },
  { to: "/review", label: "Review", icon: <TaskListSquareLtr24Regular /> },
];

const useStyles = makeStyles({
  root: {
    display: "grid",
    gridTemplateColumns: "240px 1fr",
    minHeight: "100vh",
    backgroundColor: tokens.colorNeutralBackground2,
    "@media (max-width: 768px)": {
      gridTemplateColumns: "1fr",
    },
  },
  sidebar: {
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    display: "flex",
    flexDirection: "column",
    ...shorthands.padding(tokens.spacingVerticalL, 0),
    "@media (max-width: 768px)": {
      flexDirection: "row",
      alignItems: "center",
      gap: tokens.spacingHorizontalS,
      ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
      overflowX: "auto",
    },
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
    "@media (max-width: 768px)": {
      display: "none",
    },
  },
  brandSub: {
    fontSize: tokens.fontSizeBase200,
    fontWeight: 400,
    opacity: 0.75,
    marginTop: "2px",
    "@media (max-width: 768px)": {
      display: "none",
    },
  },
  nav: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
    "@media (max-width: 768px)": {
      flexDirection: "row",
      gap: tokens.spacingHorizontalXS,
      width: "100%",
      justifyContent: "space-around",
    },
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
    "@media (max-width: 768px)": {
      ...shorthands.padding(
        tokens.spacingVerticalXS,
        tokens.spacingHorizontalS,
      ),
      gap: tokens.spacingHorizontalXS,
      fontSize: tokens.fontSizeBase200,
      whiteSpace: "nowrap",
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
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalL,
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalXL),
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    "@media (max-width: 768px)": {
      flexWrap: "wrap",
      gap: tokens.spacingHorizontalS,
      ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
  },
  tenant: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalS,
    "@media (max-width: 768px)": {
      marginLeft: 0,
      width: "100%",
      flexWrap: "wrap",
      gap: tokens.spacingHorizontalXS,
    },
  },
  fieldBox: {
    display: "flex",
    alignItems: "center",
    gap: tokens.spacingHorizontalXS,
    "@media (max-width: 768px)": {
      flexBasis: "100%",
      width: "100%",
      minWidth: 0,
    },
  },
  fieldLabel: {
    minWidth: "48px",
    "@media (max-width: 768px)": {
      minWidth: "56px",
    },
  },
  fieldInput: {
    width: "180px",
    "@media (max-width: 768px)": {
      flex: 1,
      width: "auto",
      minWidth: 0,
    },
  },
  fieldInputShort: {
    width: "120px",
    "@media (max-width: 768px)": {
      flex: 1,
      width: "auto",
      minWidth: 0,
    },
  },
  content: {
    flex: 1,
    minWidth: 0,
    minHeight: 0,
    display: "flex",
    flexDirection: "column",
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
            <div className={styles.fieldBox}>
              <Label htmlFor="t-sector" className={styles.fieldLabel}>
                sector
              </Label>
              <Combobox
                id="t-sector"
                size="small"
                freeform
                value={tenant.sector}
                selectedOptions={[tenant.sector]}
                onOptionSelect={(_, d) =>
                  d.optionValue &&
                  setTenant({ ...tenant, sector: d.optionValue })
                }
                onChange={(e) =>
                  setTenant({
                    ...tenant,
                    sector: (e.target as HTMLInputElement).value,
                  })
                }
                className={styles.fieldInput}
              >
                {SECTOR_OPTIONS.map((s) => (
                  <Option key={s} value={s}>
                    {s}
                  </Option>
                ))}
              </Combobox>
            </div>
            <div className={styles.fieldBox}>
              <Label htmlFor="t-unit" className={styles.fieldLabel}>
                unit
              </Label>
              <Combobox
                id="t-unit"
                size="small"
                freeform
                value={tenant.unit}
                selectedOptions={[tenant.unit]}
                onOptionSelect={(_, d) =>
                  d.optionValue && setTenant({ ...tenant, unit: d.optionValue })
                }
                onChange={(e) =>
                  setTenant({
                    ...tenant,
                    unit: (e.target as HTMLInputElement).value,
                  })
                }
                className={styles.fieldInputShort}
              >
                {UNIT_OPTIONS.map((u) => (
                  <Option key={u} value={u}>
                    {u}
                  </Option>
                ))}
              </Combobox>
            </div>
            <div className={styles.fieldBox}>
              <Label htmlFor="t-user" className={styles.fieldLabel}>
                user
              </Label>
              <Combobox
                id="t-user"
                size="small"
                freeform
                value={tenant.user_id}
                selectedOptions={[tenant.user_id]}
                onOptionSelect={(_, d) =>
                  d.optionValue &&
                  setTenant({ ...tenant, user_id: d.optionValue })
                }
                onChange={(e) =>
                  setTenant({
                    ...tenant,
                    user_id: (e.target as HTMLInputElement).value,
                  })
                }
                className={styles.fieldInput}
              >
                {USER_OPTIONS.map((u) => (
                  <Option key={u} value={u}>
                    {u}
                  </Option>
                ))}
              </Combobox>
            </div>
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
