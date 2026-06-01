import axios from "axios";

export const REVIEWER_ID_STORAGE_KEY = "ddf.reviewerId";

export const REVIEWER_PROFILES = [
  "takeshi@example.com",
  "haruka@example.com",
  "shigeru@example.com",
] as const;

export type ReviewerProfile = (typeof REVIEWER_PROFILES)[number];

export function getReviewerId(): ReviewerProfile {
  const v = localStorage.getItem(REVIEWER_ID_STORAGE_KEY);
  return (REVIEWER_PROFILES as readonly string[]).includes(v ?? "")
    ? (v as ReviewerProfile)
    : REVIEWER_PROFILES[0];
}

export function setReviewerId(id: ReviewerProfile): void {
  localStorage.setItem(REVIEWER_ID_STORAGE_KEY, id);
}

export const api = axios.create({ baseURL: "", timeout: 30_000 });

// Issue #35: send the dev-only X-Reviewer-Id override so the API can pivot
// review.decision customMetric by reviewer. Ignored in prod by app/util/auth.py.
api.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  config.headers["X-Reviewer-Id"] = getReviewerId();
  return config;
});
