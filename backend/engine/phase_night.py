from agents.agent import Agent
from db.shared_db import SharedDB


async def run_night(agents: dict[int, Agent], alive_ids: list[int],
                    shared_db: SharedDB, game_id: int, round_num: int,
                    broadcast) -> int | None:
    """
    Night phase: impostor kills, doctor heals, detective investigates.
    Returns killed player ID or None if saved.
    """
    all_players = await shared_db.get_players(game_id)
    names = {p['id']: p['name'] for p in all_players}
    roles = {p['id']: p['role'] for p in all_players}

    impostor = None
    detective = None
    doctor = None

    for pid in alive_ids:
        role = roles[pid]
        if role == "impostor":
            impostor = agents[pid]
        elif role == "detective":
            detective = agents[pid]
        elif role == "doctor":
            doctor = agents[pid]

    kill_target = None
    heal_target = None
    investigate_target = None

    # Impostor chooses kill
    if impostor:
        # Think first
        thought_data = await impostor.think(round_num, "night", alive_ids)
        await broadcast({
            "type": "thought",
            "data": {"agentId": impostor.id, "agentName": names[impostor.id],
                     "round": round_num, "phase": "night_kill", **thought_data}
        })
        kill_target = await impostor.night_kill(round_num, alive_ids)
        await broadcast({
            "type": "night_action",
            "data": {"round": round_num, "action": "kill",
                     "agentId": impostor.id, "agentName": names[impostor.id],
                     "targetId": kill_target, "targetName": names.get(kill_target, "?")}
        })

    # Doctor chooses heal
    if doctor:
        thought_data = await doctor.think(round_num, "night", alive_ids)
        await broadcast({
            "type": "thought",
            "data": {"agentId": doctor.id, "agentName": names[doctor.id],
                     "round": round_num, "phase": "night_heal", **thought_data}
        })
        heal_target = await doctor.night_heal(round_num, alive_ids)
        await broadcast({
            "type": "night_action",
            "data": {"round": round_num, "action": "heal",
                     "agentId": doctor.id, "agentName": names[doctor.id],
                     "targetId": heal_target, "targetName": names.get(heal_target, "?")}
        })

    # Detective investigates
    if detective:
        thought_data = await detective.think(round_num, "night", alive_ids)
        await broadcast({
            "type": "thought",
            "data": {"agentId": detective.id, "agentName": names[detective.id],
                     "round": round_num, "phase": "night_investigate", **thought_data}
        })
        investigate_target = await detective.night_investigate(round_num, alive_ids)

        # Detective learns if target is impostor
        is_impostor = roles.get(investigate_target) == "impostor"
        result_text = f"{names.get(investigate_target, '?')} is {'the IMPOSTOR!' if is_impostor else 'NOT the impostor.'}"
        await detective.agent_db.add_known_fact(
            game_id, round_num, "investigation_result", investigate_target, result_text
        )
        await broadcast({
            "type": "night_action",
            "data": {"round": round_num, "action": "investigate",
                     "agentId": detective.id, "agentName": names[detective.id],
                     "targetId": investigate_target,
                     "targetName": names.get(investigate_target, "?"),
                     "result": result_text}
        })

    # Resolve night
    saved = False
    killed_id = None

    if kill_target is not None:
        if heal_target == kill_target:
            saved = True
            killed_id = None
        else:
            killed_id = kill_target
            await shared_db.eliminate_player(game_id, killed_id, round_num, "night_kill")
            # Night kills don't reveal roles (only vote eliminations do)

    await shared_db.add_night_result(game_id, round_num, killed_id, saved)

    await broadcast({
        "type": "night_result",
        "data": {
            "round": round_num,
            "killedId": killed_id,
            "killedName": names.get(killed_id, None) if killed_id else None,
            "saved": saved,
        }
    })

    # All agents learn about the night result in the morning
    if killed_id is not None:
        for pid in alive_ids:
            if pid != killed_id:
                await agents[pid].agent_db.add_known_fact(
                    game_id, round_num, "night_death", killed_id,
                    f"{names[killed_id]} was killed during the night"
                )
    elif saved:
        for pid in alive_ids:
            await agents[pid].agent_db.add_known_fact(
                game_id, round_num, "night_save", None,
                "Someone was attacked but the doctor saved them"
            )

    return killed_id
