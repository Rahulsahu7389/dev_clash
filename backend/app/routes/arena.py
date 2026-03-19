from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from app.core.security import get_current_user_ws
from app.core.database import get_database
from app.services.arena import manager
from app.services.llm import generate_mcqs
from app.utils.elo import calculate_new_elos
import asyncio
import logging
from bson import ObjectId

router = APIRouter(prefix="/arena", tags=["Arena"])
logger = logging.getLogger(__name__)

@router.websocket("/matchmake")
async def websocket_matchmake(
    websocket: WebSocket,
    user_id: str = Depends(get_current_user_ws)
):
    await websocket.accept()
    db = get_database()
    
    # Fetch user Elo
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    elo = user.get("elo_rating", 1200)
    
    match_id = await manager.find_match(user_id, elo, websocket)
    
    if match_id:
        # Match found! Notify both players
        await manager.broadcast_to_match(match_id, {
            "type": "MATCH_FOUND",
            "match_id": match_id
        })
    else:
        # User is in waiting_queue. Keep connection open.
        try:
            while True:
                # Keep alive/check for disconnection
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.waiting_queue = [p for p in manager.waiting_queue if p["user_id"] != user_id]

@router.websocket("/battle/{match_id}")
async def websocket_battle(
    websocket: WebSocket,
    match_id: str,
    user_id: str = Depends(get_current_user_ws)
):
    await websocket.accept()
    
    if match_id not in manager.active_matches:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    match = manager.active_matches[match_id]
    
    # Ensure user is part of the match
    if user_id not in match["players"]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    # Update current user's websocket in match (it might be different from matchmake)
    match["players"][user_id]["websocket"] = websocket
    
    # Check if both players are connected for battle
    all_connected = True
    for p_id in match["players"]:
        if match["players"][p_id]["websocket"] is None:
            all_connected = False
            break
            
    if all_connected and match["status"] == "waiting":
        match["status"] = "ongoing"
        # Generate questions
        try:
            questions = await generate_mcqs("Random Science Topic")
            match["questions"] = questions
            await manager.broadcast_to_match(match_id, {
                "type": "BATTLE_START",
                "questions": questions
            })
        except Exception as e:
            logger.error(f"Failed to generate MCQs: {e}")
            await manager.broadcast_to_match(match_id, {
                "type": "ERROR",
                "message": "Failed to start battle. MCQ generation error."
            })
            del manager.active_matches[match_id]
            return

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ANSWER_SUBMITTED":
                is_correct = data.get("is_correct", False)
                if is_correct:
                    match["players"][user_id]["score"] += 1
                
                # Broadcast opponent progress
                for p_id in match["players"]:
                    if p_id != user_id:
                        opponent_ws = match["players"][p_id]["websocket"]
                        await opponent_ws.send_json({
                            "type": "OPPONENT_PROGRESS",
                            "opponent_score": match["players"][user_id]["score"]
                        })
                
                match["players"][user_id]["answer_count"] += 1
                
                if match["players"][user_id]["answer_count"] >= 5:
                    match["players"][user_id]["completed"] = True
                    
                # Check if both finished
                if all(p["completed"] for p in match["players"].values()):
                    await handle_endgame(match_id)
                    break
                    
    except WebSocketDisconnect:
        # Handle disconnect during battle
        logger.info(f"User {user_id} disconnected from match {match_id}")
        # In a real game, the other player might win by forfeit.
        if match_id in manager.active_matches:
            # Notify opponent
            for p_id in match["players"]:
                if p_id != user_id:
                    try:
                        await match["players"][p_id]["websocket"].send_json({
                            "type": "OPPONENT_DISCONNECTED",
                            "message": "Your opponent left the arena."
                        })
                    except Exception:
                        pass
            # Cleanup
            if match_id in manager.active_matches:
                del manager.active_matches[match_id]

async def handle_endgame(match_id: str):
    match = manager.active_matches[match_id]
    player_ids = list(match["players"].keys())
    p1_id, p2_id = player_ids[0], player_ids[1]
    
    p1_data = match["players"][p1_id]
    p2_data = match["players"][p2_id]
    
    new_elo_p1, new_elo_p2 = calculate_new_elos(
        p1_data["elo"], p2_data["elo"],
        p1_data["score"], p2_data["score"]
    )
    
    db = get_database()
    
    # Update MongoDB for both players
    for p_id, new_elo, score, opponent_score in [
        (p1_id, new_elo_p1, p1_data["score"], p2_data["score"]),
        (p2_id, new_elo_p2, p2_data["score"], p1_data["score"])
    ]:
        xp_gain = score * 20 + 50 # Basic XP logic
        await db.users.update_one(
            {"_id": ObjectId(p_id)},
            {
                "$set": {"elo_rating": new_elo},
                "$inc": {"total_xp": xp_gain}
            }
        )
        
        # Broadcast results to each player
        try:
            await match["players"][p_id]["websocket"].send_json({
                "type": "MATCH_OVER",
                "your_score": score,
                "opponent_score": opponent_score,
                "new_elo": new_elo,
                "xp_gained": xp_gain
            })
        except Exception:
            pass
            
    # Close sockets and cleanup
    for p_id in match["players"]:
        try:
            await match["players"][p_id]["websocket"].close()
        except Exception:
            pass
            
    if match_id in manager.active_matches:
        del manager.active_matches[match_id]
