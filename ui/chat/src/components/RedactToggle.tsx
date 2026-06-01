interface Props {
  value: boolean;
  onChange: (v: boolean) => void;
}

export function RedactToggle({ value, onChange }: Props) {
  return (
    <label
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: 13,
        color: value ? "#b91c1c" : "#374151",
      }}
    >
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
      />
      Redact 機密 (本文を保存しない)
      {value && <span aria-label="redact-on">🔒</span>}
    </label>
  );
}
