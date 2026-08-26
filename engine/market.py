"""Mandi price momentum — the market-access index (PRD §PS302, deck p.2/p.5).

🔴 PURE. No network, no clock. The Agmarknet fetch lives in adapters/mandi.py; this module only
does arithmetic on a price series it is handed.

Answers the deck's second farmer question: "sell where, and sell when". A disease warning that
saves the crop is only half the value if the farmer then sells it into the worst mandi on the worst
day.

🔴 THE NET-PRICE RULE. A higher headline price at a distant mandi is often a LOSS once the farmer
pays for transport. Every comparison in this module is on price NET of transport, and
`MandiOption.gross_premium_inr` is kept alongside so the UI can show the farmer exactly how much
the trip ate. Reporting the gross premium alone would push smallholders into trips that lose money.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

Momentum = Literal["rising", "flat", "falling", "unknown"]

# Below this many observations the trend is noise, not a signal.
MIN_OBSERVATIONS_FOR_TREND = 4

# A move smaller than this is within normal daily mandi noise and is reported as flat.
FLAT_BAND_PCT = 3.0


@dataclass(frozen=True)
class PricePoint:
    """One modal price observation for one mandi on one day. Rupees per quintal."""

    date: str          # ISO date, kept as a string because this module never parses clocks
    mandi: str
    modal_price: float


@dataclass(frozen=True)
class MandiOption:
    """One place the farmer could sell, ranked on net realisation."""

    mandi: str
    modal_price: float
    distance_km: float
    transport_cost_inr: float      # for the whole load, not per quintal
    net_price_per_quintal: float
    net_realisation_inr: float     # for the load the farmer actually has
    gross_premium_inr: float       # what the headline price suggested, before transport


@dataclass(frozen=True)
class MarketSignal:
    momentum: Momentum
    change_pct: float
    latest_price: float
    mean_price: float
    best: MandiOption | None
    alternatives: tuple[MandiOption, ...]
    advice_key: str                # a translation key, never farmer-facing English
    caveats: tuple[str, ...]


def compute_momentum(series: Sequence[PricePoint]) -> tuple[Momentum, float, float, float]:
    """
    Compare the latest price against the mean of the earlier half of the window.

    🔴 Deliberately NOT a linear regression or a moving-average crossover. Mandi series here are a
    handful of noisy points; a slope fitted to five numbers looks authoritative and means nothing.
    Comparing the latest value to the earlier mean is crude, robust, and explainable to a farmer in
    one sentence — which matters more than sophistication for a number someone will act on.
    """
    if len(series) < MIN_OBSERVATIONS_FOR_TREND:
        latest = series[-1].modal_price if series else 0.0
        return "unknown", 0.0, latest, latest

    prices = [p.modal_price for p in series]
    latest = prices[-1]
    earlier = prices[: max(1, len(prices) // 2)]
    baseline = sum(earlier) / len(earlier)
    mean_all = sum(prices) / len(prices)

    if baseline <= 0:
        return "unknown", 0.0, latest, mean_all

    change_pct = ((latest - baseline) / baseline) * 100.0

    if abs(change_pct) < FLAT_BAND_PCT:
        momentum: Momentum = "flat"
    elif change_pct > 0:
        momentum = "rising"
    else:
        momentum = "falling"

    return momentum, round(change_pct, 1), round(latest, 2), round(mean_all, 2)


def rank_mandis(
    quotes: Sequence[tuple[str, float, float]],
    *,
    load_quintals: float,
    transport_inr_per_km: float,
) -> tuple[MandiOption, ...]:
    """
    Rank mandis by NET realisation for this specific load.

    `quotes` is (mandi_name, modal_price_per_quintal, distance_km).

    🔴 Transport is charged for the ROUND trip. A farmer pays to come back with an empty trolley,
    and halving that cost is how a comparison quietly turns a losing trip into a winning one.
    """
    if load_quintals <= 0:
        raise ValueError("load_quintals must be positive")

    options: list[MandiOption] = []
    nearest_price = None
    if quotes:
        nearest = min(quotes, key=lambda q: q[2])
        nearest_price = nearest[1]

    for mandi, price, distance_km in quotes:
        transport = distance_km * 2.0 * transport_inr_per_km
        net_total = price * load_quintals - transport
        net_per_quintal = net_total / load_quintals
        gross_premium = (
            (price - nearest_price) * load_quintals if nearest_price is not None else 0.0
        )
        options.append(
            MandiOption(
                mandi=mandi,
                modal_price=round(price, 2),
                distance_km=round(distance_km, 1),
                transport_cost_inr=round(transport, 0),
                net_price_per_quintal=round(net_per_quintal, 2),
                net_realisation_inr=round(net_total, 0),
                gross_premium_inr=round(gross_premium, 0),
            )
        )

    return tuple(sorted(options, key=lambda o: o.net_realisation_inr, reverse=True))


def build_market_signal(
    series: Sequence[PricePoint],
    quotes: Sequence[tuple[str, float, float]],
    *,
    load_quintals: float,
    transport_inr_per_km: float,
    is_stale: bool = False,
) -> MarketSignal:
    """Combine the trend and the mandi ranking into one signal for the UI."""
    momentum, change_pct, latest, mean_price = compute_momentum(series)
    ranked = rank_mandis(quotes, load_quintals=load_quintals,
                         transport_inr_per_km=transport_inr_per_km) if quotes else ()

    # 🔴 advice_key is a key, never a sentence. Farmer-facing wording lives in the i18n layer so
    # this pure module can never leak untranslated English onto a Hindi screen.
    if momentum == "rising":
        advice_key = "market.hold_prices_rising"
    elif momentum == "falling":
        advice_key = "market.sell_soon_prices_falling"
    elif momentum == "flat":
        advice_key = "market.no_timing_edge"
    else:
        advice_key = "market.insufficient_data"

    caveats: list[str] = []
    if len(series) < MIN_OBSERVATIONS_FOR_TREND:
        caveats.append(f"only {len(series)} price observations; trend not reported")
    if is_stale:
        caveats.append("prices are from the last successful fetch, not today")
    if ranked and len(ranked) == 1:
        caveats.append("only one mandi quoted; no comparison possible")

    return MarketSignal(
        momentum=momentum,
        change_pct=change_pct,
        latest_price=latest,
        mean_price=mean_price,
        best=ranked[0] if ranked else None,
        alternatives=ranked[1:] if len(ranked) > 1 else (),
        advice_key=advice_key,
        caveats=tuple(caveats),
    )
