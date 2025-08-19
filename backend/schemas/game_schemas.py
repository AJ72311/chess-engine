from pydantic import BaseModel

class NewGameRequest(BaseModel):
    # player_move == None -> engine plays as white
    # player_move exists -> engine plays as black
    player_move: str | None

class NewGameResponse(BaseModel):
    new_fen: str
    game_id: str

class PlayMoveRequest(BaseModel):
    player_move: str
    session_id: str
    client_fen: str

class PlayMoveResponse(BaseModel):
    new_fen: str
