"""The forecasting model (the AI part of DukaTrack).

Works on ONE product at a time using its daily sales history.
- 28 days or more of history -> Holt-Winters exponential smoothing with a weekly pattern
  (shops sell more on some days of the week).
- 14 to 27 days            -> damped-trend exponential smoothing.
- fewer than 14 days        -> simple average of the days we have.
This keeps it usable for a single small shop with little data.
"""
import warnings
import numpy as np
import pandas as pd


def forecast_total(daily: pd.Series, days: int):
    """daily: units sold per day (index = consecutive dates). Returns (total, method)."""
    daily = daily.astype(float)
    n = len(daily)
    if n == 0 or daily.sum() == 0:
        return 0.0, "no sales history"
    method = "average"
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if n >= 28:
                fit = ExponentialSmoothing(daily.values, trend="add", damped_trend=True,
                                           seasonal="add", seasonal_periods=7).fit()
                method = "Holt-Winters (weekly pattern)"
            elif n >= 14:
                fit = ExponentialSmoothing(daily.values, trend="add", damped_trend=True).fit()
                method = "damped trend"
            else:
                fit = None
        if fit is not None:
            values = fit.forecast(days)
            return float(np.clip(values, 0, None).sum()), method
    except Exception:
        pass                                  # fall back to the average below
    return float(daily.tail(14).mean() * days), "average"


def daily_series(rows, end_day):
    """rows: list of (date, quantity). Gives one number per day, zero when nothing sold."""
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series({pd.Timestamp(d): q for d, q in rows}, dtype=float)
    s = s.groupby(level=0).sum()
    full = pd.date_range(s.index.min(), pd.Timestamp(end_day), freq="D")
    return s.reindex(full, fill_value=0.0)
