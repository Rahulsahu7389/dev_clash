from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.core.security import get_current_user_ws
from app.core.database import get_database
from app.services.arena import manager
from app.services.llm import generate_mcqs, generate_mcqs_from_context, generate_vault_mcqs, generate_adaptive_pyqs
import asyncio
import uuid
import logging
import random
from bson import ObjectId
from datetime import datetime, timezone
from app.utils.srs import calculate_next_review

router = APIRouter(prefix="/ws", tags=["Arena"])
logger = logging.getLogger(__name__)

async def simulate_bot_game(match_id: str, real_player_ws: WebSocket, bot_id: str):
    bot_iq = random.uniform(0.40, 0.85)
    for _ in range(5):
        await asyncio.sleep(random.randint(4, 11))
        
        if match_id not in manager.active_matches:
            break
            
        match = manager.active_matches[match_id]
        if match.get("status") == "finished":
            break
            
        if random.random() <= bot_iq:
            match["players"][bot_id]["score"] += 1
            
        match["players"][bot_id]["answer_count"] += 1
        
        if match["players"][bot_id]["answer_count"] >= 5:
            match["players"][bot_id]["completed"] = True
            
        try:
            await real_player_ws.send_json({
                "type": "OPPONENT_PROGRESS",
                "opponent_score": match["players"][bot_id]["score"]
            })
        except Exception:
            pass
            
        # If bot reaches 5 questions, check if real player is already done
        if match["players"][bot_id]["completed"] and manager.check_match_complete(match_id):
            db = get_database()
            await manager.trigger_endgame(match_id, db)
            break

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
    exam_track = user.get("exam_track", "JEE")
    
    # Try to intercept VAULT_BOT_MATCH payload immediately
    initial_data = None
    try:
        initial_data = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
    except asyncio.TimeoutError:
        pass

    if initial_data and initial_data.get("type", "").upper() == "TOPIC_BOT_MATCH":
        target_topic = initial_data.get("topic", "General Science")
        match_id = f"TOPIC_MATCH_{uuid.uuid4().hex[:8]}"
        bot_id = "SRS_BOT"
        
        manager.active_matches[match_id] = {
            "players": {
                user_id: {"websocket": websocket, "score": 0, "answer_count": 0, "completed": False, "elo": elo},
                bot_id: {"websocket": None, "score": 0, "answer_count": 0, "completed": False, "elo": elo}
            },
            "status": "ongoing",
            "exam_track": exam_track,
            "target_topic": target_topic,   # <--- ADD THIS
            "is_srs_match": True            # <--- ADD THIS
        }
        
        await websocket.send_json({
            "type": "MATCH_FOUND",
            "opponent": bot_id
        })
        
        # Generate questions directly from the topic string!
        questions = await generate_mcqs(target_topic, exam_track)
        manager.active_matches[match_id]["questions"] = questions
        
        await websocket.send_json({
            "type": "BATTLE_START",
            "questions": questions
        })
        asyncio.create_task(simulate_bot_game(match_id, websocket, bot_id))
        is_starter = False
    elif initial_data and initial_data.get("type", "").upper() == "ADAPTIVE_BOT_MATCH":
        target_topic = initial_data.get("topic", "General")
        
        # Fetch past mistakes for context
        mistakes_cursor = db.mistake_logs.find({
            "user_id": {"$in": [user_id, ObjectId(user_id)]}, 
            "target_topics": target_topic
        }).sort("created_at", -1).limit(3)
        mistakes = await mistakes_cursor.to_list(length=3)
        mistake_texts = [m.get("question", "") for m in mistakes]

        match_id = f"ADAPTIVE_{uuid.uuid4().hex[:8]}"
        bot_id = "PYQ_MASTER_BOT"

        manager.active_matches[match_id] = {
            "players": {
                user_id: {"websocket": websocket, "score": 0, "answer_count": 0, "completed": False, "elo": elo},
                bot_id: {"websocket": None, "score": 0, "answer_count": 0, "completed": False, "elo": elo}
            },
            "status": "ongoing",
            "exam_track": exam_track,
            "target_topic": target_topic,
            "is_srs_match": True
        }
        
        await websocket.send_json({
            "type": "MATCH_FOUND",
            "opponent": bot_id
        })
        
        questions = await generate_adaptive_pyqs(target_topic, mistake_texts, exam_track)
        manager.active_matches[match_id]["questions"] = questions
        
        await websocket.send_json({
            "type": "BATTLE_START",
            "questions": questions
        })
        asyncio.create_task(simulate_bot_game(match_id, websocket, bot_id))
        is_starter = False
    elif initial_data and initial_data.get("type", "").upper() == "VAULT_BOT_MATCH":
        active_doc_ids = initial_data.get("active_doc_ids", [])
        match_id = f"VAULT_MATCH_{uuid.uuid4().hex[:8]}"
        bot_id = "VAULT_BOT"
        
        manager.active_matches[match_id] = {
            "players": {
                user_id: {"websocket": websocket, "score": 0, "answer_count": 0, "completed": False, "elo": elo},
                bot_id: {"websocket": None, "score": 0, "answer_count": 0, "completed": False, "elo": elo}
            },
            "status": "ongoing",
            "exam_track": exam_track,
            "vault_doc_ids": active_doc_ids
        }
        
        await websocket.send_json({
            "type": "MATCH_FOUND",
            "opponent": bot_id
        })
        
        questions = await generate_vault_mcqs(active_doc_ids, exam_track)
        manager.active_matches[match_id]["questions"] = questions
        
        await websocket.send_json({
            "type": "BATTLE_START",
            "questions": questions
        })
        asyncio.create_task(simulate_bot_game(match_id, websocket, bot_id))
        is_starter = False
    else:
        # Standard Queue Logic
        match_id = await manager.find_match(user_id, elo, exam_track, websocket)
        is_starter = False
        
        if not match_id:
            # Wait up to 10 seconds for opponent
            for _ in range(10):
                await asyncio.sleep(1)
                for m_id, m_data in manager.active_matches.items():
                    if user_id in m_data["players"]:
                        match_id = m_id
                        break
                if match_id:
                    break
                
        if not match_id:
            # Ghost Bot Setup
            manager.remove_from_queue(user_id)
            match_id = manager.create_bot_match(user_id, elo, exam_track, websocket)
            bot_id = f"PRITHVI_BOT_{exam_track}_{elo}"
            
            await websocket.send_json({
                "type": "MATCH_FOUND",
                "opponent": bot_id
            })
            
            match = manager.active_matches[match_id]
            match["status"] = "ongoing"
            try:
                SYLLABUS = {
                    "JEE": {
                        "Physics": ["Kinematics", "Thermodynamics", "Electromagnetism"],
                        "Chemistry": ["Chemical Bonding", "Organic Chemistry", "Equilibrium"],
                        "Math": ["Calculus", "Algebra", "Coordinate Geometry"]
                    },
                    "NEET": {
                        "Physics": ["Mechanics", "Optics", "Modern Physics"],
                        "Chemistry": ["Physical Chemistry", "Inorganic Chemistry", "Organic Chemistry"],
                        "Biology": ["Human Physiology", "Genetics", "Plant Diversity"]
                    },
                    "UPSC": {
                        "History": ["Modern Indian History", "Ancient India"],
                        "Geography": ["Physical Geography", "Indian Geography"],
                        "Polity": ["Constitution", "Governance"]
                    },
                    "GATE": {
                        "Core": ["Data Structures", "Algorithms", "Operating Systems"],
                        "Math": ["Engineering Mathematics", "Discrete Math"],
                        "Aptitude": ["Quantitative Aptitude", "Logical Reasoning"]
                    }
                }
                track = match.get("exam_track", "JEE")
                track_subjects = SYLLABUS.get(track, SYLLABUS["JEE"])
                
                selected_topics = []
                for subject, topics in track_subjects.items():
                    selected_topics.append(f"{subject}: {random.choice(topics)}")
                    
                mixed_topic_string = " and ".join(selected_topics)
                questions = await generate_mcqs(mixed_topic_string, track)
                match["questions"] = questions
                await websocket.send_json({
                    "type": "BATTLE_START",
                    "questions": questions
                })
            except Exception as e:
                logger.error(f"MCQ Generation failed: {e}")
                await manager.broadcast_to_match(match_id, {
                    "type": "MATCH_OVER", 
                    "reason": "error", 
                    "message": "The AI referee encountered an error generating questions. Please queue again."
                })
                manager.active_matches.pop(match_id, None)
                try:
                    await websocket.close()
                except Exception:
                    pass
                return
                
            asyncio.create_task(simulate_bot_game(match_id, websocket, bot_id))
        else:
            is_starter = True
        
    if match_id and is_starter:
        match = manager.active_matches[match_id]
        players_list = list(match["players"].keys())
        p1 = players_list[0]
        p2 = players_list[1]
        
        try:
            await match["players"][p1]["websocket"].send_json({
                "type": "MATCH_FOUND",
                "opponent": f"Player {p2[-4:]}"
            })
            ws_p2 = match["players"][p2]["websocket"]
            if ws_p2:
                await ws_p2.send_json({
                    "type": "MATCH_FOUND",
                    "opponent": f"Player {p1[-4:]}"
                })
        except Exception:
            pass
            
        match["status"] = "ongoing"
        try:
            SYLLABUS = {
                "JEE": {
                    "Physics": ["Kinematics", "Thermodynamics", "Electromagnetism"],
                    "Chemistry": ["Chemical Bonding", "Organic Chemistry", "Equilibrium"],
                    "Math": ["Calculus", "Algebra", "Coordinate Geometry"]
                },
                "NEET": {
                    "Physics": ["Mechanics", "Optics", "Modern Physics"],
                    "Chemistry": ["Physical Chemistry", "Inorganic Chemistry", "Organic Chemistry"],
                    "Biology": ["Human Physiology", "Genetics", "Plant Diversity"]
                },
                "UPSC": {
                    "History": ["Modern Indian History", "Ancient India"],
                    "Geography": ["Physical Geography", "Indian Geography"],
                    "Polity": ["Constitution", "Governance"]
                },
                "GATE": {
                    "Core": ["Data Structures", "Algorithms", "Operating Systems"],
                    "Math": ["Engineering Mathematics", "Discrete Math"],
                    "Aptitude": ["Quantitative Aptitude", "Logical Reasoning"]
                }
            }
            track = match.get("exam_track", "JEE")
            track_subjects = SYLLABUS.get(track, SYLLABUS["JEE"])
            
            selected_topics = []
            for subject, topics in track_subjects.items():
                selected_topics.append(f"{subject}: {random.choice(topics)}")
                
            mixed_topic_string = " and ".join(selected_topics)
            questions = await generate_mcqs(mixed_topic_string, track)
            match["questions"] = questions
            await manager.broadcast_to_match(match_id, {
                "type": "BATTLE_START",
                "questions": questions
            })
        except Exception as e:
            logger.error(f"MCQ Generation failed: {e}")
            await manager.broadcast_to_match(match_id, {
                "type": "MATCH_OVER", 
                "reason": "error", 
                "message": "The AI referee encountered an error generating questions. Please queue again."
            })
            manager.active_matches.pop(match_id, None)
            try:
                if ws_p1: await ws_p1.close()
            except Exception: pass
            try:
                if ws_p2: await ws_p2.close()
            except Exception: pass
            return
            
    # Main Real-Time Loop
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "").upper()
            
            if msg_type == "ANSWER_SUBMITTED":
                is_correct = data.get("is_correct", False)
                time_taken = data.get("time_taken", 0)
                current_q_idx = data.get("question_idx", 0)
                user_match_id = None
                for m_id, m_data in manager.active_matches.items():
                    if user_id in m_data["players"]:
                        user_match_id = m_id
                        break
                        
                if user_match_id:
                    match = manager.active_matches[user_match_id]
                    if is_correct:
                        match["players"][user_id]["score"] += 1
                        
                    # --- ATOMIC INJECTION: WEAKNESS DETECTION ---
                    # If they got it wrong OR took more than 20 seconds, log it as a weakness
                    if not is_correct or time_taken > 20:
                        qs = match.get("questions", [])
                        current_q = qs[current_q_idx] if qs and current_q_idx < len(qs) else {}
                        q_text = current_q.get("question", "Unknown Question")
                        target_topic = match.get("target_topic", "General")
                        
                        asyncio.create_task(db.mistake_logs.insert_one({
                            "user_id": user_id,
                            "match_id": user_match_id,
                            "target_topics": [target_topic],
                            "question": q_text,
                            "time_taken": time_taken,
                            "is_correct": is_correct,
                            "is_resolved": False,
                            "created_at": datetime.now(timezone.utc)
                        }))
                    # --- END INJECTION ---

                    match["players"][user_id]["answer_count"] += 1
                    
                    if match["players"][user_id]["answer_count"] >= 5:
                        match["players"][user_id]["completed"] = True

                    # --- ATOMIC INJECTION: SRS CURVE UPDATE ---
                    if match.get("is_srs_match") and match.get("target_topic"):
                        topic = match["target_topic"]
                        score = match["players"][user_id]["score"]
                        quality = int((score / 5.0) * 5) # Convert 0-5 score to SM-2 quality factor
                        
                        # Fetch existing SRS record
                        srs_record = await db.srs_records.find_one({"user_id": user_id, "reference_id": topic})
                        cf = srs_record["ease_factor"] if srs_record else 2.5
                        interval = srs_record["interval"] if srs_record else 0
                        
                        # Calculate new curve
                        srs_result = calculate_next_review(quality, cf, interval)
                        
                        await db.srs_records.update_one(
                            {"user_id": user_id, "reference_id": topic},
                            {
                                "$set": {
                                    "ease_factor": srs_result["ease_factor"],
                                    "interval": srs_result["interval"],
                                    "next_review_date": srs_result["next_review_date"],
                                    "last_reviewed_date": datetime.now(timezone.utc),
                                    "record_type": "topic"
                                },
                                "$inc": {"repetition_count": 1}
                            },
                            upsert=True
                        )
                    # --- END INJECTION ---

                    for p_id in match["players"]:
                        if p_id != user_id and match["players"][p_id]["websocket"]:
                            opponent_ws = match["players"][p_id]["websocket"]
                            try:
                                await opponent_ws.send_json({
                                    "type": "OPPONENT_PROGRESS",
                                    "opponent_score": match["players"][user_id]["score"]
                                })
                            except Exception: pass
                                
                    if manager.check_match_complete(user_match_id):
                        await manager.trigger_endgame(user_match_id, db)
                        break
                    elif match["players"][user_id]["completed"]:
                        try:
                            await websocket.send_json({
                                "type": "WAITING_FOR_OPPONENT",
                                "your_score": match["players"][user_id]["score"],
                                "message": "Waiting for opponent to finish..."
                            })
                        except Exception: pass

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected.")
        manager.disconnect(websocket, user_id=user_id)
        
        user_match_id = None
        for m_id, m_data in manager.active_matches.items():
            if user_id in m_data["players"]:
                user_match_id = m_id
                break
        
        if user_match_id:
            logger.warning(f"Rage quit detected in {user_match_id}")
            await manager.handle_disconnect(user_match_id, user_id, db)
