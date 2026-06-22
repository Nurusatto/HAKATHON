"use client";

import { useEffect, useRef, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";

type LogRow = {
  id: number;
  created_at: string;
  username: string;
  avg_requests_1m: number;
  max_requests_1m: number;
  avg_download_mb: number;
  max_download_mb: number;
};

import { RefreshCw, ShieldAlert, User } from "lucide-react";
import { Button } from "@/components/ui/button";

const GRID_LAYOUT =
  "grid grid-cols-[100px_140px_1fr_1fr_1fr_1fr] gap-4 items-center w-full min-w-[768px]";

export const List = () => {
  const PAGE_SIZE = 40;
  const supabase = createClient();
  const containerRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useInfiniteQuery<LogRow[], Error>({
    queryKey: ["userPatterns"],
    queryFn: async ({ pageParam = 0 }) => {
      const from = (pageParam as number) * PAGE_SIZE;
      const to = from + PAGE_SIZE - 1;

      const { data, error } = await supabase
        .from("user_profiles")
        .select(
          "id, created_at, username, avg_requests_1m, max_requests_1m, avg_download_mb, max_download_mb",
        )
        .order("created_at", { ascending: false })
        .range(from, to);

      if (error) throw new Error(error.message);
      return data || [];
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.length === PAGE_SIZE ? allPages.length : undefined;
    },

    staleTime: Infinity, // Данные никогда не считаются устаревшими автоматически
    refetchOnWindowFocus: false, // Отключаем перезапрос при смене вкладок браузера
    refetchOnMount: false, // Отключаем перезапрос при повторном открытии страницы/компонента
    refetchOnReconnect: false, // Отключаем перезапрос при восстановлении интернета
  });

  const allLogs = data ? data.pages.flat() : [];
  const getScrollElement = useCallback(() => containerRef.current, []);

  // eslint-disable-next-line react-hooks/incompatible-library
  const rowVirtualizer = useVirtualizer({
    count: hasNextPage ? allLogs.length + 1 : allLogs.length,
    getScrollElement,
    estimateSize: useCallback(() => 48, []),
    overscan: 10,
  });

  const virtualItems = rowVirtualizer.getVirtualItems();

  // Синхронизация горизонтального скролла шапки и тела таблицы на мобилках
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (headerRef.current) {
      headerRef.current.scrollLeft = e.currentTarget.scrollLeft;
    }
  };

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

  if (isLoading) {
    return (
      <div className="w-full bg-card border border-border rounded-xl p-4 shadow-xs">
        <div className="h-6 w-48 bg-muted rounded animate-pulse mb-6" />
        <div className="h-125 w-full bg-muted/20 border border-border/50 rounded-lg animate-pulse flex items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 border border-destructive/20 bg-destructive/5 rounded-xl text-destructive font-medium flex items-center gap-2">
        <ShieldAlert className="h-5 w-5" />
        Ошибка загрузки поведенческих паттернов
      </div>
    );
  }

  return (
    <div className="w-full bg-card border border-border rounded-xl p-3 sm:p-4 shadow-xs text-card-foreground overflow-hidden">
      {/* Адаптивная шапка с текстом и кнопкой */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-5">
        <div>
          <h2 className="text-base sm:text-lg font-semibold tracking-tight text-foreground">
            User Behavior Patterns
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Session-based user activity analysis
          </p>
        </div>

        <Button
          onClick={() => refetch()}
          disabled={isFetching}
          variant="outline"
          size="sm"
          className="gap-2 text-xs w-full sm:w-auto justify-center"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`}
          />
          {isFetching ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      {/* Обертка для шапки, скрывающая скроллбар, но скроллящаяся синхронно */}
      <div
        ref={headerRef}
        className="overflow-hidden border-x border-t border-border bg-muted/50 rounded-t-lg"
      >
        <div
          className={`${GRID_LAYOUT} px-4 py-2.5 text-xs font-medium text-muted-foreground`}
        >
          <div>Time</div>
          <div>User</div>
          <div className="text-right">Avg Req/min</div>
          <div className="text-right">Max Req/min</div>
          <div className="text-right">Avg Download</div>
          <div className="text-right">Max Download</div>
        </div>
      </div>

      {/* Контейнер скролла с горизонтальной прокруткой для мобилок */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-125 overflow-auto border-x border-b border-border bg-background rounded-b-lg custom-scrollbar outline-none focus-visible:ring-1 focus-visible:ring-ring"
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
                className="flex items-center px-4 border-b border-border/40 text-xs hover:bg-muted/40 transition-colors duration-100"
              >
                {isLoaderRow ? (
                  <div className="text-muted-foreground flex items-center gap-2 animate-pulse py-2 min-w-3xl">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary animate-ping" />
                    Загрузка данных...
                  </div>
                ) : (
                  <div className={GRID_LAYOUT}>
                    {/* Время */}
                    <span className="text-muted-foreground font-mono">
                      {log.created_at
                        ? new Date(log.created_at).toLocaleTimeString("ru-RU")
                        : "—"}
                    </span>

                    {/* Юзернейм */}
                    <span className="text-foreground font-medium flex items-center gap-1.5 truncate">
                      <User className="h-3 w-3 text-muted-foreground shrink-0" />
                      <span className="truncate">
                        {log.username || "unknown"}
                      </span>
                    </span>

                    {/* Метрики */}
                    <span className="text-right font-mono text-muted-foreground font-medium">
                      {log.avg_requests_1m ?? "0"}
                    </span>
                    <span className="text-right font-mono text-foreground font-semibold">
                      {log.max_requests_1m ?? "0"}
                    </span>
                    <span className="text-right font-mono text-muted-foreground">
                      {log.avg_download_mb
                        ? `${log.avg_download_mb} МБ`
                        : "0 МБ"}
                    </span>
                    <span className="text-right font-mono text-foreground font-medium">
                      {log.max_download_mb
                        ? `${log.max_download_mb} МБ`
                        : "0 МБ"}
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
};
