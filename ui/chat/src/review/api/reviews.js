import { api } from "./client";
import { FormalizationTicket, } from "../types";
export async function listReviews(priorityOnly = false) {
    const { data } = await api.get("/reviews", {
        params: { priority_only: priorityOnly },
    });
    return data.map((x) => FormalizationTicket.parse(x));
}
export async function listConflictReviews() {
    const { data } = await api.get("/reviews/conflict");
    return data.map((x) => FormalizationTicket.parse(x));
}
export async function lockReview(id) {
    const { data } = await api.post(`/reviews/${encodeURIComponent(id)}/lock`);
    return data;
}
export async function unlockReview(id) {
    await api.post(`/reviews/${encodeURIComponent(id)}/unlock`);
}
export async function decideReview(id, sector, unit, decision) {
    const { data } = await api.post(`/reviews/${encodeURIComponent(id)}/decision`, { decision }, { params: { sector, unit } });
    return data;
}
export async function decideConflict(id, sector, unit, decision) {
    const { data } = await api.post(`/reviews/${encodeURIComponent(id)}/conflict`, { decision }, { params: { sector, unit } });
    return data;
}
export async function getSelfApproval() {
    const { data } = await api.get("/reviews/self-approval");
    return data;
}
export async function getPriorityMode() {
    const { data } = await api.get("/reviews/priority-mode");
    return data;
}
