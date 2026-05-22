8 tracks · ~13 minutes.

Track one available here: https://soundcloud.com/jongerhardson/experimental_rap-2 

I like JPEGMAFIA this is just me taking a stupid joke too far. A python scripts generates some beats and uses yt-dlp to download audio from talks given by the "experimental" artist/poet/critic David Antin, samples the talks, and mixes it all together. 

License: CC0 only becvause CC negative infinity does not exist. 

## Quick start

```bash
pip install -r requirements.txt     # numpy, scipy, yt-dlp  (+ ffmpeg on PATH)
python album.py                     # downloads sources, builds & masters all 8 MP3s
```

**note** ffmpeg is needed on PATH (system binary, not pip), and you also need [faster-whisper](https://github.com/SYSTRAN/faster-whisper) if you want to make full transcripts to fuck around with what gets sampled.



Output: `01 - would that count.mp3` … `08 - it is narrow it is dark.mp3`
(320 kbps, loudness-normalized to −14 LUFS, tagged).

```bash
python album.py 1 6 8        # build only these tracks (fetches just the sources they need)
python album.py --no-master  # raw WAVs only, skip the ffmpeg mastering step
python album.py --skip-download   # use antin_*.wav already on disk
