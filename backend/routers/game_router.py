from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from services import game_service

router = APIRouter()

class NewGameRequest(BaseModel):
    fen: str

@router.post('/new-game')
async def new_game(request: NewGameRequest):
    # run search in thread pool to avoid blocking server event loop
    res_fen = await run_in_threadpool(game_service.new_game, request.fen)

    if res_fen is None:
        raise HTTPException(status_code=400, detail='Engine could not find a valid move')
    
    return res_fen