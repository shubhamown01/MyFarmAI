from fastapi import FastAPI

app = FastAPI(title="My Farm AI Backend")


@app.get("/")
def root():
    return {
        "project": "My Farm AI",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }
