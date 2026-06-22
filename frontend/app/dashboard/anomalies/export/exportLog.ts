import { createClient } from "@/lib/supabase/client";
import * as XLSX from "xlsx";

export const downloadAllAnomalousLogs = async () => {
  const supabase = createClient();

  const { data, error } = await supabase
    .from("security_alerts")
    .select(
      "created_at, username, event_type, risk_score, explanation, ip_address",
    )
    .order("created_at", { ascending: false });

  if (error) {
    throw new Error(error.message);
  }

  if (!data || data.length === 0) {
    alert("Нет данных для скачивания");
    return;
  }

  const formattedData = data.map((log) => {
    // 1. Обрабатываем JSON-объект explanation
    let explanationText = "—";

    if (log.explanation && typeof log.explanation === "object") {
      // Собираем все текстовые значения из объекта в один массив и склеиваем через " | "
      explanationText = Object.values(log.explanation)
        .filter((value) => typeof value === "string") // берем только строковые сообщения
        .join(" | "); // разделяем их красивой чертой
    } else if (typeof log.explanation === "string") {
      explanationText = log.explanation;
    }

    return {
      "Дата и время": log.created_at
        ? new Date(log.created_at).toLocaleString("ru-RU")
        : "—",
      "IP-адрес": log.ip_address || "—",
      Пользователь: log.username || "—",
      "Тип события": log.event_type || "—",
      "Уровень аномальности (%)":
        log.risk_score !== undefined ? log.risk_score : "—",
      "Описание / Причина": explanationText, // Подставляем нашу готовую строку
    };
  });

  // 3. Создаем рабочий лист Excel
  const worksheet = XLSX.utils.json_to_sheet(formattedData);

  // Настройка автоширины колонок
  const objectMaxWidth: number[] = [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  formattedData.forEach((row: any) => {
    Object.keys(row).forEach((key, i) => {
      const value = row[key] ? row[key].toString() : "";
      objectMaxWidth[i] = Math.max(
        objectMaxWidth[i] || 10,
        value.length,
        key.length,
      );
    });
  });

  // ИСПРАВЛЕНО: строго wch вместо wth
  worksheet["!cols"] = objectMaxWidth.map((w) => ({ wch: w + 2 }));

  // 4. Создаем книгу и сохраняем файл
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Аномалии");

  const timestamp = new Date().toISOString().slice(0, 10);
  XLSX.writeFile(workbook, `anomaly_report_${timestamp}.xlsx`);
};
