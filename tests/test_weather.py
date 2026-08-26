"""Tests for the weather adapter — the 3 Open-Meteo traps (§29.2), all offline (no network)."""
import pytest

from adapters.weather import NodeSeries, OpenMeteoProvider, ReplayProvider, align_from_date


def _series(lat, lon, times, temps):
    return NodeSeries(lat=lat, lon=lon, times=tuple(times),
                      variables={"temperature_2m": tuple(temps)})


def test_replay_returns_series_in_request_order():
    s0 = _series(27.4, 79.6, ["2026-01-10T00:00"], [12.0])
    s1 = _series(27.5, 79.7, ["2026-01-10T00:00"], [13.0])
    prov = ReplayProvider([s0, s1])
    out = prov.fetch([(27.4, 79.6), (27.5, 79.7)])
    assert [s.lat for s in out] == [27.4, 27.5]


def test_replay_rejects_coord_count_mismatch():
    prov = ReplayProvider([_series(27.4, 79.6, ["2026-01-10T00:00"], [12.0])])
    with pytest.raises(ValueError):
        prov.fetch([(27.4, 79.6), (27.5, 79.7)])   # 2 coords, 1 series


def test_align_handles_past_days_origin_shift():
    # Trap #2: with past_days=2, index 0 is TWO DAYS AGO. Aligning to "today" must trim it.
    times = ["2026-01-08T00:00", "2026-01-09T00:00", "2026-01-10T00:00", "2026-01-11T00:00"]
    s = _series(27.4, 79.6, times, [1.0, 2.0, 3.0, 4.0])
    aligned = align_from_date(s, "2026-01-10")
    assert aligned.times[0] == "2026-01-10T00:00"
    assert aligned.variables["temperature_2m"] == (3.0, 4.0)   # origin correctly shifted


def test_align_to_future_date_yields_empty():
    s = _series(27.4, 79.6, ["2026-01-08T00:00"], [1.0])
    aligned = align_from_date(s, "2026-01-10")
    assert aligned.times == ()


class _FakeResp:
    def __init__(self, payload): self._payload = payload
    def raise_for_status(self): pass
    def json(self): return self._payload


def test_openmeteo_normalises_single_object_and_checks_snap(monkeypatch):
    # Trap #1: a single coordinate comes back as an OBJECT, not a list. Trap #3: snapped
    # coords must be near the request. We stub requests.get so no network is touched.
    payload = {  # note: object, not [ ... ]
        "latitude": 27.41, "longitude": 79.59,   # snapped, within tolerance
        "hourly": {"time": ["2026-01-10T00:00"], "temperature_2m": [12.3]},
    }
    import adapters.weather as w
    monkeypatch.setattr(w.requests, "get", lambda *a, **k: _FakeResp(payload))
    out = OpenMeteoProvider().fetch([(27.4, 79.6)], variables=("temperature_2m",))
    assert len(out) == 1
    assert (out[0].lat, out[0].lon) == (27.4, 79.6)      # keeps REQUESTED coords
    assert out[0].variables["temperature_2m"] == (12.3,)


def test_openmeteo_rejects_far_snap(monkeypatch):
    payload = {"latitude": 30.0, "longitude": 79.6,       # 2.6 deg off -> real mismatch
               "hourly": {"time": ["2026-01-10T00:00"], "temperature_2m": [12.3]}}
    import adapters.weather as w
    monkeypatch.setattr(w.requests, "get", lambda *a, **k: _FakeResp(payload))
    with pytest.raises(ValueError):
        OpenMeteoProvider().fetch([(27.4, 79.6)], variables=("temperature_2m",))
