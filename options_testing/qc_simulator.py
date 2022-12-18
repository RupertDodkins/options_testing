import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from datetime import datetime, timedelta
import copy

from quantconnect import load_tsla_hourly
from utils import format_dates, black_scholes

class QuantBook():
    def __init__(self):
        self.Securities = Securities()
        self.OptionChainProvider = OptionChainProvider()

    def AddEquity(self, ticker):
        self.Securities.Keys = Equity(ticker)
        return self.Securities.Keys

    def History(self, keys, *args):
        tsla = load_tsla_hourly()
        tsla.index = pd.to_datetime(tsla.index)

        if isinstance(keys, Equity):
            nbar, res = args
            assert res == 'h'
            tsla = tsla.iloc[:nbar]
            tsla['symbol'] = 'lol'
            tsla['time'] = tsla.index
            tsla.set_index(['symbol', 'time'], inplace=True)
        elif isinstance(keys, Contract):
            start, expiration, res = args
            print(keys.ID.__dict__, expiration)
            assert res == 'h'
            start, expiry = format_dates(start, expiration)
            tsla = tsla[start:expiration]
            for index, row in tsla.iterrows():
                ohlc = black_scholes(row[['open', 'high', 'low', 'close']].array, keys.ID.StrikePrice,
                                   (keys.ID.Date-index).days, r=3, sigma=53, right=keys.ID.OptionRight)
                tsla.loc[index][['open', 'high', 'low', 'close']] = ohlc
            tsla['expiry'] = expiration
            tsla['strike'] = keys.ID.StrikePrice
            tsla['type'] = keys.ID.OptionRight
            tsla['symbol'] = 'lol'
            tsla['time'] = tsla.index
            tsla.set_index(['expiry', 'strike', 'type', 'symbol', 'time'], inplace=True)
        else:
            raise NotImplementedError

        return tsla

class Equity():
    def __init__(self, ticker):
        self.Symbol = ticker

class Securities():
    def __init__(self):
        self.Keys = None


class OptionChainProvider():
    def __init__(self):
        self.tsla_underlying = load_tsla_hourly()['open']
        self.tsla_underlying.index = pd.to_datetime(self.tsla_underlying.index)

    def GetOptionContractList(self, symbol, start, weeks_out=4, strikes_out=15, strike_sep_factor=50,
                              split_correct=(2022, 8, 25)):
        # TODO possibly implement monthly expirations after weeklies

        assert symbol.upper() == 'TSLA'
        start = format_dates(start)

        underlying_price = self.tsla_underlying[self.tsla_underlying.index <= start.replace(hour=0, minute=0)][-1]
        underlying_price = np.round(underlying_price)

        if split_correct:  # qc's get_available_strikes has the listed strike prices at the time (not corrected to today)
            split_correct = format_dates(split_correct)
            if start < split_correct:
                underlying_price *= 3

        strike_sep = underlying_price/strike_sep_factor
        strike_sep = np.round(strike_sep)

        rights = ['Call', 'Put']
        closest_exp = start.replace(hour=0, minute=0) + timedelta(days=4 - start.weekday()) #+ timedelta(hours=16-start.hour)
        strikes = underlying_price + np.arange(-strikes_out, strikes_out+1)*strike_sep
        dates = [closest_exp + timedelta(days=7*week) for week in range(weeks_out)]

        contract_symbols = [Contract(strike, right, date) for right in rights for date in dates for strike in strikes]
        return contract_symbols


class Contract():
    def __init__(self, strike, right, date):
        self.ID = ContractMeta(strike, right, date)


class ContractMeta():
    def __init__(self, strike=300, right='Call', date=None):
        self.StrikePrice = strike
        self.OptionRight = getattr(OptionRight, right)
        self.Date = date


class Resolution():
    # def __init__(self):
    Hour = 'h'

class OptionRight():
    # def __init__(self):
    Call = 'c'
    Put = 'p'
