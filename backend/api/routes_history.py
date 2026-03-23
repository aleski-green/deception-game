from fastapi import APIRouter, HTTPException
from api.routes_game import get_engine

router = APIRouter(prefix="/api/history")


@router.get("/public")
async def get_public_history():
    eng = get_engine()
    if not eng.shared_db or not eng.game_id:
        return {"freechats": [], "pitches": [], "votes": [], "voteResults": [], "nightResults": []}

    return {
        "freechats": await eng.shared_db.get_all_freechats(eng.game_id),
        "pitches": await eng.shared_db.get_all_pitches(eng.game_id),
        "votes": await eng.shared_db.get_all_votes(eng.game_id),
        "voteResults": await eng.shared_db.get_vote_results(eng.game_id),
        "nightResults": await eng.shared_db.get_night_results(eng.game_id),
    }


@router.get("/agent/{agent_id}")
async def get_agent_history(agent_id: int):
    eng = get_engine()
    if agent_id < 0 or agent_id > 4:
        raise HTTPException(400, "Agent ID must be 0-4")
    data = await eng.get_agent_history(agent_id)
    # data now includes: thoughts, suspicions, known_facts, diary, round_summaries, positions
    return data


@router.get("/freechat/{round_num}")
async def get_freechat(round_num: int):
    eng = get_engine()
    if not eng.shared_db or not eng.game_id:
        return []
    return await eng.shared_db.get_freechats(eng.game_id, round_num)


@router.get("/votes/{round_num}")
async def get_votes(round_num: int):
    eng = get_engine()
    if not eng.shared_db or not eng.game_id:
        return []
    return await eng.shared_db.get_votes(eng.game_id, round_num)
