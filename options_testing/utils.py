import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from scipy.stats import norm

def uniform_samp(df):
    diff = np.array(df.index[1:] - df.iloc[:-1].index)/np.timedelta64(1,'ns')
    jump_locs = np.where(diff != diff[0])[0]
    diff = jump_locs[1:] - jump_locs[:-1]
    jump_locs = np.where(diff != diff[0])[0].any()
    return jump_locs

def aggregate(df_minutely, freq='hourly'):
    dt_args = ['year', 'month', 'day', 'hour', 'minute']
    dt_starts = {dta: s for dta, s in zip(dt_args, [1970, 1, 1, 9, 30])}

    times = pd.to_datetime(df_minutely.index)
    if freq == 'hourly':
        groups = ['year', 'month', 'day', 'hour']
    elif freq == 'daily':
        groups = ['year', 'month', 'day']
    elif freq == 'weekly':
        groups = ['year', 'week']
    elif freq == 'monthly':
        groups = ['year', 'month']
    else:
        raise ValueError(f"frequency '{freq}' not recognised")

    grouped = df_minutely.groupby([getattr(times, g) for g in groups])
    close = grouped.close.last()
    df_subsamp = pd.DataFrame(index=range(len(close)), columns=['open', 'high', 'low', 'close', 'volume'])
    df_subsamp['open'] = np.array(grouped.open.first())
    df_subsamp['high'] = np.array(grouped.open.max())
    df_subsamp['low'] = np.array(grouped.open.min())
    df_subsamp['close'] = np.array(close)
    df_subsamp['volume'] = np.array(grouped.volume.sum())

    indices = np.empty(len(close), dtype=datetime)
    for r, dt_tup in enumerate(zip(*[close.index.get_level_values(i) for i in range(len(groups))])):
        kwargs = {k: dt_tup[groups.index(k)] if k in groups else dt_starts[k] for k in dt_args}

        if 'week' in groups:
            weeks = dt_tup[groups.index('week')]
        else:
            weeks = 0
        week_offset = relativedelta(weeks=weeks)
        date = datetime(**kwargs) + week_offset

        indices[r] = date
    df_subsamp.index = indices
    return df_subsamp

def concat_dfs(main_df, indicator_df):
    cols = indicator_df.columns
    for col in cols:
        main_df[col] = np.nan
        main_df.loc[indicator_df.index, col] = indicator_df[col].array
    return main_df

def get_start_price(df, g, expiration):
    options_create = g.underlying_open.first()
    df = df.merge(options_create, left_on=['year' ,expiration], right_on=['year' ,expiration], suffixes=('', '_b'))
    df = df.rename(columns={'underlying_open_b': 'start_price'})
    return df

def format_dates(*dates):
    dates = [datetime(*date) if isinstance(date, tuple) else date for date in dates]
    if len(dates) == 1:
        dates = dates[0]
    return dates

def black_scholes(S, K, T, r, sigma, right='c'):
    '''

    :param S: Asset price
    :param K: Strike price
    :param T: Time to maturity
    :param r: risk-free rate (treasury bills)
    :param sigma: volatility
    :return: call price
    '''

    N_prime = norm.pdf
    N = norm.cdf

    T /= 365.
    r /= 100.
    sigma /= 100.

    ###standard black-scholes formula
    d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if right == 'c':
        contract = S * N(d1) - N(d2)* K * np.exp(-r * T)
    else:
        contract = N(-d2) * K * np.exp(-r * T) - S * N(-d1)
    return contract

def colfix(df, L=5): 
    df = df.rename(columns=lambda x: ''.join(x.replace('_', ' ')[i:i+L] for i in range(0,len(x),L)))# if df[x].dtype in ['float64','int64'] else x)
    df = df.round(decimals=2)
    return df

def pretty_strat_df(df):
    df = df.drop(['underlying_high', 'underlying_low', 'volume', 'week', 'year', 'date_expiration'], axis=1)
    df = colfix(df)
    return df