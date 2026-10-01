import { StandupView, validDay } from "@/features/standups";

export default async function AdminStandupPage({ searchParams }: PageProps<"/admin/standup">) {
  const { day } = await searchParams;
  return <StandupView day={validDay(day)} />;
}
