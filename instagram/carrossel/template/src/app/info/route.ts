// Gab: quantos slides e o tamanho do quadro, para exportar sem clique (instagram/carrossel/exportar.py).
import { SLIDES, DEFAULT_FORMAT } from "../../slides";
import { FORMAT_PRESETS } from "../../lib/presets";

export const dynamic = "force-dynamic";

export function GET() {
  const f = FORMAT_PRESETS[DEFAULT_FORMAT];
  return Response.json({ total: SLIDES.length, w: f.w, h: f.h, tipos: SLIDES.map((s) => s.type) });
}
