import random
from collections import Counter
from agents.agent import Agent
from db.shared_db import SharedDB


async def run_freechat(agents: dict[int, Agent], alive_ids: list[int],
                       shared_db: SharedDB, game_id: int, round_num: int,
                       broadcast) -> None:
    """P2P neighbor conversations. Players arranged in circle, each talks to neighbors."""
    if len(alive_ids) < 2:
        return

    # Build circular neighbor pairs
    pairs = []
    for i in range(len(alive_ids)):
        j = (i + 1) % len(alive_ids)
        pairs.append((alive_ids[i], alive_ids[j]))

    random.shuffle(pairs)

    all_players = await shared_db.get_players(game_id)
    names = {p['id']: p['name'] for p in all_players}

    for a_id, b_id in pairs:
        agent_a = agents[a_id]
        agent_b = agents[b_id]
        conversation = []

        # 2-3 exchanges (max 5 messages total per pair)
        num_exchanges = random.randint(2, 3)
        msg_count = 0
        for exchange in range(num_exchanges):
            # A speaks
            if msg_count >= 5:
                break
            msg_a = await agent_a.freechat(round_num, names[b_id], conversation)
            msg_a = msg_a[:250]
            conversation.append({"sender": names[a_id], "content": msg_a})
            await shared_db.add_freechat(game_id, round_num, a_id, b_id, msg_a)
            await broadcast({
                "type": "freechat",
                "data": {"round": round_num, "senderId": a_id, "receiverId": b_id,
                         "senderName": names[a_id], "receiverName": names[b_id],
                         "content": msg_a}
            })
            msg_count += 1

            # B responds
            if msg_count >= 5:
                break
            msg_b = await agent_b.freechat(round_num, names[a_id], conversation)
            msg_b = msg_b[:250]
            conversation.append({"sender": names[b_id], "content": msg_b})
            await shared_db.add_freechat(game_id, round_num, b_id, a_id, msg_b)
            await broadcast({
                "type": "freechat",
                "data": {"round": round_num, "senderId": b_id, "receiverId": a_id,
                         "senderName": names[b_id], "receiverName": names[a_id],
                         "content": msg_b}
            })
            msg_count += 1


async def run_pitches(agents: dict[int, Agent], alive_ids: list[int],
                      shared_db: SharedDB, game_id: int, round_num: int,
                      broadcast) -> None:
    """Each alive player gives a public pitch."""
    order = list(alive_ids)
    random.shuffle(order)

    all_players = await shared_db.get_players(game_id)
    names = {p['id']: p['name'] for p in all_players}

    # First, everyone thinks
    for pid in order:
        thought_data = await agents[pid].think(round_num, "pitch", alive_ids)
        await broadcast({
            "type": "thought",
            "data": {"agentId": pid, "agentName": names[pid],
                     "round": round_num, "phase": "pitch", **thought_data}
        })

    # Then pitches
    for pid in order:
        pitch_text = await agents[pid].pitch(round_num)
        await shared_db.add_pitch(game_id, round_num, pid, pitch_text)
        await broadcast({
            "type": "pitch",
            "data": {"round": round_num, "speakerId": pid,
                     "speakerName": names[pid], "content": pitch_text}
        })


async def run_vote(agents: dict[int, Agent], alive_ids: list[int],
                   shared_db: SharedDB, game_id: int, round_num: int,
                   broadcast) -> int | None:
    """Everyone votes. Returns eliminated player ID or None."""
    all_players = await shared_db.get_players(game_id)
    names = {p['id']: p['name'] for p in all_players}
    roles = {p['id']: p['role'] for p in all_players}

    # Think before voting
    for pid in alive_ids:
        thought_data = await agents[pid].think(round_num, "vote", alive_ids)
        await broadcast({
            "type": "thought",
            "data": {"agentId": pid, "agentName": names[pid],
                     "round": round_num, "phase": "vote", **thought_data}
        })

    # Collect votes
    votes = {}
    for pid in alive_ids:
        target = await agents[pid].vote(round_num, alive_ids)
        votes[pid] = target
        await shared_db.add_vote(game_id, round_num, pid, target)
        await broadcast({
            "type": "vote",
            "data": {"round": round_num, "voterId": pid, "voterName": names[pid],
                     "targetId": target, "targetName": names.get(target, "?")}
        })

    # Tally
    vote_counts = Counter(votes.values())
    if not vote_counts:
        return None

    max_votes = max(vote_counts.values())
    top_targets = [pid for pid, count in vote_counts.items() if count == max_votes]

    if len(top_targets) == 1 and max_votes > len(alive_ids) / 2:
        eliminated_id = top_targets[0]
    elif len(top_targets) == 1 and max_votes >= 2:
        # Simple plurality with at least 2 votes
        eliminated_id = top_targets[0]
    else:
        # Tie — no elimination
        eliminated_id = None

    if eliminated_id is not None:
        revealed_role = roles[eliminated_id]
        await shared_db.eliminate_player(game_id, eliminated_id, round_num, "vote")
        await shared_db.add_vote_result(game_id, round_num, eliminated_id, revealed_role)

        # All agents learn the revealed role
        for pid in alive_ids:
            if pid != eliminated_id:
                await agents[pid].agent_db.add_known_fact(
                    game_id, round_num, "death_role_reveal", eliminated_id,
                    f"{names[eliminated_id]} was voted out and revealed as {revealed_role}"
                )

        await broadcast({
            "type": "vote_result",
            "data": {"round": round_num, "eliminatedId": eliminated_id,
                     "eliminatedName": names[eliminated_id],
                     "revealedRole": revealed_role,
                     "votes": {str(k): v for k, v in votes.items()}}
        })
    else:
        await shared_db.add_vote_result(game_id, round_num, None, None)
        await broadcast({
            "type": "vote_result",
            "data": {"round": round_num, "eliminatedId": None,
                     "revealedRole": None,
                     "votes": {str(k): v for k, v in votes.items()}}
        })

    return eliminated_id
