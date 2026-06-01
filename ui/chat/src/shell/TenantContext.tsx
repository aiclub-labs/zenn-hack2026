import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const KEY = "dda-tenant";

export interface Tenant {
  sector: string;
  unit: string;
  user_id: string;
}

const DEFAULT: Tenant = {
  sector: "manufacturing-s8b",
  unit: "line-A",
  user_id: "haruka@example.com",
};

interface Ctx {
  tenant: Tenant;
  setTenant: (t: Tenant) => void;
  sessionId: string;
}

const TenantCtx = createContext<Ctx | null>(null);

function load(): Tenant {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...DEFAULT, ...JSON.parse(raw) };
  } catch {
    /* noop */
  }
  return DEFAULT;
}

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenantState] = useState<Tenant>(load);
  const [sessionId] = useState(() => crypto.randomUUID());

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(tenant));
    } catch {
      /* noop */
    }
  }, [tenant]);

  const value = useMemo<Ctx>(
    () => ({ tenant, setTenant: setTenantState, sessionId }),
    [tenant, sessionId],
  );

  return <TenantCtx.Provider value={value}>{children}</TenantCtx.Provider>;
}

export function useTenantCtx(): Ctx {
  const v = useContext(TenantCtx);
  if (!v) throw new Error("useTenantCtx must be used inside TenantProvider");
  return v;
}
