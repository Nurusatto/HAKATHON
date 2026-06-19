import type { NextConfig } from "next";
import dotenv from "dotenv";
import path from "path";

dotenv.config({
  path: path.resolve("../.env"),
});

const nextConfig: NextConfig = {};

export default nextConfig;
