from decimal import ROUND_HALF_UP, Decimal

from utils.config_loader import load_paytable

TWO_DP = Decimal("0.01")


class Paytable:
    """Wraps the static paytable reference data (config/paytable.yaml,
    extracted from the math file) and scales credit values to an arbitrary
    total bet. All money values are Decimal, converted via Decimal(str(v))
    to avoid binary floating-point rounding errors."""

    def __init__(self):
        data = load_paytable()
        self.total_bet_credits: Decimal = Decimal(str(data["total_bet_credits"]))
        self.symbols: dict[str, list[Decimal]] = {
            symbol: [Decimal(str(v)) for v in pays] for symbol, pays in data["symbols"].items()
        }

    def raw_pay(self, symbol: str, count: int) -> Decimal:
        """Pay in credits at the reference total bet, for `count` matching
        symbols (3-6)."""
        return self.symbols[symbol][count - 1]

    def pay_for_bet(self, symbol: str, count: int, total_bet) -> Decimal:
        """Pay scaled to `total_bet`, matching the game's win formula:
        credits * (total_bet / reference_total_bet), rounded half-up to 2
        decimals (confirmed game rounding: opCnf.moneyRounding)."""
        total_bet = Decimal(str(total_bet))
        raw = self.raw_pay(symbol, count) * total_bet / self.total_bet_credits
        return raw.quantize(TWO_DP, rounding=ROUND_HALF_UP)

    def as_api_shape(self) -> dict[str, list[Decimal]]:
        """Return the paytable in the same [0, 0, 3oak, 4oak, 5oak, 6oak]
        shape as the live init API's `payTable` field, for direct comparison
        in math/functional assertions."""
        return self.symbols
