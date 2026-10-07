"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Play } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

async function callGenerator(method: "GET" | "POST") {
  const response = await fetch("/api/generator", { method });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Ошибка генератора");
  }
  return data;
}

export function GeneratorButton() {
  const queryClient = useQueryClient();
  const status = useQuery<{ running: boolean }>({
    queryKey: ["generatorStatus"],
    queryFn: () => callGenerator("GET"),
    retry: false,
    refetchInterval: (query) => query.state.data?.running ? 3000 : false,
  });
  const start = useMutation({
    mutationFn: () => callGenerator("POST"),
    onSuccess: () => {
      queryClient.setQueryData(["generatorStatus"], { running: true });
      toast.success("Генератор запущен: 150 событий. Логи будут появляться постепенно.");
    },
    onError: (error: Error) => {
      toast.error(error.message);
      void queryClient.invalidateQueries({ queryKey: ["generatorStatus"] });
    },
  });
  const running = start.isPending || status.data?.running;

  return (
    <div className="flex flex-col items-end gap-2">
      <Button onClick={() => start.mutate()} disabled={running || status.isPending}>
        {running ? <Loader2 className="animate-spin" /> : <Play />}
        {running ? "Генератор работает…" : "Запустить генератор"}
      </Button>
      {status.isError && (
        <p role="status" className="text-sm text-destructive">
          {status.error.message}
        </p>
      )}
    </div>
  );
}
