import { useEffect, useState } from "react";

interface Props {
  lockedBy?: string | null;
  lockExpiresAt?: string | null;
}

export function LockBadge({ lockedBy, lockExpiresAt }: Props) {
  const [remaining, setRemaining] = useState<number>(0);
  useEffect(() => {
    if (!lockExpiresAt) return;
    const t = setInterval(() => {
      const ms = new Date(lockExpiresAt).getTime() - Date.now();
      setRemaining(Math.max(0, Math.floor(ms / 1000)));
    }, 1000);
    return () => clearInterval(t);
  }, [lockExpiresAt]);
  if (!lockedBy)
    return <span style={{ color: "#999", fontSize: 12 }}>unlocked</span>;
  const mm = Math.floor(remaining / 60);
  const ss = String(remaining % 60).padStart(2, "0");
  return (
    <span
      style={{
        background: "#fde68a",
        color: "#78350f",
        padding: "2px 6px",
        borderRadius: 4,
        fontSize: 12,
      }}
      title={`locked by ${lockedBy}`}
    >
      🔒 {lockedBy.slice(0, 6)} {mm}:{ss}
    </span>
  );
}
