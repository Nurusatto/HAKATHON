import * as yup from "yup";

const ipRegex =
  /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

export const schema = yup
  .object({
    // 🔒 IP строго обязателен и должен проходить через твой Regex
    ip: yup
      .string()
      .required("IP address is strictly required")
      .matches(ipRegex, "Invalid IP address format"),

    // 🔓 Причина может быть пустой, но гарантированно вернет string вместо undefined
    reason: yup.string().ensure(),
  })
  .required();
