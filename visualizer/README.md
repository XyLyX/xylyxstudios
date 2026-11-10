# XyLyX Wired Globe

The revolving studio globe, six frequency-reactive circuit wires, and gold beat ring. Uses the existing studio artwork in `assets/`.

Install Python dependencies with `python -m pip install numpy scipy pillow`. Install FFmpeg with H.264 and AAC support. The default fonts are Bahnschrift and Consolas from Windows.

From the repository root:

```powershell
python visualizer/render.py "new-song.mp3" "New Song" "new-song-visualizer.mp4" --series 002
```

For the CapCut FFmpeg build on Windows, pass `--ffmpeg "C:/path/to/ffmpeg.exe" --encoder h264_mf`. Use `--fonts` to select a folder containing both font files and `--subtitle` to change the line under the title.

Render locally with your own source audio. The track and rendered MP4 stay outside source control.
