from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth.token import get_current_user
from database import SessionLocal
from model import Problem, Submission as SubmissionModel
from models.problems import Submission  
from errors import APIError

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/problems")
async def get_problems(db: Session = Depends(get_db)):
    problems = db.query(Problem).all()
    return [
        {"id": p.id, "title": p.title}
        for p in problems
    ]

@router.get("/problems/{problem_id}")
async def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise APIError("Problem not found", code=404, details={"problem_id": problem_id})

    total_submissions = db.query(SubmissionModel).filter(SubmissionModel.problem_id == problem_id).count()
    accepted_submissions = db.query(SubmissionModel).filter(
        SubmissionModel.problem_id == problem_id,
        SubmissionModel.verdict == "Accepted"
    ).count()

    return {
        "id": problem.id,
        "title": problem.title,
        "description": problem.description,
        "total_submissions": total_submissions,
        "accepted_submissions": accepted_submissions
    }

@router.post("/submit")
async def submit_solution(
    submission: Submission,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
    if not problem:
        raise APIError("Problem not found", code=404, details={"problem_id": submission.problem_id})

    new_submission = SubmissionModel(
        problem_id=submission.problem_id,
        code=submission.code,
        verdict=submission.verdict,
        user_id=current_user["id"]  
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return {
        "message": "Successfully Submitted!",
        "problem_id": new_submission.problem_id,
        "user_id": new_submission.user_id
    }

@router.get("/submissions/{problem_id}")
async def get_submissions(problem_id: int, db: Session = Depends(get_db)):
    submissions = db.query(SubmissionModel).filter(SubmissionModel.problem_id == problem_id).all()
    if not submissions:
        raise APIError("No submissions found for this problem", code=404, details={"problem_id": problem_id})
    return submissions
