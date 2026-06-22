"use client";

import { createClient } from "@/lib/supabase/client";
import { useQuery } from "@tanstack/react-query";
import { DataTable } from "@/components/dataTable/data-table";
import { columns } from "@/components/dataTable/rules/column";

export default function RulesPage() {
  const supabase = createClient();
  const QUERY_KEY = ["rulesList"];

  const { data = [] } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const { data, error } = await supabase.from("security_rules").select("*");
      if (error) throw error;
      console.log(data);
      return data;
    },
  });

  return (
    <section className="flex flex-col gap-4">
      <DataTable columns={columns} data={data} />
    </section>
  );
}
