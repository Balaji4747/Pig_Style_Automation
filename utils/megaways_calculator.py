"""Pig Style reference win calculator (test oracle).

Derived from real spin responses. Rules marked ASSUMPTION are not yet
confirmed by the math file and must be checked before certification use.

Confirmed from samples:
- Position index = row * 6 + reel_index (0-based, top row = 0).
- One winLine entry per individual way (not aggregated per symbol).
- Win per way = paytable[symbol][count - 1] * betAmountUsed * multiplier.
- betAmountUsed = bet / 20 (0.05 at bet 1).
- WC substitutes for paying symbols (seen on reel 2, 0-based reel 1).
- A winning way containing a wild is scaled by the round's active wild
  multiplier (DECISIONS.md D-025/D-035): confirmed live against a real
  captured sample where wild_multipliers=[[1, 4, 2]] and a wild_count=1 way
  paid exactly double its base paytable amount — the LAST element of each
  entry is the real multiplier VALUE (not an index). A value of 0 is
  treated as "no multiplier" (1x), since 0 is never a valid wild-multiplier
  value per the math file's confirmed x1/x2/x3 range.
- Neither per-way amounts nor the aggregate total_win are rounded
  server-side (confirmed live 27 Oct 2026: a single 0.075 way produces a
  total_win of exactly 0.075, not 0.08) — superseded the project's earlier
  documented assumption that opCnf.moneyRounding (half-up, 2dp) applied to
  these values; it does not. evaluate()/total_win() return full, unrounded
  precision accordingly.
"""
from dataclasses import dataclass
from decimal import Decimal
from itertools import product

WILD = "WC"
NON_PAYING = {"WC", "BN"}
REELS = 6


@dataclass(frozen=True)
class Way:
    symbol: str
    count: int
    positions: tuple
    wild_count: int
    win: Decimal


def position(reel: int, row: int) -> int:
    return row * REELS + reel


def active_wild_multiplier(wild_multipliers) -> int:
    """Combine the server's raw `wildMultipliers` entries into a single
    per-spin multiplier to apply to any winning way containing a wild.

    Confirmed from a real captured sample (D-025): `wild_multipliers=[[1, 4,
    2]]` and a wild_count=1 way paid exactly double its base amount — the
    last element of each entry is the real multiplier value, not an index.
    A 0 is treated as 1 (no multiplier), since 0 never appears as a real
    wild-multiplier value per the math file's confirmed x1/x2/x3 range.

    ASSUMPTION, not yet empirically validated: when more than one entry is
    present (more than one wild landed this spin), this multiplies their
    values together. No sample with 2+ wilds contributing to the same
    winning way has been captured yet to confirm this combination rule —
    revisit if one surfaces."""
    if not wild_multipliers:
        return 1
    total = 1
    for entry in wild_multipliers:
        value = entry[-1] if entry else 0
        total *= value if value and value >= 1 else 1
    return total


def evaluate(reel_view, paytable, bet_amount_used, multiplier=1, wild_multipliers=None):
    """Return every winning way for one reel window, matching the server's
    winLines format. `wild_multipliers` is the raw `result.wild_multipliers`
    list — pass it so a way containing a wild is scaled correctly (D-025)."""
    coin = Decimal(str(bet_amount_used))
    wild_mult = active_wild_multiplier(wild_multipliers)
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
            wild_count = symbols_in_way.count(WILD)
            way_multiplier = Decimal(multiplier) * (Decimal(wild_mult) if wild_count else Decimal(1))
            # Confirmed live (27 Oct 2026): each way's win amount is NOT
            # rounded server-side - e.g. a 0.075 way is reported as exactly
            # 0.075, not 0.08. Previously an unconfirmed assumption; fixed
            # with explicit user sign-off per this module's standing "never
            # modify without discussion" rule, alongside the matching fix in
            # total_win().
            win = Decimal(pays[count - 1]) * coin * way_multiplier
            ways.append(Way(
                symbol=symbol,
                count=count,
                positions=tuple(position(reel, row) for reel, row in combo),
                wild_count=wild_count,
                win=win,
            ))
    return ways


def total_win(ways) -> Decimal:
    """Sum of all ways' win amounts, at full unrounded precision. Confirmed
    live (27 Oct 2026): the server's own total_win field is the exact
    unrounded sum of per-way amounts (e.g. a single 0.075 way produces a
    total_win of exactly 0.075, not 0.08) - it is NOT rounded to 2 decimals,
    contrary to this project's earlier documented assumption that
    opCnf.moneyRounding (half-up) applied here. Fixed with explicit user
    sign-off per the standing "never modify without discussion" rule for
    this module."""
    return sum((w.win for w in ways), Decimal("0"))


def ways_count(reel_view) -> int:
    """Total ways on screen: product of symbols per reel (max 7^6 = 117,649)."""
    total = 1
    for reel in reel_view:
        total *= len(reel)
    return total