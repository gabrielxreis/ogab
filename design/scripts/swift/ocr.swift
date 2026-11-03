// OCR nativo do macOS (Vision). Uso: ocr imagem.png [pt-BR,en-US]  ->  JSON com cada linha: texto, caixa em px, confiança.
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1, let img = NSImage(contentsOfFile: args[1]),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("[]"); exit(1)
}
let W = CGFloat(cg.width), H = CGFloat(cg.height)
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = true
req.recognitionLanguages = args.count > 2 ? args[2].components(separatedBy: ",") : ["pt-BR", "en-US"]
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try? handler.perform([req])
var out: [[String: Any]] = []
for obs in (req.results ?? []) {
    guard let c = obs.topCandidates(1).first else { continue }
    let b = obs.boundingBox   // normalizado, origem embaixo
    // caixa de cada palavra (para detectar negrito/cor por palavra)
    var palavras: [[String: Any]] = []
    let s = c.string
    s.enumerateSubstrings(in: s.startIndex..<s.endIndex, options: .byWords) { sub, r, _, _ in
        if let sub = sub, let wb = try? c.boundingBox(for: r)?.boundingBox {
            let ini = s.distance(from: s.startIndex, to: r.lowerBound)
            palavras.append(["p": sub, "i": ini, "n": sub.count, "x": Int(wb.minX * W), "y": Int((1 - wb.maxY) * H), "w": Int(wb.width * W), "h": Int(wb.height * H)])
        }
    }
    // inclinação da linha pelos cantos do retângulo (texto impresso na foto costuma vir torto/em perspectiva)
    let dxA = Double(obs.topRight.x - obs.topLeft.x) * Double(W), dyA = Double(obs.topRight.y - obs.topLeft.y) * Double(H)
    let ang = atan2(dyA, dxA) * 180 / Double.pi
    out.append(["texto": c.string, "conf": Double(c.confidence), "palavras": palavras, "angulo": ang,
                "x": Int(b.minX * W), "y": Int((1 - b.maxY) * H), "w": Int(b.width * W), "h": Int(b.height * H)])
}
out.sort { ($0["y"] as! Int) < ($1["y"] as! Int) }
let data = try! JSONSerialization.data(withJSONObject: out, options: [.prettyPrinted])
print(String(data: data, encoding: .utf8)!)
