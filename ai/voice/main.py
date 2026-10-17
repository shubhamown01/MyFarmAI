from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import tempfile
import os

app = FastAPI(title="My Farm AI Voice Service")

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)


@app.get("/health")
def health():
    return {
        "service": "voice",
        "status": "ok"
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):

    suffix = os.path.splitext(file.filename or ".wav")[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp:

        temp.write(await file.read())
        temp_path = temp.name

    try:
        segments, info = model.transcribe(
            temp_path,
            language="hi"
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return {
            "language": info.language,
            "text": text
        }

    finally:
        os.remove(temp_path)
