import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
export function LockBadge({ lockedBy, lockExpiresAt }) {
    const [remaining, setRemaining] = useState(0);
    useEffect(() => {
        if (!lockExpiresAt)
            return;
        const t = setInterval(() => {
            const ms = new Date(lockExpiresAt).getTime() - Date.now();
            setRemaining(Math.max(0, Math.floor(ms / 1000)));
        }, 1000);
        return () => clearInterval(t);
    }, [lockExpiresAt]);
    if (!lockedBy)
        return _jsx("span", { style: { color: "#999", fontSize: 12 }, children: "unlocked" });
    const mm = Math.floor(remaining / 60);
    const ss = String(remaining % 60).padStart(2, "0");
    return (_jsxs("span", { style: {
            background: "#fde68a",
            color: "#78350f",
            padding: "2px 6px",
            borderRadius: 4,
            fontSize: 12,
        }, title: `locked by ${lockedBy}`, children: ["\uD83D\uDD12 ", lockedBy.slice(0, 6), " ", mm, ":", ss] }));
}
