import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useEffect, useMemo, useState, } from "react";
const KEY = "dda-tenant";
const DEFAULT = {
    sector: "manufacturing-s8b",
    unit: "line-A",
    user_id: "haruka@example.com",
};
const TenantCtx = createContext(null);
function load() {
    try {
        const raw = localStorage.getItem(KEY);
        if (raw)
            return { ...DEFAULT, ...JSON.parse(raw) };
    }
    catch {
        /* noop */
    }
    return DEFAULT;
}
export function TenantProvider({ children }) {
    const [tenant, setTenantState] = useState(load);
    const [sessionId] = useState(() => crypto.randomUUID());
    useEffect(() => {
        try {
            localStorage.setItem(KEY, JSON.stringify(tenant));
        }
        catch {
            /* noop */
        }
    }, [tenant]);
    const value = useMemo(() => ({ tenant, setTenant: setTenantState, sessionId }), [tenant, sessionId]);
    return _jsx(TenantCtx.Provider, { value: value, children: children });
}
export function useTenantCtx() {
    const v = useContext(TenantCtx);
    if (!v)
        throw new Error("useTenantCtx must be used inside TenantProvider");
    return v;
}
