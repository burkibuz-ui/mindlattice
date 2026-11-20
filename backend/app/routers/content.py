from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Concept, Problem
from ..schemas import ConceptOut, GraphOut, ProblemOut
from ..services.tutor import NotFound, load_graph

router = APIRouter(prefix="/api", tags=["content"])


@router.get("/concepts", response_model=list[ConceptOut])
def list_concepts(db: Session = Depends(get_db)):
    graph = load_graph(db)
    concepts = db.scalars(select(Concept))
    by_id = {c.id: c for c in concepts}
    return [ConceptOut(id=cid, name=by_id[cid].name, description=by_id[cid].description,
                       prerequisites=graph.prerequisites(cid))
            for cid in graph.topological_order()]


@router.get("/graph", response_model=GraphOut)
def get_graph(db: Session = Depends(get_db)):
    nodes = list_concepts(db)
    edges = [{"from": prereq, "to": node.id} for node in nodes for prereq in node.prerequisites]
    return GraphOut(nodes=nodes, edges=edges)


@router.get("/problems", response_model=list[ProblemOut])
def list_problems(db: Session = Depends(get_db)):
    return db.scalars(select(Problem).order_by(Problem.position)).all()


@router.get("/problems/{problem_id}", response_model=ProblemOut)
def get_problem(problem_id: str, db: Session = Depends(get_db)):
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise NotFound(f"Problem '{problem_id}' not found")
    return problem
