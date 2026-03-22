import random
from enum import Enum


class Role(str, Enum):
    IMPOSTOR = "impostor"
    DETECTIVE = "detective"
    DOCTOR = "doctor"
    CIVILIAN = "civilian"


def assign_roles(num_players: int = 5) -> list[str]:
    roles = [Role.IMPOSTOR, Role.DETECTIVE, Role.DOCTOR]
    roles += [Role.CIVILIAN] * (num_players - 3)
    random.shuffle(roles)
    return [r.value for r in roles]
