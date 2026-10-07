"use client";

import { useEffect } from "react";
import { CardPanel } from "./CardPanel/cardPanel";
import { createClient } from "@/lib/supabase/client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { RealtimePostgresUpdatePayload } from "@supabase/supabase-js";
import LogList from "./logList/logList";
import { GeneratorButton } from "./generator-button";

type DatabaseStatsRow = {
  id: string;
  count: number;
  header: string | null;
  description: string;
};

type CardItem = {
  id: string;
  header: string;
  count: number;
  description: string;
};

export default function LogsPage() {
  const supabase = createClient();
  const queryClient = useQueryClient();

  const fetchDashboardStats = async (): Promise<CardItem[]> => {
    const { data, error } = await supabase
      .from<"dashboard_stats", DatabaseStatsRow>("dashboard_stats")
      .select("*");

    if (error) throw new Error(error.message);

    return (data || []).map((item) => ({
      id: item.id,
      header:
        item.header ||
        (item.id === "total_logs" ? "Системные Логи" : "Критические Алерты"),
      count: item.count,
      description: item.description,
    }));
  };

  const {
    data: stats,
    isLoading,
    isError,
    error,
  } = useQuery<CardItem[], Error>({
    queryKey: ["dashboardStats"],
    queryFn: fetchDashboardStats,
  });

  useEffect(() => {
    const statsChannel = supabase
      .channel("realtime-stats")
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "dashboard_stats" },
        (payload: RealtimePostgresUpdatePayload<DatabaseStatsRow>) => {
          const updatedRow = payload.new;

          queryClient.setQueryData<CardItem[]>(
            ["dashboardStats"],
            (oldData) => {
              if (!oldData) return oldData;

              return oldData.map((item) =>
                item.id === updatedRow.id
                  ? { ...item, count: updatedRow.count }
                  : item,
              );
            },
          );
        },
      )
      .subscribe();

    return () => {
      supabase.removeChannel(statsChannel);
    };
  }, [queryClient, supabase]);

  return (
    <section className="flex gap-3.5 flex-col">
      <GeneratorButton />
      <CardPanel
        data={stats || []}
        isLoading={isLoading}
        error={error}
        isError={isError}
      />
      <LogList />
    </section>
  );
}
