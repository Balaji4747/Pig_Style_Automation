import pytest

from utils.paytable_loader import Paytable


@pytest.mark.math
def test_live_paytable_matches_math_file(init_data):
    """PS-FUN-023..033: the live game session's paytable (init_data, read at
    runtime from the init API response) must match the math file's paytable
    (config/paytable.yaml, extracted from pig_style_R7_1.xlsx) exactly, for
    every symbol and every OAK count."""
    math_paytable = Paytable()
    live_paytable = init_data.game_info.pay_table

    assert live_paytable.keys() == math_paytable.as_api_shape().keys()
    for symbol, math_pays in math_paytable.as_api_shape().items():
        assert live_paytable[symbol] == math_pays, (
            f"Symbol {symbol}: live={live_paytable[symbol]} math_file={math_pays}"
        )
