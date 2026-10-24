"""Typed parsing of the game's init/spin API responses.

Money values are parsed as Decimal (via the JSON value's str() form, never
via float) to avoid binary floating-point rounding errors on balances, bets
and wins. Shapes confirmed live against the qa game session (23 Oct 2026):
  init: POST /gs/pack-alpha/games/init
  spin: POST /gs/pack-alpha/games/spin

The /gs/pack-alpha/games/feature endpoint (Free Spins round spins) is not
parsed here yet — its response shape hasn't been captured/confirmed.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from utils.megaways_calculator import ways_count


def _dec(value) -> Decimal:
    return Decimal(str(value))


@dataclass(frozen=True)
class MoneyRounding:
    decimals: int
    mode: str


@dataclass(frozen=True)
class OpCnf:
    spin_duration_ms: int
    show_gamble_warning: bool
    show_elapsed_time: bool
    show_net_loss: bool
    show_max_bet: bool
    show_max_win: bool
    show_hourly_loss: bool
    responsible_gaming: bool
    is_auto_available: bool
    is_turbo_available: bool
    is_bb_available: bool
    allow_full_ante_bet: bool
    auto_spin_spending_limit: bool
    show_disclosure_text: bool
    show_rtp: bool
    money_rounding: MoneyRounding


@dataclass(frozen=True)
class PlayerInfo:
    player_id: str
    currency_code: str
    max_payout: Decimal
    balance: Decimal
    language: str
    max_bet: Decimal
    bb_max_bet: Decimal
    min_bet: Decimal
    default_bet: Decimal
    bb_max_win: Decimal
    allow_cheat: bool
    possible_bets: list[Decimal]
    buy_feature: bool
    home_url: Optional[str]
    deposit_url: Optional[str]
    bb_bet_multiplier_settings: dict[str, int]


@dataclass(frozen=True)
class GameInfo:
    game_id: str
    dev_mode: bool
    pay_table: dict[str, list[Decimal]]


@dataclass(frozen=True)
class InitResponse:
    unfinished_info: Optional[dict]
    game_info: GameInfo
    player_info: PlayerInfo
    bet_type: Optional[str]
    preferences: dict
    op_cnf: OpCnf
    rtp_base: Decimal
    epoch: int
    jackpot_info: Optional[dict]


@dataclass(frozen=True)
class WinLine:
    symbol: str
    win_amount: Decimal
    multiplier: int
    consecutive_count: int
    winning_position: tuple
    wild_count: int


@dataclass(frozen=True)
class SpinResult:
    game_id: str
    round_id: str
    closed: bool
    balance: Decimal
    bet: Decimal
    bet_amount_used: Decimal
    total_win: Decimal
    reel_view: list
    win_lines: tuple
    reel_modifiers: list
    next_feature: Optional[str]
    next_feature_sub_type: Optional[str]
    wild_multipliers: list
    spin_win: Decimal
    max_cap_reached: bool
    max_win: Decimal
    feature_trigger_positions: list
    scatter_count: int
    is_feature_triggered: bool

    @property
    def ways(self) -> int:
        """Megaways count: product of each reel's visible symbol count.
        Confirmed against the live MEGAWAYS counter (e.g. reel lengths
        3,7,3,6,3,2 -> 2268; all reels at 7 -> 117649)."""
        return ways_count(self.reel_view)


def parse_init_response(raw: dict) -> InitResponse:
    data = raw["data"]
    game_info = data["gameInfo"]
    player_info = data["playerInfo"]
    op_cnf = data["opCnf"]
    money_rounding = op_cnf["moneyRounding"]

    return InitResponse(
        unfinished_info=data.get("unfinishedInfo"),
        game_info=GameInfo(
            game_id=game_info["gameId"],
            dev_mode=game_info["devMode"],
            pay_table={symbol: [_dec(v) for v in pays] for symbol, pays in game_info["payTable"].items()},
        ),
        player_info=PlayerInfo(
            player_id=player_info["playerId"],
            currency_code=player_info["currencyCode"],
            max_payout=_dec(player_info["maxPayout"]),
            balance=_dec(player_info["balance"]),
            language=player_info["language"],
            max_bet=_dec(player_info["maxBet"]),
            bb_max_bet=_dec(player_info["bbMaxBet"]),
            min_bet=_dec(player_info["minBet"]),
            default_bet=_dec(player_info["defaultBet"]),
            bb_max_win=_dec(player_info["bbMaxWin"]),
            allow_cheat=player_info["allowCheat"],
            possible_bets=[_dec(b) for b in player_info["possibleBets"]],
            buy_feature=player_info["buyFeature"],
            home_url=player_info.get("homeURL"),
            deposit_url=player_info.get("depositUrl"),
            bb_bet_multiplier_settings=player_info.get("bbBetMultiplierSettings", {}),
        ),
        bet_type=data.get("betType"),
        preferences=data.get("preferences", {}),
        op_cnf=OpCnf(
            spin_duration_ms=op_cnf["spinDuration"],
            show_gamble_warning=op_cnf["showGambleWarning"],
            show_elapsed_time=op_cnf["showElapsedTime"],
            show_net_loss=op_cnf["showNetLoss"],
            show_max_bet=op_cnf["showMaxBet"],
            show_max_win=op_cnf["showMaxWin"],
            show_hourly_loss=op_cnf["showHourlyLoss"],
            responsible_gaming=op_cnf["responsibleGaming"],
            is_auto_available=op_cnf["isAutoAvailable"],
            is_turbo_available=op_cnf["isTurboAvailable"],
            is_bb_available=op_cnf["isBBAvailable"],
            allow_full_ante_bet=op_cnf["allowFullAnteBet"],
            auto_spin_spending_limit=op_cnf["autoSpinSpendingLimit"],
            show_disclosure_text=op_cnf["showDisclosureText"],
            show_rtp=op_cnf["showRTP"],
            money_rounding=MoneyRounding(decimals=money_rounding["decimals"], mode=money_rounding["mode"]),
        ),
        rtp_base=_dec(data["rtp"]["base"]),
        epoch=data["epoch"],
        jackpot_info=data.get("jackpotInfo"),
    )


def parse_spin_response(raw: dict) -> SpinResult:
    data = raw["data"]
    result = data["result"]

    return SpinResult(
        game_id=data["gameId"],
        round_id=data["roundId"],
        closed=data["closed"],
        balance=_dec(data["playerInfo"]["balance"]),
        bet=_dec(result["bet"]),
        bet_amount_used=_dec(result["betAmountUsed"]),
        total_win=_dec(result["totalWin"]),
        reel_view=result["reelView"],
        win_lines=tuple(
            WinLine(
                symbol=win_line["symbol"],
                win_amount=_dec(win_line["winAmount"]),
                multiplier=win_line["multiplier"],
                consecutive_count=win_line["consecutiveCount"],
                winning_position=tuple(win_line["winningPosition"]),
                wild_count=win_line["wildCount"],
            )
            for win_line in result.get("winLines", [])
        ),
        reel_modifiers=result.get("reelModifiers", []),
        next_feature=result.get("nextFeature"),
        next_feature_sub_type=result.get("nextFeatureSubType"),
        wild_multipliers=result.get("wildMultipliers", []),
        spin_win=_dec(result["spinWin"]),
        max_cap_reached=result["maxCapReached"],
        max_win=_dec(result["maxWin"]),
        feature_trigger_positions=result.get("featureTriggerPositions", []),
        scatter_count=result["scatterCount"],
        is_feature_triggered=result["isFeatureTriggered"],
    )
