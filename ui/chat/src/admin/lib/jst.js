// All times displayed in JST per WT-C requirement.
const JST = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
});
export function formatJst(iso) {
    try {
        return JST.format(new Date(iso)) + " JST";
    }
    catch {
        return iso;
    }
}
