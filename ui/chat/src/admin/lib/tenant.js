import { useState, useEffect } from "react";
const KEY = "dda-tenant";
export function loadTenant() {
    try {
        const raw = localStorage.getItem(KEY);
        if (raw)
            return JSON.parse(raw);
    }
    catch {
        /* noop */
    }
    return { sector: "demo", unit: "team-a" };
}
export function saveTenant(t) {
    localStorage.setItem(KEY, JSON.stringify(t));
}
export function pk(t) {
    return `${t.sector}#${t.unit}`;
}
export function useTenant() {
    const [t, setT] = useState(loadTenant);
    useEffect(() => saveTenant(t), [t]);
    return [t, setT];
}
