import { api } from "./client";
import { HearoutTurn } from "../types";

export async function startHearout(args: {
  gap_event_id: string;
  user_id: string;
  sector: string;
  unit: string;
}): Promise<HearoutTurn> {
  const { data } = await api.post("/hearout/start", args);
  return HearoutTurn.parse(data);
}

export async function respondHearout(
  session_id: string,
  answer: string,
): Promise<HearoutTurn> {
  const { data } = await api.post(
    `/hearout/${encodeURIComponent(session_id)}/respond`,
    { answer },
  );
  return HearoutTurn.parse(data);
}

export async function skipHearout(session_id: string): Promise<unknown> {
  const { data } = await api.post(
    `/hearout/${encodeURIComponent(session_id)}/skip`,
  );
  return data;
}
