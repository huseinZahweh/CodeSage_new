from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from auth.token import get_current_user
from errors import APIError
from model import Submission, User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/profile/{username}")
async def get_user_profile(username: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if username != current_user["email"]:
        raise APIError("Access denied", code=403)
    
    user = db.query(User).filter(User.email == username).first()
    if not user:
        raise APIError("User not found", code=404)

    user_subs = db.query(Submission).filter(Submission.user_id == user.id).all()
    if not user_subs:
        raise APIError("User has no submissions yet", code=404)
    
    total_submissions = len(user_subs)
    solved_problems = len({
        sub.problem_id for sub in user_subs if sub.verdict == "Accepted"
    })

    submission_history = [
        {
            "id": sub.id,
            "problem_id": sub.problem_id,
            "verdict": sub.verdict,
            "submitted_at": sub.submitted_at
        }
        for sub in user_subs
    ]

    return {
        "username": username,
        "fullname": user.fullname,
        "total_submissions": total_submissions,
        "solved_problems": solved_problems,
        "submission_history": submission_history
    }