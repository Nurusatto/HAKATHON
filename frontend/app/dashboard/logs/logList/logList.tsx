"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";

type LogRow = {
  id: number;
  created_at: string;
  username: string;
  event_type: string;
  source_ip: string;
  download_size_mb: number;
  request_count_1m: number;
};

const PAGE_SIZE = 40;

export default function LogList() {
  "use no memo";
  const supabase = createClient();
  const queryClient = useQueryClient();
  const containerRef = useRef<HTMLDivElement>(null);

  // Состояние для паузы стрима
  const [isLive, setIsLive] = useState(true);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useInfiniteQuery<LogRow[], Error>({
    queryKey: ["rawLogs"],
    queryFn: async ({ pageParam = 0 }) => {
      const from = (pageParam as number) * PAGE_SIZE;
      const to = from + PAGE_SIZE - 1;

      const { data, error } = await supabase
        .from("raw_logs")
        .select("*")
        .order("created_at", { ascending: false })
        .range(from, to);

      if (error) throw new Error(error.message);
      return data || [];
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.length === PAGE_SIZE ? allPages.length : undefined;
    },
  });

  const allLogs = data ? data.pages.flat() : [];
  const getScrollElement = useCallback(() => containerRef.current, []);

  // eslint-disable-next-line react-hooks/incompatible-library
  const rowVirtualizer = useVirtualizer({
    count: hasNextPage ? allLogs.length + 1 : allLogs.length,
    getScrollElement,
    estimateSize: useCallback(() => 45, []),
    overscan: 15,
  });

  const virtualItems = rowVirtualizer.getVirtualItems();

  useEffect(() => {
    const lastItem = virtualItems[virtualItems.length - 1];
    if (!lastItem) return;

    if (
      lastItem.index >= allLogs.length - 1 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [
    virtualItems,
    allLogs.length,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  ]);

  // Магия паузы стрима внутри Realtime подписки
  useEffect(() => {
    const channel = supabase
      .channel("realtime-raw-logs")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "raw_logs" },
        (payload) => {
          // ЕСЛИ СТРИМ НА ПАУЗЕ — ПРОСТО ИГНОРИРУЕМ НОВЫЕ ПОСТУПЛЕНИЯ В ИНТЕРФЕЙСЕ
          if (!isLive) return;

          const newLog = payload.new as LogRow;

          queryClient.setQueryData<{
            pages: LogRow[][];
            pageParams: unknown[];
          }>(["rawLogs"], (oldData) => {
            if (!oldData) return oldData;
            const updatedPages = [...oldData.pages];
            if (updatedPages.length > 0) {
              updatedPages[0] = [newLog, ...updatedPages[0]];
            } else {
              updatedPages[0] = [newLog];
            }
            return { ...oldData, pages: updatedPages };
          });
        },
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [queryClient, supabase, isLive]); // Перезапускаем подписку при смене режима паузы

  useEffect(() => {
    if (isLive) {
      queryClient.invalidateQueries({ queryKey: ["rawLogs"] });
    }
  }, [isLive, queryClient]);

  // Скелетоны подвязаны под токены
  if (isLoading) {
    return (
      <div className="w-full bg-card border border-border rounded-xl p-4 shadow-sm">
        <div className="h-5 w-48 bg-muted rounded animate-pulse mb-6" />
        <div className="h-137.5 w-full bg-muted/40 border border-border/50 rounded-lg animate-pulse flex items-center justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent opacity-40" />
        </div>
      </div>
    );
  }

  if (isError)
    return (
      <div className="p-4 text-destructive font-medium">
        Ошибка загрузки логов
      </div>
    );

  return (
    <div className="w-full bg-card border border-border rounded-xl p-4 shadow-sm text-card-foreground">
      <div className="flex justify-between items-center mb-4 gap-1">
        <div className="flex items-center gap-2 min-w-0">
          <h2 className="text-base sm:text-lg font-semibold tracking-tight text-foreground truncate sm:overflow-visible sm:whitespace-normal">
            Живой поток событий (SIEM)
          </h2>

          {/* Добавили shrink-0, чтобы точка никогда не деформировалась */}
          <span className="flex h-2 w-2 relative shrink-0">
            {isLive && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/40 opacity-75"></span>
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isLive ? "bg-primary" : "bg-muted-foreground/50"
              }`}
            ></span>
          </span>
        </div>

        <button
          onClick={() => setIsLive(!isLive)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium cursor-pointer transition-all duration-200 shadow-xs
            ${
              isLive
                ? "bg-muted/50 hover:bg-muted border-border text-foreground"
                : "bg-primary text-primary-foreground border-primary hover:opacity-90"
            }`}
        >
          {isLive ? (
            <>
              <svg className="h-3 w-3 fill-current" viewBox="0 0 24 24">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
              </svg>
              <span>Пауза стрима</span>
            </>
          ) : (
            <>
              <svg className="h-3 w-3 fill-current" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              <span>Возобновить трансляцию</span>
            </>
          )}
        </button>
      </div>

      <div
        ref={containerRef}
        className="h-137.5 overflow-auto border border-border bg-muted/20 rounded-lg custom-scrollbar outline-none focus-visible:ring-1 focus-visible:ring-ring"
        style={{ contain: "strict" }}
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            width: "100%",
            position: "relative",
          }}
        >
          {virtualItems.map((virtualItem) => {
            const isLoaderRow = virtualItem.index > allLogs.length - 1;
            const log = allLogs[virtualItem.index];

            return (
              <div
                key={virtualItem.key}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  height: `${virtualItem.size}px`,
                  transform: `translateY(${virtualItem.start}px)`,
                }}
                className="flex items-center px-4 border-b border-border/40 font-mono text-xs hover:bg-accent hover:text-accent-foreground transition-colors duration-150"
              >
                {isLoaderRow ? (
                  <div className="text-muted-foreground flex items-center gap-2 animate-pulse">
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                    Подгрузка старых логов...
                  </div>
                ) : (
                  <div className="flex w-full justify-between items-center gap-4">
                    <span className="text-muted-foreground whitespace-nowrap">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </span>

                    <span className="text-primary font-semibold tracking-mono whitespace-nowrap min-w-27.5">
                      {log.source_ip}
                    </span>

                    <span className="text-foreground font-medium min-w-22.5 truncate">
                      {log.username}
                    </span>

                    <span className="text-accent-foreground flex-1 font-medium truncate">
                      {log.event_type}
                    </span>

                    <div className="text-right whitespace-nowrap min-w-20">
                      {log.download_size_mb >= 1000 ? (
                        <span className="inline-flex items-center rounded-md bg-destructive/10 px-2 py-0.5 text-[11px] font-bold text-destructive animate-pulse">
                          {(log.download_size_mb / 1000).toFixed(1)} GB
                        </span>
                      ) : log.download_size_mb >= 100 ? (
                        <span className="inline-flex items-center rounded-md bg-amber-500/10 px-2 py-0.5 text-[11px] font-semibold text-amber-500 dark:text-amber-400">
                          {log.download_size_mb} MB
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-xs font-medium">
                          {log.download_size_mb.toFixed(0)} MB
                        </span>
                      )}
                    </div>

                    <span className="text-muted-foreground text-right whitespace-nowrap">
                      {log.request_count_1m} req/m
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
