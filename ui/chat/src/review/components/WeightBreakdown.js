import { jsxs as _jsxs } from "react/jsx-runtime";
export function WeightBreakdown({ a, b, c, final }) {
    return (_jsxs("span", { title: `A(self-critic)=${a.toFixed(2)} × B(distance)=${b.toFixed(2)} × C(coverage)=${c.toFixed(2)} → ${final.toFixed(2)}`, style: {
            display: "inline-block",
            padding: "2px 6px",
            background: "#f0f0f0",
            borderRadius: 4,
            fontSize: 12,
            cursor: "help",
        }, children: ["W=", final.toFixed(2)] }));
}
