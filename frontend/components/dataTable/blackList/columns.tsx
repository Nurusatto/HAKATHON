"use client";

import { ColumnDef } from "@tanstack/react-table";
import type { blackList } from "./type";
import { Actions } from "./action";

export const columns: ColumnDef<blackList>[] = [
  {
    accessorKey: "type",
    header: "type",
  },
  {
    accessorKey: "value",
    header: "value",
  },
  {
    accessorKey: "reason",
    header: "reason",
  },
  {
    accessorKey: "is_active",
    header: "status",
  },
  {
    accessorKey: "created_at",
    header: "created",
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => {
      return <Actions data={row.original} />;
    },
  },
];
