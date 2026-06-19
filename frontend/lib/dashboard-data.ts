import {
  Activity,
  Ban,
  FileWarning,
  ListChecks,
  ScanSearch,
} from "lucide-react"

export const navigation = [
  {
    title: "Все логи",
    href: "/dashboard/logs",
    icon: Activity,
    description: "Общий поток событий",
  },
  {
    title: "Аномалии",
    href: "/dashboard/anomalies",
    icon: FileWarning,
    description: "События с риском",
  },
  {
    title: "Черный лист",
    href: "/dashboard/blacklist",
    icon: Ban,
    description: "Заблокированные пользователи",
  },
  {
    title: "Правила",
    href: "/dashboard/rules",
    icon: ListChecks,
    description: "Политики детекта",
  },
  {
    title: "Паттерны",
    href: "/dashboard/patterns",
    icon: ScanSearch,
    description: "Поведение пользователей",
  },
]

export const logs = [
  {
    id: "LOG-2048",
    time: "15:42:18",
    user: "aidar.s",
    ip: "10.24.8.19",
    action: "POST /api/payment/refund",
    status: "warning",
    risk: 78,
    source: "billing-service",
    message: "Повторный refund после смены устройства",
  },
  {
    id: "LOG-2047",
    time: "15:39:02",
    user: "bot-keeper",
    ip: "185.31.44.7",
    action: "GET /admin/export",
    status: "blocked",
    risk: 96,
    source: "gateway",
    message: "Доступ к закрытому endpoint из запрещенной сети",
  },
  {
    id: "LOG-2046",
    time: "15:36:51",
    user: "dana.k",
    ip: "10.24.4.81",
    action: "PATCH /api/profile",
    status: "normal",
    risk: 18,
    source: "identity",
    message: "Обновление профиля в пределах обычного поведения",
  },
  {
    id: "LOG-2045",
    time: "15:33:11",
    user: "miras.t",
    ip: "10.24.7.13",
    action: "POST /api/auth/mfa",
    status: "anomaly",
    risk: 84,
    source: "auth-service",
    message: "Пять MFA попыток за 90 секунд",
  },
  {
    id: "LOG-2044",
    time: "15:28:45",
    user: "aliya.n",
    ip: "10.24.2.44",
    action: "GET /api/orders",
    status: "normal",
    risk: 12,
    source: "orders",
    message: "Стандартный просмотр заказов",
  },
  {
    id: "LOG-2043",
    time: "15:24:17",
    user: "unknown",
    ip: "91.203.14.88",
    action: "POST /api/auth/login",
    status: "blocked",
    risk: 99,
    source: "waf",
    message: "Credential stuffing по 42 аккаунтам",
  },
]

export const anomalies = logs.filter((log) =>
  ["warning", "anomaly", "blocked"].includes(log.status)
)

export const blacklist = [
  {
    user: "bot-keeper",
    ip: "185.31.44.7",
    reason: "Запросы к admin export",
    logs: 37,
    expires: "Бессрочно",
  },
  {
    user: "unknown",
    ip: "91.203.14.88",
    reason: "Credential stuffing",
    logs: 42,
    expires: "72 часа",
  },
  {
    user: "temp-api-17",
    ip: "45.90.12.201",
    reason: "Подмена User-Agent и токена",
    logs: 18,
    expires: "14 дней",
  },
]

export const rules = [
  {
    name: "MFA burst",
    scope: "auth-service",
    condition: ">= 5 MFA ошибок за 2 минуты",
    severity: "high",
    enabled: true,
  },
  {
    name: "Refund after device change",
    scope: "billing-service",
    condition: "refund после смены fingerprint",
    severity: "medium",
    enabled: true,
  },
  {
    name: "Admin export from public net",
    scope: "gateway",
    condition: "admin endpoint вне VPN",
    severity: "critical",
    enabled: true,
  },
  {
    name: "Order scraping",
    scope: "orders",
    condition: "> 120 order reads за 10 минут",
    severity: "medium",
    enabled: false,
  },
]

export const patterns = [
  {
    user: "aidar.s",
    baseline: "09:00-18:00, web, Almaty",
    drift: "+41%",
    signal: "billing actions ночью",
    risk: 78,
  },
  {
    user: "dana.k",
    baseline: "mobile + web, стабильный IP",
    drift: "+6%",
    signal: "обычный профиль",
    risk: 18,
  },
  {
    user: "miras.t",
    baseline: "web, офисная сеть",
    drift: "+52%",
    signal: "MFA retry burst",
    risk: 84,
  },
  {
    user: "aliya.n",
    baseline: "просмотр заказов утром",
    drift: "+4%",
    signal: "без отклонений",
    risk: 12,
  },
]
