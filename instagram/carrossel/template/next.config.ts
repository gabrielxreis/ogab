import type { NextConfig } from "next";

// Gab: sem o indicador do Next no canto (aparecia nos PNGs exportados pelo Chrome sem janela)
const nextConfig: NextConfig = { devIndicators: false };

export default nextConfig;
