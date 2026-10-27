#!/usr/bin/env bash
# JAAY — déclinaisons et fichiers d'accompagnement
set -euo pipefail
cd "$(dirname "$0")/.."
FF=$(cat .ffmpeg_path)
M=out/JAAY_1000F_POUR_COMMENCER_GRAND_9x16_60fps.mp4

# 1:1 (feed) et 4:5 (Instagram), recadrés sur la zone d'information
# 1:1 et 4:5 : fond flou + image entière (aucun texte coupé)

  

  

# affiche (dernière image stable) + planche de contrôle
"$FF" -y -hide_banner -loglevel error -ss 44.2 -i "$M" -frames:v 1 out/JAAY_affiche_finale.png
"$FF" -y -hide_banner -loglevel error -i "$M" -vf "fps=1/1.5,scale=243:432,tile=6x5:padding=6:margin=6:color=0x111111" \
  -frames:v 1 out/qa/contact_sheet.png

# audio séparés (montage / doublage)
"$FF" -y -hide_banner -loglevel error -i "$M" -vn -c:a aac -b:a 192k out/JAAY_mix_final.m4a

# sous-titres français incrustables
if [ -f docs/jaay.fr.srt ]; then
  "$FF" -y -hide_banner -loglevel error -i "$M" \
    -vf "subtitles=docs/jaay.fr.srt:force_style='FontName=Inter,FontSize=11,Bold=1,PrimaryColour=&H00F2F7F2,OutlineColour=&H000B1F16,BorderStyle=3,Outline=1.1,Shadow=0,BackColour=&H98030A07,Alignment=2,MarginV=130,MarginL=70,MarginR=70'" \
    -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -c:a copy out/JAAY_9x16_sous-titre_fr.mp4
fi
echo "declinaisons prêtes"
