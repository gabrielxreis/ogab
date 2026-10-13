// ============================================================
// ✏️  O GAB SÓ MEXE NESTE ARQUIVO PARA CRIAR UM CARROSSEL
// ============================================================
//
// - SLIDES: o conteúdo (tipos em src/lib/types.ts; tabela em ../CARROSSEL.md)
// - MARCA:  cores e fonte do cliente (de clientes/<empresa>/ e da pasta marca/ do cliente).
//           A fonte vai em public/fonts/marca.ttf (texto) e marca-titulo.ttf (gancho, opcional).
// - DEFAULT_FONT / SURFACE / ACCENT: "marca" usa a MARCA; os outros são os estilos prontos
//   (fontes: minimal, editorial, clean, mono, condensed; fundos: dark, white, light, paper, gradient,
//   pastel, neon, ember; destaques: yellow, red, teal, coral, orange, violet, lime, blue, fuchsia, pink, amber)
// - DEFAULT_PURPOSE: "carousel" | "presentation"
// - DEFAULT_BG: "none" | "blobs" | "grid" | "lines" | "paper" | "noise" | "bignumber" | "glow"
// - DEFAULT_FORMAT: "threads-4x5" (Instagram 4:5) | "instagram-square" | "linkedin-square" | "tiktok-9x16" | "story-9x16" | "wide-16x9"
//
// Imagens: copiar para public/images/ e usar imageSrc: "/images/arquivo.png". Sem travessão nos textos.
// ============================================================

import type { SlideData, BgType, FormatId, FontId, SurfaceId, AccentId, PurposeId } from "./lib/types";

export const MARCA = {
  nome: "Gab",
  fundo: "#0d1117",
  fundoGradiente: "radial-gradient(circle at 80% 10%, #3a1f14 0%, #141a26 45%, #0d1117 100%)" as string | undefined,
  texto: "#f5f7fb",
  textoSecundario: "rgba(245,247,251,0.6)",
  titulos: "#f5f7fb" as string | undefined,
  destaque: "#ff7a3d",
  fonteReserva: "var(--font-inter)" as string | undefined,
};

export const SLIDES: SlideData[] = [
  {
    type: "hook",
    text: "Seu Reel\nmerece um post\nque prende",
    highlight: "prende",
    highlightStyle: "italic-box",
  },
  {
    type: "number",
    badge: "01",
    bigNumber: "125",
    title: "caracteres",
    text: "É o que aparece antes do \"mais\".\nO gancho inteiro mora aqui.",
    highlight: "antes do \"mais\"",
  },
  {
    type: "list",
    badge: "02",
    title: "Um bom carrossel",
    highlight: "Uma ideia",
    items: [
      "Gancho no primeiro slide",
      "Uma ideia por slide",
      "Números no lugar de adjetivos",
      "Um CTA só no final",
    ],
  },
  {
    type: "stats",
    badge: "03",
    title: "Por que carrossel",
    stats: [
      { value: "3×", label: "mais salvamentos" },
      { value: "+40%", label: "tempo no post" },
    ],
  },
  {
    type: "comparison",
    badge: "04",
    leftLabel: "Antes",
    leftItems: ["30 hashtags", "Texto de IA", "Três CTAs"],
    rightLabel: "Depois",
    rightItems: ["3 a 5 hashtags", "Voz da marca", "Um CTA claro"],
  },
  {
    type: "quote",
    text: "Post bom é o que\nvocê salva para\nler de novo.",
    author: "regra da casa",
  },
  {
    type: "cta",
    text: "Salva este post\ne manda para o seu sócio",
    handle: "@seucliente",
  },
];

export const DEFAULT_FONT: FontId = "marca";
export const DEFAULT_SURFACE: SurfaceId = "marca";
export const DEFAULT_ACCENT: AccentId = "marca";
export const DEFAULT_PURPOSE: PurposeId = "carousel";
export const DEFAULT_BG: BgType = "glow";
export const DEFAULT_FORMAT: FormatId = "threads-4x5";
// Apresentação: DEFAULT_PURPOSE = "presentation" e DEFAULT_FORMAT = "wide-16x9".
