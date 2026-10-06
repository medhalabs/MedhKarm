import { apiGet } from "@/shared/api/client";

/** How many are on the waitlist, for "join N builders"; 0 when the count can't be read. */
export async function getWaitlistCount(): Promise<number> {
  try {
    const result = await apiGet<{ count: number }>("/public/waitlist/count", {
      next: { revalidate: 60 },
    });
    return result.count;
  } catch {
    return 0;
  }
}
