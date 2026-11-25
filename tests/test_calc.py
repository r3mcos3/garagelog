"""Pure calculation tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from custom_components.garagelog import calc


def R(d, odo, litres, full=True, cost=None):
    return {"date": d, "odometer": odo, "liters": litres, "full": full, "total_cost": cost}


def test_normalize_refuel_derives_missing_value():
    assert calc.normalize_refuel(40, None, 1.8) == (40, 72.0, 1.8)
    assert calc.normalize_refuel(40, 72, None) == (40, 72, 1.8)
    with pytest.raises(ValueError):
        calc.normalize_refuel(0, 1, None)


def test_consumption_full_to_full():
    refuels = [R("2026-01-01", 1000, 40), R("2026-02-01", 1500, 30), R("2026-03-01", 2100, 36)]
    seg = calc.consumption_segments(refuels)
    assert [s["l_per_100km"] for s in seg] == [6.0, 6.0]
    assert calc.average_consumption(seg) == 6.0
    assert calc.km_per_litre(6.0) == 16.67


def test_consumption_partial_fills_are_summed():
    refuels = [
        R("2026-01-01", 1000, 40),
        R("2026-01-10", 1200, 10, full=False),
        R("2026-02-01", 1500, 20),
    ]
    seg = calc.consumption_segments(refuels)
    assert len(seg) == 1
    assert seg[0]["litres"] == 30.0 and seg[0]["km"] == 500.0 and seg[0]["l_per_100km"] == 6.0


def test_consumption_needs_two_full_tanks_and_ignores_leading_partials():
    assert calc.consumption_segments([R("2026-01-01", 1000, 40)]) == []
    assert calc.consumption_segments([R("2026-01-01", 900, 5, full=False), R("2026-02-01", 1000, 40)]) == []
    assert calc.average_consumption([]) is None


def test_costs():
    costs = calc.all_costs(
        [R("2025-12-20", 1, 10, cost=20)],
        [{"date": "2026-03-05", "cost": 300}],
        [{"date": "2026-03-10", "cost": 10}, {"date": "2026-03-11"}],
    )
    assert calc.cost_total(costs) == 330
    assert calc.cost_in_year(costs, 2026) == 310
    assert calc.cost_in_month(costs, 2026, 3) == 310
    assert calc.average_monthly_cost(costs, date(2026, 3, 31)) == 82.5  # dec..mar = 4 months
    assert calc.average_monthly_cost([], date(2026, 3, 31)) is None


def test_next_service_interval_and_explicit():
    services = [{"date": "2026-01-10", "odometer": 10000, "type": "maintenance"}]
    res = calc.next_service(
        services, interval_km=15000, interval_days=365, today=date(2026, 6, 1), odometer=14000
    )
    assert res["due_odometer"] == 25000 and res["km"] == 11000
    assert res["due_date"] == date(2027, 1, 10) and res["days"] == 223
    services[0].update(next_due_date="2026-07-01", next_due_odometer=16000)
    res = calc.next_service(services, interval_km=None, interval_days=None, today=date(2026, 6, 1), odometer=15500)
    assert (res["days"], res["km"]) == (30, 500)


def test_next_service_none_without_maintenance():
    res = calc.next_service([{"date": "2026-01-01", "type": "oil_change"}], interval_km=1, interval_days=1,
                            today=date(2026, 6, 1), odometer=5)
    assert res["days"] is None and res["km"] is None


@pytest.mark.parametrize(
    ("days", "status"),
    [(None, "ok"), (0, "ok"), (29, "ok"), (30, "soon"), (59, "soon"), (60, "due"), (200, "due")],
)
def test_wash_status(days, status):
    assert calc.wash_status(days, 30, 60) == status


def test_tyres():
    assert calc.to_bar(250, "kPa") == 2.5
    assert calc.to_bar(2.4, "bar") == 2.4
    assert calc.to_bar(36, "psi") == pytest.approx(2.482, abs=0.001)
    assert calc.tyre_deviation({"fl": 2.5, "fr": 2.2, "rl": 2.6, "rr": 2.5}, 2.5) == 0.3
    assert calc.tyre_deviation({}, 2.5) is None


def test_oil_check_due_date_is_first_weekend_a_month_after_the_last_check():
    assert calc.oil_check_due_date([]) is None
    assert calc.oil_check_due_date([{"date": "2026-10-25"}]) == date(2026, 11, 28)  # Wed 25 Nov -> Sat
    assert calc.oil_check_due_date([{"date": "2026-06-27"}, {"date": "2026-07-25"}]) == date(2026, 8, 29)  # Tue 25 Aug -> Sat
    assert calc.oil_check_due_date([{"date": "2026-12-31"}]) == date(2027, 1, 31)  # a Sunday
    assert calc.oil_check_due_date([{"date": "2027-01-31"}]) == date(2027, 2, 28)  # clamped, a Sunday


def test_oil_check_due():
    last = [{"date": "2026-10-25"}]
    assert not calc.oil_check_due(date(2026, 11, 27), last)
    assert calc.oil_check_due(date(2026, 11, 28), last)
    assert calc.oil_check_due(date(2026, 12, 15), last)
    assert not calc.oil_check_due(date(2026, 12, 15), [*last, {"date": "2026-11-28"}])
    assert not calc.oil_check_due(date(2026, 11, 1), [])



def test_oil_estimate():
    samples = [
        {"date": "2026-01-01", "odometer": 10000, "life_pct": 100},
        {"date": "2026-04-11", "odometer": 12000, "life_pct": 80},
    ]
    est = calc.oil_estimate(samples, today=date(2026, 4, 11), odometer=12000)
    assert est["estimate"] is True
    assert est["km"] == 8000  # 20% per 2000km -> 80% left = 8000km
    assert est["date"] == date(2026, 4, 11).fromordinal(date(2026, 4, 11).toordinal() + 400)  # 100 days: 20%


def test_oil_estimate_needs_enough_data():
    assert calc.oil_estimate([], today=date(2026, 1, 1), odometer=None) is None
    one = [{"date": "2026-01-01", "odometer": 1, "life_pct": 100}]
    assert calc.oil_estimate(one, today=date(2026, 1, 1), odometer=None) is None
    small = [*one, {"date": "2026-01-10", "odometer": 500, "life_pct": 99}]
    assert calc.oil_estimate(small, today=date(2026, 1, 10), odometer=500) is None


# ---------------------------------------------------------------- fuel prices
def _log(*pairs):
    return [{"price": p, "at": f"{d}T12:00:00+00:00"} for d, p in pairs]


def test_price_change_previous_and_since():
    log = _log(("2026-10-01", 1.90), ("2026-10-10", 1.85), ("2026-10-20", 1.85), ("2026-11-01", 1.80))
    change = calc.price_change(log)
    assert change["previous"] == 1.85 and change["direction"] == "down" and change["delta"] == -0.05
    assert change["since"].startswith("2026-11-01")
    log.append({"price": 1.80, "at": "2026-11-05T12:00:00+00:00"})
    assert calc.price_change(log)["since"].startswith("2026-11-01")  # same price: since the first of the run
    assert calc.price_change(_log(("2026-10-01", 1.9)))["previous"] is None
    assert calc.price_change([])["direction"] is None


def test_weighted_average_counts_duration():
    log = _log(("2026-10-01", 2.00), ("2026-10-11", 1.00))
    now = datetime(2026, 10, 21, 12, tzinfo=UTC)
    assert calc.weighted_average_price(log, now) == pytest.approx(1.5)
    assert calc.weighted_average_price([], now) is None


def test_price_trend_needs_14_days_and_one_percent():
    now = datetime(2026, 11, 1, 12, tzinfo=UTC)
    assert calc.price_trend(_log(("2026-10-25", 1.9)), 1.7, now) is None  # only 7 days
    log = _log(("2026-10-01", 2.00), ("2026-10-20", 1.80))
    trend = calc.price_trend(log, 1.80, now)
    assert trend["pct"] < 0 and trend["days"] == 31
    assert calc.price_trend(_log(("2026-10-01", 1.80)), 1.80, now) is None  # equal to its average
    assert calc.price_trend(log, None, now) is None


def test_best_weekday_needs_history_and_a_gap():
    now = datetime(2026, 11, 20, 12, tzinfo=UTC)
    short = _log(("2026-10-25", 1.8))
    assert calc.best_weekday(short, date(2026, 11, 20), now) is None
    # a price that is 10 cents lower on every Sunday only: logged as changes each week
    log = []
    day = date(2026, 1, 4)  # a Sunday
    while day < date(2026, 11, 20):
        log.append({"price": 1.80, "at": f"{day.isoformat()}T01:00:00+00:00"})
        log.append({"price": 1.90, "at": f"{date.fromordinal(day.toordinal() + 1).isoformat()}T01:00:00+00:00"})
        day = date.fromordinal(day.toordinal() + 7)
    best = calc.best_weekday(log, date(2026, 11, 20), now)
    assert best["cheapest"] == 6 and best["gap"] >= 0.005
    assert calc.best_weekday(_log(("2026-01-01", 1.8)), date(2026, 11, 20), now) is None  # flat: no gap


def test_top_up_full_tank_or_missing_part():
    assert calc.top_up(1.8, 50, None) == {"liters": 50.0, "cost": 90.0}
    assert calc.top_up(1.8, 50, 40) == {"liters": 30.0, "cost": 54.0}
    assert calc.top_up(1.8, 50, 120)["liters"] == 0.0
