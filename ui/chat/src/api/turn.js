import { api } from "./client";
import { TurnResponse } from "../types";
export async function postTurn(ctx, user_content, redact) {
    const { data } = await api.post("/turn", { ...ctx, user_content, redact });
    return TurnResponse.parse(data);
}
export async function deleteTurn(turn_id, sector, unit) {
    await api.delete(`/turn/${encodeURIComponent(turn_id)}`, {
        params: { sector, unit },
    });
}
export async function ackBanner(turn_id, sector, unit, user_id) {
    await api.post(`/turn/${encodeURIComponent(turn_id)}/ack-banner`, null, {
        params: { sector, unit, user_id },
    });
}
