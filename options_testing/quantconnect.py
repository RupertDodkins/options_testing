import pandas as pd
import numpy as np
import os

def load_tsla_minutely(data_dir=None, suffix=None):
    if not data_dir:
        data_dir = '/Users/dodkins/PythonProjects/stocks/options_testing/data/'
    if not suffix:
        suffix = 'tsla_minutely_'
    tsla = pd.DataFrame(columns=['date', 'open','close'])
    for col, dtype in zip(['date', 'open','close'], [str, float, float]):
        tsla_col_loc = os.path.join(data_dir, f'{suffix}{col}.txt')
        tsla[col] = np.loadtxt(tsla_col_loc, delimiter=',', dtype=dtype)
    tsla = tsla.set_index('date')
    return tsla

def load_tsla_hourly(data_dir=None, suffix=None):
    df_loc = '/Users/dodkins/PythonProjects/stocks/options_testing/data/tsla_hourly_2010+'
    if os.path.exists(df_loc):
        tsla = pd.read_csv(df_loc, index_col='datetime')
    else:
        if not data_dir:
            data_dir = '/Users/dodkins/PythonProjects/stocks/options_testing/data/'
        if not suffix:
            suffix = 'tsla_hourly_'
        cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        tsla = pd.DataFrame(columns=cols)
        for col, dtype in zip(cols, [str, float, float, float, float, float]):
            tsla_col_loc = os.path.join(data_dir, f'{suffix}{col}.txt')
            data = np.loadtxt(tsla_col_loc, delimiter=',', dtype=dtype)[:21450]
            print(col, len(data))
            tsla[col] = data
        tsla = tsla.set_index('datetime')
        tsla = tsla.iloc[:-7]
        tsla.to_csv(df_loc)
    return tsla
