import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from run_quizforge import run_quizforge_job

app = FastAPI()


class SpecRequest(BaseModel):
    spec_text: str


@app.post("/generate")
def generate_quiz(req: SpecRequest):
    try:
        job_id = str(uuid.uuid4())
        output_dir = os.path.join("Finished_Exports", job_id)
        os.makedirs(output_dir, exist_ok=True)

        result_file = run_quizforge_job(
            spec_text=req.spec_text,
            output_dir=output_dir,
        )

        abs_path = os.path.abspath(result_file)

        return {
            "status": "success",
            "file": os.path.basename(result_file),
            "path": abs_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
