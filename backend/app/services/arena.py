from typing import List, Dict, Any
from fastapi import WebSocket
import uuid
import asyncio
from bson import ObjectId
from app.utils.elo import calculate_new_elos

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

    def disconnect(self, websocket: WebSocket, user_id: str | None = None, match_id: str | None = None):
        # Remove from waiting queue if exists
        self.waiting_queue = [p for p in self.waiting_queue if p["websocket"] != websocket]
        
        # If in a match, handle appropriately (e.g., notify opponent)
        # This will be handled more specifically in the endpoint loops
        pass

    async def find_match(self, user_id: str, elo_rating: int, websocket: WebSocket) -> str | None:
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

    def check_match_complete(self, match_id: str) -> bool:
        if match_id not in self.active_matches:
            return False
        match = self.active_matches[match_id]
        return all(p.get("completed", False) for p in match["players"].values())

    async def trigger_endgame(self, match_id: str, db, reason: str = "NORMAL"):
        if match_id not in self.active_matches:
            return
            
        match = self.active_matches[match_id]
        player_ids = list(match["players"].keys())
        if len(player_ids) != 2:
            return
            
        player_a_id = player_ids[0]
        player_b_id = player_ids[1]

        score_a = match["players"][player_a_id]["score"]
        score_b = match["players"][player_b_id]["score"]

        elo_a = match["players"][player_a_id]["elo"]
        elo_b = match["players"][player_b_id]["elo"]

        new_elo_a, new_elo_b = calculate_new_elos(elo_a, elo_b, score_a, score_b)

        await db["users"].update_one({"_id": ObjectId(player_a_id)}, {"$set": {"elo_rating": new_elo_a}})
        await db["users"].update_one({"_id": ObjectId(player_b_id)}, {"$set": {"elo_rating": new_elo_b}})
        
        # Determine winner
        winner_id = None
        if score_a > score_b:
            winner_id = player_a_id
        elif score_b > score_a:
            winner_id = player_b_id
        elif reason == "ABANDONED":
            # If abandoned, the still-connected player wins by default.
            # Simplified logic: If B abandoned, A wins. 
            pass

        # Send personalized message to Player A
        ws_a = match["players"][player_a_id]["websocket"]
        try:
             await ws_a.send_json({
                 "type": "match_over",
                 "winner_id": winner_id,
                 "new_elo": new_elo_a,
                 "xp_gained": 50 if winner_id == player_a_id else 15
             })
        except Exception: pass
        
        # Send personalized message to Player B
        ws_b = match["players"][player_b_id]["websocket"]
        try:
             await ws_b.send_json({
                 "type": "match_over",
                 "winner_id": winner_id,
                 "new_elo": new_elo_b,
                 "xp_gained": 50 if winner_id == player_b_id else 15
             })
        except Exception: pass

        for p_id in player_ids:
            try:
                await match["players"][p_id]["websocket"].close()
            except Exception:
                pass

        if match_id in self.active_matches:
            self.active_matches.pop(match_id, None)

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
