// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const renderExplanation = (explanation: any) => {
  if (!explanation || Object.keys(explanation).length === 0)
    return "Причины не указаны";

  return (
    <div className="space-y-1.5 text-xs max-w-xs p-1">
      {Object.entries(explanation).map(([key, value]) => {
        // Красивое форматирование ключей
        const title = key
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());
        return (
          <div
            key={key}
            className="border-b border-border/40 last:border-0 pb-1 last:pb-0 "
          >
            <span className="font-bold text-amber-400 block text-[10px] uppercase tracking-wider">
              {title}:{" "}
            </span>
            <span className="text-zinc-300 leading-normal">
              {String(value)}
            </span>
          </div>
        );
      })}
    </div>
  );
};
