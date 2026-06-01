import { api } from "./client";
import { TurnResponse, TenantCtx } from "../types";

export async function postTurn(
  ctx: TenantCtx,
  user_content: string,
  redact: boolean,
): Promise<TurnResponse> {
  const { data } = await api.post("/turn", { ...ctx, user_content, redact });
  return TurnResponse.parse(data);
}

export async function deleteTurn(
  turn_id: string,
  sector: string,
  unit: string,
): Promise<void> {
  await api.delete(`/turn/${encodeURIComponent(turn_id)}`, {
    params: { sector, unit },
  });
}

export async function ackBanner(
  turn_id: string,
  sector: string,
  unit: string,
  user_id: string,
): Promise<void> {
  await api.post(`/turn/${encodeURIComponent(turn_id)}/ack-banner`, null, {
    params: { sector, unit, user_id },
  });
}
