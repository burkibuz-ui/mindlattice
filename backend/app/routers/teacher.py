"""Teacher dashboard data."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ClassOverviewOut
from ..services import tutor

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.get("/overview", response_model=ClassOverviewOut)
def overview(db: Session = Depends(get_db)):
    return tutor.class_overview(db)
