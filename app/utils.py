from ossapi.enums import Grade

def rank_to_str(rank: Grade) -> str:
    if rank == Grade.SSH:
        return "XH"
    elif rank == Grade.SS:
        return "X"
    elif rank == Grade.SH:
        return "SH"
    elif rank == Grade.S:
        return "S"
    elif rank == Grade.A:
        return "A"
    elif rank == Grade.B:
        return "B"
    elif rank == Grade.C:
        return "C"
    elif rank == Grade.D:
        return "D"
