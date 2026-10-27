#!/usr/bin/env bash
# JAAY — final audio mix: original score + French narration (ducked) + limiter ceiling
set -euo pipefail
cd "$(dirname "$0")/.."
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
VO=audio/vo
python3 src/audio_gen.py

# narration cue sheet (seconds) — matches the cut
# vo01 0.35 | vo02 4.75 | vo03 10.30 | vo04 16.35 | vo05 20.65 | vo06 24.75 | vo07 31.05 | vo08 36.35
D1=350; D2=4750; D3=10300; D4=16350; D5=20650; D6=24750; D7=31050; D8=36350

"$FF" -y -hide_banner -loglevel error \
 -i build/score.wav -i "$VO/vo01.mp3" -i "$VO/vo02.mp3" -i "$VO/vo03.mp3" \
 -i "$VO/vo04.mp3" -i "$VO/vo05.mp3" -i "$VO/vo06.mp3" -i "$VO/vo07.mp3" -i "$VO/vo08.mp3" \
 -filter_complex "\
[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D1}|${D1},volume=1.0[v1];\
[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D2}|${D2},volume=1.0[v2];\
[3:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D3}|${D3},volume=1.0[v3];\
[4:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D4}|${D4},volume=1.0[v4];\
[5:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D5}|${D5},volume=1.0[v5];\
[6:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D6}|${D6},volume=1.0[v6];\
[7:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D7}|${D7},volume=1.0[v7];\
[8:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay=${D8}|${D8},volume=1.0[v8];\
[v1][v2][v3][v4][v5][v6][v7][v8]amix=inputs=8:normalize=0[vo];\
[vo]highpass=f=95,equalizer=f=190:t=q:w=1.2:g=-7,equalizer=f=420:t=q:w=1.4:g=-3,equalizer=f=1100:t=q:w=1.2:g=5,equalizer=f=2600:t=q:w=1.1:g=10,equalizer=f=4800:t=q:w=1.2:g=9,highshelf=f=7000:g=5,crystalizer=i=3,acompressor=threshold=-20dB:ratio=3:attack=6:release=150:makeup=4,alimiter=limit=0.82:level=disabled[voc];\
[0:a]highpass=f=36,equalizer=f=250:t=q:w=1.3:g=-5.5,equalizer=f=420:t=q:w=1.6:g=-3,equalizer=f=1000:t=q:w=1.0:g=1.5,highshelf=f=6000:g=2.0,volume=0.58[bed];\
[bed][voc]amix=inputs=2:normalize=0,alimiter=limit=0.92:attack=4:release=80:level=disabled,aresample=48000[out]" \
 -map "[out]" -t 45 -c:a pcm_s16le build/mix.wav

# QA stems
"$FF" -y -hide_banner -loglevel error -i build/score.wav -af "highpass=f=36,equalizer=f=250:t=q:w=1.3:g=-5.5,equalizer=f=420:t=q:w=1.6:g=-3,highshelf=f=6000:g=2.0,volume=0.58" -c:a pcm_s16le build/bed.wav
echo "mix ready: build/mix.wav"
