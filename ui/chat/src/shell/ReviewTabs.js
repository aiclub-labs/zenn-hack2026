import { jsx as _jsx } from "react/jsx-runtime";
import { useLocation, useNavigate } from "react-router-dom";
import { TabList, Tab, makeStyles, tokens, shorthands, } from "@fluentui/react-components";
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
    return (_jsx("div", { className: styles.bar, children: _jsx(TabList, { selectedValue: active, onTabSelect: (_e, d) => {
                const v = d.value;
                navigate(v ? `/review/${v}` : "/review");
            }, children: TABS.map((t) => (_jsx(Tab, { value: t.value, children: t.label }, t.value))) }) }));
}
