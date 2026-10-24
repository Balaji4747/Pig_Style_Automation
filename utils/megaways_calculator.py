"""Pig Style reference win calculator (test oracle).

Derived from real spin responses. Rules marked ASSUMPTION are not yet
confirmed by the math file and must be checked before certification use.

Confirmed from samples:
- Position index = row * 6 + reel_index (0-based, top row = 0).
- One winLine entry per individual way (not aggregated per symbol).
- Win per way = paytable[symbol][count - 1] * betAmountUsed * multiplier.
- betAmountUsed = bet / 20 (0.05 at bet 1).
- WC substitutes for paying symbols (seen on reel 2, 0-based reel 1).
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from itertools import product

WILD = "WC"
NON_PAYING = {"WC", "BN"}
REELS = 6
TWO_DP = Decimal("0.01")


@dataclass(frozen=True)
class Way:
    symbol: str
    count: int
    positions: tuple
    wild_count: int
    win: Decimal


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(TWO_DP, rounding=ROUND_HALF_UP)


def position(reel: int, row: int) -> int:
    return row * REELS + reel


def evaluate(reel_view, paytable, bet_amount_used, multiplier=1):
    """Return every winning way for one reel window, matching the server's winLines format."""
    coin = Decimal(str(bet_amount_used))
    ways = []
    for symbol, pays in paytable.items():
        if symbol in NON_PAYING:
            continue
        # Matching rows per reel, left to right, stop at first reel with no match.
        matches = []
        for reel_index, reel in enumerate(reel_view):
            rows = [r for r, s in enumerate(reel) if s == symbol or s == WILD]
            if not rows:
                break
            matches.append([(reel_index, r) for r in rows])
        count = len(matches)
        if count < 3 or pays[count - 1] == 0:
            continue
        for combo in product(*matches):
            symbols_in_way = [reel_view[reel][row] for reel, row in combo]
            # ASSUMPTION: an all-wild way is not paid as every symbol.
            if all(s == WILD for s in symbols_in_way):
                continue
            # ASSUMPTION: rounding is applied per way, then summed.
            win = money(Decimal(pays[count - 1]) * coin * Decimal(multiplier))
            ways.append(Way(
                symbol=symbol,
                count=count,
                positions=tuple(position(reel, row) for reel, row in combo),
                wild_count=symbols_in_way.count(WILD),
                win=win,
            ))
    return ways


def total_win(ways) -> Decimal:
    return money(sum((w.win for w in ways), Decimal("0")))


def ways_count(reel_view) -> int:
    """Total ways on screen: product of symbols per reel (max 7^6 = 117,649)."""
    total = 1
    for reel in reel_view:
        total *= len(reel)
    return total