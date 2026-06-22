"use client";

import { ColumnDef } from "@tanstack/react-table";
import { Actions } from "./action";
import type { Rules } from "./type";

export const columns: ColumnDef<Rules>[] = [
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ row }) => {
      const date = row.original.created_at;
      return date ? new Date(date).toLocaleString("ru-RU") : "—";
    },
  },
  {
    accessorKey: "event_type",
    header: "Event",
  },
  {
    accessorKey: "description",
    header: "Description",
  },
  {
    accessorKey: "risk_weight",
    header: "Risk",
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => {
      const isActive = row.original.is_active;
      return (
        <span
          className={
            isActive ? "text-muted-foreground" : "text-red-600 font-medium"
          }
        >
          {isActive ? "Active" : "No active"}
        </span>
      );
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => {
      return <Actions data={row.original} />;
    },
  },
];
