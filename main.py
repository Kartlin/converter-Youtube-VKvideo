# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI()

# Подключаем статику (фронтенд)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

class ConvertRequest(BaseModel):
    url: str
    format: str  # "video" или "audio"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.post("/convert")
def convert(req: ConvertRequest):
    if req.format not in ("video", "audio"):
        raise HTTPException(400, "format must be 'video' or 'audio'")
    
    job_id = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")
    
    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
    }

    if req.format == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            filename = ydl.prepare_filename(info)
            # для аудио после конвертации расширение меняется на .mp3
            if req.format == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"
            if not os.path.exists(filename):
                raise HTTPException(500, "File not found after conversion")
            return FileResponse(filename, media_type="application/octet-stream", filename=os.path.basename(filename))
    except Exception as e:
        raise HTTPException(500, str(e))
