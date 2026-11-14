# infinity_chess/geometry.py
from __future__ import annotations
from functools import lru_cache
from typing import NamedTuple
from infinity_chess.move import Square

KNIGHT_OFFSETS = ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1))
KING_OFFSETS   = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
ROOK_DIRS      = ((1,0),(-1,0),(0,1),(0,-1))
BISHOP_DIRS    = ((1,1),(1,-1),(-1,1),(-1,-1))


@lru_cache(maxsize=None)
def square_table(ranks: int, files: int) -> tuple[Square, ...]:
    """One shared, immutable Square per index, so index -> Square never allocates."""
    return tuple(Square(i // files, i % files) for i in range(ranks * files))


class Geometry(NamedTuple):
    knight: tuple        # idx -> target indices
    king: tuple
    pawn_from: tuple     # [0=white, 1=black][idx] -> squares a pawn would attack idx from
    rook_rays: tuple     # idx -> rays; each ray = indices, nearest first
    bishop_rays: tuple


def _step(ranks, files, wrap, idx, dr, df) -> int:
    r, f = divmod(idx, files)
    r += dr
    f += df
    if not 0 <= r < ranks:
        return -1
    if wrap:
        f %= files
    elif not 0 <= f < files:
        return -1
    return r * files + f


@lru_cache(maxsize=None)
def geometry(ranks: int, files: int, wrap: bool) -> Geometry:
    n = ranks * files

    def leaper(offsets):
        table = []
        for idx in range(n):
            out = []
            for dr, df in offsets:
                t = _step(ranks, files, wrap, idx, dr, df)
                if t != -1 and t not in out:
                    out.append(t)
            table.append(tuple(out))
        return tuple(table)

    def rays(dirs):
        table = []
        for idx in range(n):
            per_dir = []
            for dr, df in dirs:
                ray, t = [], _step(ranks, files, wrap, idx, dr, df)
                while t != -1 and t != idx:        # t == idx: wrapped fully round
                    ray.append(t)
                    t = _step(ranks, files, wrap, t, dr, df)
                per_dir.append(tuple(ray))
            table.append(tuple(per_dir))
        return tuple(table)

    def pawn_from(direction):
        table = []
        for idx in range(n):
            srcs = [_step(ranks, files, wrap, idx, -direction, df) for df in (-1, 1)]
            table.append(tuple(t for t in srcs if t != -1))
        return tuple(table)

    return Geometry(leaper(KNIGHT_OFFSETS), leaper(KING_OFFSETS),
                    (pawn_from(1), pawn_from(-1)), rays(ROOK_DIRS), rays(BISHOP_DIRS))