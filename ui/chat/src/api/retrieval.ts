import { api } from "./client";
import { RetrieveResponse } from "../types";

export async function retrieve(
  sector: string,
  unit: string,
  q: string,
  user_id: string,
): Promise<RetrieveResponse> {
  const { data } = await api.get("/retrieve", {
    params: { sector, unit, q, user_id },
  });
  return RetrieveResponse.parse(data);
}
