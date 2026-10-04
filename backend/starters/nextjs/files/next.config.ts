import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A self-contained server in .next/standalone, for Docker hosting. Vercel ignores it.
  output: "standalone",
};

export default nextConfig;
