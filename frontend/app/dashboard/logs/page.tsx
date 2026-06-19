"use client";
import { createClient } from "@/lib/supabase/client";
import { useEffect, useState } from "react";
import { CardPanel } from "./cardPanel";

export default function LogsPage() {
  // const supabase = createClient();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  // const [logs, setLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const data = {
    raw: [{ header: "hello" }, { description: "hello" }],
    alert: [{ header: "security" }, { description: "security" }],
    block: [{ header: "block" }, { description: "block" }],
    isActiveRule: [{ header: "rule" }, { description: "rule" }],
    patternProfiles: [{ header: "profiles" }, { description: "profiles" }],
  };

  // useEffect(() => {
  //   supabase
  //     .from("raw_logs")
  //     .select("*")
  //     .then(({ data, error }) => {
  //       if (error) {
  //         console.error("Ошибка при получении логов:", error);
  //       } else {
  //         setLogs(data || []);
  //       }
  //       setIsLoading(false);
  //     });

  //   const channel = supabase
  //     .channel("schema-db-changes")
  //     .on(
  //       "postgres_changes",
  //       { event: "INSERT", schema: "public", table: "raw_logs" },
  //       (payload) => {
  //         setLogs((prev) => [payload.new, ...prev]);
  //       },
  //     )
  //     .subscribe();

  //   return () => {
  //     supabase.removeChannel(channel);
  //   };
  //   // eslint-disable-next-line react-hooks/exhaustive-deps
  // }, []);

  return (
    <div className="">
      <section>
        <CardPanel data={data} isLoading={isLoading} />
      </section>
    </div>
  );
}
