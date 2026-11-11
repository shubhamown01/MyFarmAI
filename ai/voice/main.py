import hmac
import os
import tempfile

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from faster_whisper import WhisperModel

app = FastAPI(title="My Farm AI Voice Service")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB (SEC-028 request-size cap)
_CHUNK = 1024 * 1024

model = WhisperModel("small", device="cpu", compute_type="int8")


def require_token(authorization: str | None = Header(default=None)) -> None:
    """Fail closed unless VOICE_SERVICE_TOKEN is set and matches the bearer token."""
    expected = os.environ.get("VOICE_SERVICE_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="voice service token not configured",
        )
    provided = ""
    if authorization and authorization.startswith("Bearer "):
        provided = authorization[len("Bearer ") :]
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health():
    return {"service": "voice", "status": "ok"}


@app.post("/transcribe", dependencies=[Depends(require_token)])
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or ".wav")[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp_path = temp.name
        total = 0
        try:
            while True:
                chunk = await file.read(_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="file too large",
                    )
                temp.write(chunk)
        except Exception:
            os.remove(temp_path)
            raise

    try:
        segments, info = model.transcribe(temp_path, language="hi")

        text = " ".join(segment.text.strip() for segment in segments)

        return {"language": info.language, "text": text}

    finally:
        os.remove(temp_path)
