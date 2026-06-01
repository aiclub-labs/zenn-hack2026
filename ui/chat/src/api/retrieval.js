import { api } from "./client";
import { RetrieveResponse } from "../types";
export async function retrieve(sector, unit, q, user_id) {
    const { data } = await api.get("/retrieve", {
        params: { sector, unit, q, user_id },
    });
    return RetrieveResponse.parse(data);
}
