import {
  BrandVariants,
  createLightTheme,
  Theme,
} from "@fluentui/react-components";

// KPMG Global brand ramp — anchored on KPMG Navy (#00338D, slot 80) and
// Medium Blue (#0091DA, used as the brighter interactive accent at slot 70).
// Other slots interpolated to keep Fluent's contrast guarantees.
const kpmgBrand: BrandVariants = {
  10: "#040A1F",
  20: "#0A1530",
  30: "#0F1F4D",
  40: "#142A6A",
  50: "#1A3585",
  60: "#1F3FA0",
  70: "#0091DA",
  80: "#00338D",
  90: "#1F4FB8",
  100: "#3D6BD0",
  110: "#5C87E8",
  120: "#7BA2F5",
  130: "#9ABBFA",
  140: "#B9D3FD",
  150: "#D8E8FE",
  160: "#EEF4FF",
};

export const kpmgLightTheme: Theme = {
  ...createLightTheme(kpmgBrand),
  fontFamilyBase:
    "'Segoe UI', 'Yu Gothic UI', 'Hiragino Sans', Meiryo, Arial, sans-serif",
};

// Secondary accents (used directly via tokens — not part of the brand ramp).
export const kpmgAccents = {
  purple: "#483698",
  pink: "#C800A1",
  green: "#00A3A1",
  lightBlue: "#00A3E1",
} as const;
