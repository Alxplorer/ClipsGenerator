import type { NextConfig } from "next";

if (process.env.RENDER === "true") {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL;
  let apiUrl: URL | null = null;
  try {
    apiUrl = value ? new URL(value) : null;
  } catch {
    // The error below explains which deployment setting needs correction.
  }
  if (
    apiUrl === null
    || apiUrl.protocol !== "https:"
    || value !== apiUrl.origin
    || apiUrl.hostname === "localhost"
    || apiUrl.hostname.endsWith(".localhost")
    || apiUrl.hostname === "0.0.0.0"
    || apiUrl.hostname.startsWith("127.")
    || apiUrl.hostname === "[::1]"
  ) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL debe ser el origen HTTPS público de la API.");
  }
}

const nextConfig: NextConfig = {
  output: "export",
};

export default nextConfig;
