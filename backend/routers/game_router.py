from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from services import game_service
from schemas.game_schemas import NewGameRequest, NewGameResponse

router = APIRouter()

@router.post('/new-game', response_model = NewGameResponse)
async def new_game(request: NewGameRequest):
    try:
        # run search in thread pool to avoid blocking server event loop
        new_game = await run_in_threadpool(game_service.new_game, request.player_move)
        
        return NewGameResponse(
            new_fen = new_game[0],
            game_id = new_game[1],
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except RuntimeError as e:
        print(f"A server-side engine error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal engine error occurred')

    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail='An internal server error occurred')