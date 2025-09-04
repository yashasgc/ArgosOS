from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.db.engine import get_db
from app.db.crud import DocumentCRUD
from app.db.schemas import DocumentResponse

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    documents: List[DocumentResponse]

@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest, db: Session = Depends(get_db)):
    """Search documents by content"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        # Simple text search for now
        # In a full implementation, this would use vector search or AI
        documents = DocumentCRUD.search_by_content(db, request.query)
        return SearchResponse(documents=documents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


