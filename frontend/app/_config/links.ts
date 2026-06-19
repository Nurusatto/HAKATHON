import type { LucideIcon } from "lucide-react";
import { Logs, Lock, ScrollText, ShieldAlert, ScanSearch } from "lucide-react";

type item = {
  label: string;
  href: string;
  icon: LucideIcon;
};

export const group: Array<item> = [
  {
    label: "raw logs",
    href: "/dashboard/logs",
    icon: Logs,
  },
  {
    label: "Block",
    href: "/dashboard/blacklist",
    icon: Lock,
  },
  {
    label: "rules",
    href: "/dashboard/rules",
    icon: ScrollText,
  },
  {
    label: "Anomalii",
    href: "/dashboard/anomalies",
    icon: ShieldAlert,
  },
  {
    label: "Pattern",
    href: "/dashboard/patterns",
    icon: ScanSearch,
  },
];
