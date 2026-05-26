import { jsx as _jsx } from "react/jsx-runtime";
import { useLocation, useNavigate } from "react-router-dom";
import { TabList, Tab, makeStyles, tokens, shorthands, } from "@fluentui/react-components";
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
    return (_jsx("div", { className: styles.bar, children: _jsx(TabList, { selectedValue: active, onTabSelect: (_e, d) => navigate(`/admin/${d.value}`), children: TABS.map((t) => (_jsx(Tab, { value: t.value, children: t.label }, t.value))) }) }));
}
