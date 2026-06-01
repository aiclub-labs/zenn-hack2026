import { useState, useEffect } from "react";

const KEY = "dda-tenant";

export interface TenantSel {
  sector: string;
  unit: string;
}

export function loadTenant(): TenantSel {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as TenantSel;
  } catch {
    /* noop */
  }
  return { sector: "demo", unit: "team-a" };
}

export function saveTenant(t: TenantSel): void {
  localStorage.setItem(KEY, JSON.stringify(t));
}

export function pk(t: TenantSel): string {
  return `${t.sector}#${t.unit}`;
}

export function useTenant(): [TenantSel, (t: TenantSel) => void] {
  const [t, setT] = useState<TenantSel>(loadTenant);
  useEffect(() => saveTenant(t), [t]);
  return [t, setT];
}
