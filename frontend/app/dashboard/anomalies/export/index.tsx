"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";
import { downloadAllAnomalousLogs } from "@/app/dashboard/anomalies/export/exportLog";
import { toast } from "sonner"; // если используешь toast из shadcn

export function ExportLogsButton() {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await downloadAllAnomalousLogs();

      toast.success("Отчет об аномалиях успешно загружен");
    } catch (error) {
      console.error("Ошибка при экспорте:", error);
      toast.error("Не удалось получить данные из базы данных.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Button
      onClick={handleExport}
      disabled={isExporting}
      variant="outline"
      className="gap-2 border-red-200 hover:bg-red-50 hover:text-red-600 dark:border-red-900/30 dark:hover:bg-red-950/20"
    >
      {isExporting ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Generating file...
        </>
      ) : (
        <>
          <Download className="h-4 w-4" />
          Export All Anomalies (.xlsx)
        </>
      )}
    </Button>
  );
}
