"use client";

import { createClient } from "@/lib/supabase/client";
import { useQuery } from "@tanstack/react-query";
import { DataTable } from "@/components/dataTable/data-table";
import { columns } from "@/components/dataTable/blackList/columns";
import { BlockIpForm } from "@/app/dashboard/blacklist/BlockIpForm/BlockIpForm";

export default function BlacklistPage() {
  const supabase = createClient();
  const QUERY_KEY = ["blacklist"];

  const { data: blacklistData = [] } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const { data, error } = await supabase.from("security_bl").select("*");
      if (error) throw error;
      return data;
    },
  });

  return (
    <section className="flex gap-3.5 flex-col">
      <BlockIpForm />
      <DataTable columns={columns} data={blacklistData} />
    </section>
  );
}
