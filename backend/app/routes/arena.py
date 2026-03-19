from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.security import get_current_user_ws
from app.core.database import get_database
from app.services.arena import manager
from app.services.llm import generate_mcqs
import asyncio
import logging
from bson import ObjectId

router = APIRouter(prefix="/ws", tags=["Arena"])
logger = logging.getLogger(__name__)

@router.websocket("/arena")
async def websocket_arena(
    websocket: WebSocket,
    token: str = Query(...)
):
    try:
        user_id = await get_current_user_ws(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    elo = user.get("elo_rating", 1200)
    user_name = user.get("username", "Competitor")
    
    # Try matchmaking logic
    match_id = await manager.find_match(user_id, elo, websocket)
    
    if match_id:
        match = manager.active_matches[match_id]
        
        # Inform both players that they have matched
        players_list = list(match["players"].keys())
        p1 = players_list[0]
        p2 = players_list[1]
        
        # We need to send 'match_found' with opponent info
        try:
            await match["players"][p1]["websocket"].send_json({
                "type": "match_found",
                "opponent": f"Player {p2[-4:]}" # Defaulting opponent name to trailing ID chars
            })
            await match["players"][p2]["websocket"].send_json({
                "type": "match_found",
                "opponent": f"Player {p1[-4:]}"
            })
        except Exception:
            pass
            
        # Start Battle automatically
        match["status"] = "ongoing"
        try:
            questions = await generate_mcqs("General Knowledge Arena")
            match["questions"] = questions
            await manager.broadcast_to_match(match_id, {
                "type": "battle_start",
                "questions": questions
            })
        except Exception as e:
            logger.error(f"MCQ Generation failed: {e}")
            await manager.broadcast_to_match(match_id, {"type": "error", "message": "Failed to start battle."})
            del manager.active_matches[match_id]
            return
            
    # Main Real-Time Loop
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "answer_submitted":
                is_correct = data.get("is_correct", False)
                # Find which match this user is in
                user_match_id = None
                for m_id, m_data in manager.active_matches.items():
                    if user_id in m_data["players"]:
                        user_match_id = m_id
                        break
                        
                if user_match_id:
                    match = manager.active_matches[user_match_id]
                    if is_correct:
                        match["players"][user_id]["score"] += 1
                        
                    match["players"][user_id]["answer_count"] += 1
                    
                    if match["players"][user_id]["answer_count"] >= 5: # Assuming game ends at 5
                        match["players"][user_id]["completed"] = True

                    # Broadcast opponent_progress explicitly
                    for p_id in match["players"]:
                        if p_id != user_id:
                            opponent_ws = match["players"][p_id]["websocket"]
                            try:
                                await opponent_ws.send_json({
                                    "type": "opponent_progress",
                                    "score": match["players"][user_id]["score"]
                                })
                            except Exception: pass
                                
                    if manager.check_match_complete(user_match_id):
                        await manager.trigger_endgame(user_match_id, db, "NORMAL")
                        break

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected.")
        manager.disconnect(websocket, user_id=user_id)
        
        # Cleanup matches and force abandon if disconnected during combat
        user_match_id = None
        for m_id, m_data in manager.active_matches.items():
            if user_id in m_data["players"]:
                user_match_id = m_id
                break
        
        if user_match_id:
            logger.warning(f"Killing match {user_match_id} due to drop")
            await manager.trigger_endgame(user_match_id, db, "ABANDONED")
