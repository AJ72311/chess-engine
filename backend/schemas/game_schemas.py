from pydantic import BaseModel
from uuid import UUID

class NewGameRequest(BaseModel):
    # player_move == None -> engine plays as white
    # player_move exists -> engine plays as black
    player_move: str | None

class NewGameResponse(BaseModel):
    new_fen: str
    game_id: str