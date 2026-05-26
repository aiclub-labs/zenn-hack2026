import { api } from "./client";
import { CitationDetail } from "../types";

export async function getCitation(
  citation_id: string,
  sector: string,
  unit: string,
): Promise<CitationDetail> {
  const { data } = await api.get(
    `/citations/${encodeURIComponent(citation_id)}`,
    { params: { sector, unit } },
  );
  return CitationDetail.parse(data);
}
