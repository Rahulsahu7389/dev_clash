from typing import List, Dict, Any
from fastapi import WebSocket
import uuid
import asyncio

class ConnectionManager:
    def __init__(self):
        # List of dicts: {"user_id": str, "elo": int, "websocket": WebSocket}
        self.waiting_queue: List[Dict[str, Any]] = []
        
        # Dict of match_id -> {
        #   "players": {user_id: {"websocket": WebSocket, "score": int, "elo": int, "completed": bool}},
        #   "questions": List[dict],
        #   "status": str (waiting, ongoing, finished)
        # }
        self.active_matches: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def disconnect(self, websocket: WebSocket, user_id: str = None, match_id: str = None):
        # Remove from waiting queue if exists
        self.waiting_queue = [p for p in self.waiting_queue if p["websocket"] != websocket]
        
        # If in a match, handle appropriately (e.g., notify opponent)
        # This will be handled more specifically in the endpoint loops
        pass

    async def find_match(self, user_id: str, elo_rating: int, websocket: WebSocket) -> str:
        """
        Check if another user is in waiting_queue. If yes, create a match.
        Else add current user to queue.
        Returns match_id if match is found, else None.
        """
        # Simple matchmaking: pick the first person in queue
        # In a real app, we'd match by Elo range.
        if self.waiting_queue:
            opponent = self.waiting_queue.pop(0)
            match_id = str(uuid.uuid4())
            
            self.active_matches[match_id] = {
                "players": {
                    user_id: {"websocket": websocket, "score": 0, "elo": elo_rating, "completed": False, "answer_count": 0},
                    opponent["user_id"]: {"websocket": opponent["websocket"], "score": 0, "elo": opponent["elo"], "completed": False, "answer_count": 0}
                },
                "questions": [],
                "status": "waiting"
            }
            return match_id
        else:
            self.waiting_queue.append({
                "user_id": user_id,
                "elo": elo_rating,
                "websocket": websocket
            })
            return None

    async def broadcast_to_match(self, match_id: str, message: dict):
        if match_id in self.active_matches:
            players = self.active_matches[match_id]["players"]
            for player_id in players:
                ws = players[player_id]["websocket"]
                try:
                    await ws.send_json(message)
                except Exception:
                    # Handle disconnected clients
                    pass

manager = ConnectionManager()
