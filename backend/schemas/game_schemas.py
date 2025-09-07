from pydantic import BaseModel

class NewGameRequest(BaseModel):
    # player_move == None -> engine plays as white
    # player_move exists -> engine plays as black
    player_move: str | None

class NewGameResponse(BaseModel):
    new_fen: str
    move_played: str
    depth_reached: int | None
    nodes_searched: int | None
    is_book: bool
    game_id: str

class PlayMoveRequest(BaseModel):
    player_move: str
    session_id: str
    client_fen: str

class PlayMoveResponse(BaseModel):
    new_fen: str
    move_played: str
    depth_reached: int | None
    nodes_searched: int | None
    is_book: bool
    server_status: str  # 'ok', 'heavy_load', or 'busy'

class StatusResponse(BaseModel):
    status: str
