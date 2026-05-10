import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile

from extractor_adapter import ExtractorAdapter, ExtractorAdapterError

app = FastAPI(title="Alpha White ENEM Extractor", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract")
async def extract(prova: UploadFile = File(...), gabarito: UploadFile = File(...)) -> dict:
    adapter = ExtractorAdapter(process_questions_with_images=False)

    try:
        prova_path = _save_upload_to_tempfile(prova)
        gabarito_path = _save_upload_to_tempfile(gabarito)
        return adapter.extract(exam_pdf_path=prova_path, answer_key_pdf_path=gabarito_path)
    except (IOError, ExtractorAdapterError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno de extração: {e}") from e
    finally:
        _safe_delete(prova_path if "prova_path" in locals() else None)
        _safe_delete(gabarito_path if "gabarito_path" in locals() else None)


def _save_upload_to_tempfile(upload: UploadFile) -> str:
    original_name = os.path.basename(upload.filename or "enem_upload.pdf")
    stem, suffix = os.path.splitext(original_name)
    suffix = suffix or ".pdf"
    safe_stem = "".join(ch for ch in stem if ch.isalnum() or ch in ("_", "-")) or "enem_upload"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=f"{safe_stem}_") as tmp:
        tmp.write(upload.file.read())
        return tmp.name


def _safe_delete(path: str | None) -> None:
    if not path:
        return
    if os.path.exists(path):
        os.remove(path)
