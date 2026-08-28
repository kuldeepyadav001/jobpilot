import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.resume import Resume
from api.schemas import ResumeOut
from engine.parser import parse_resume_file

router = APIRouter(prefix="/resumes", tags=["Resumes"])

UPLOAD_DIR = "/app/resumes"


@router.get("", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db)):
    return db.query(Resume).order_by(Resume.created_at.desc()).all()


@router.post("", response_model=ResumeOut, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    name: str = Form(...),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "docx"):
        raise HTTPException(400, "Only PDF and DOCX files are supported.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        parsed_text = parse_resume_file(file_path, ext)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(500, f"Failed to parse resume: {e}")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    resume = Resume(
        name=name,
        file_path=file_path,
        file_type=ext,
        tags=tag_list,
        version=1,
        parsed_text=parsed_text,
        is_active=True,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(404, "Resume not found")
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    db.delete(resume)
    db.commit()