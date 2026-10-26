"""Gera as mídias de teste em teste/midia com ffmpeg (não vão no zip: ~100 MB). Rodar antes dos testes t2..t11."""
import os, subprocess

import sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "midia")
os.makedirs(D, exist_ok=True)


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


ff("-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=20", "-f", "lavfi", "-i", "sine=f=440:d=20",
   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", os.path.join(D, "bruto.mp4"))
ff("-f", "lavfi", "-i", "smptebars=s=1920x1080:r=30:d=6", "-f", "lavfi", "-i", "sine=f=880:d=6",
   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", os.path.join(D, "take_01.mp4"))
ff("-f", "lavfi", "-i", "mandelbrot=s=1920x1080:r=30", "-t", "6", "-f", "lavfi", "-i", "sine=f=660:d=6",
   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", os.path.join(D, "take_02.mp4"))
ff("-f", "lavfi", "-i", "sine=f=220:d=40", "-ar", "48000", os.path.join(D, "musica.wav"))
# Motion com alfa de verdade (quadrado amarelo opaco, resto transparente), ProRes 4444 sem áudio.
for nome, dur in (("motion.mov", 3), ("motion2.mov", 2)):
    ff("-f", "lavfi", "-i", f"color=c=yellow:s=1080x1920:r=30:d={dur},format=rgba,"
       "geq=r='255':g='220':b='0':a='if(between(X,340,740)*between(Y,860,1060),255,0)'",
       "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", os.path.join(D, nome))
with open(os.path.join(D, "legenda.srt"), "w", encoding="utf-8", newline="\r\n") as f:
    f.write("1\n00:00:00,500 --> 00:00:02,000\nOLÁ, TESTE DO GAB\n\n2\n00:00:02,200 --> 00:00:04,000\nLEGENDA SEM OLHAR A TELA\n\n")
print("mídias em", D, sorted(os.listdir(D)))
