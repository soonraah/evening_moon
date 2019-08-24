import datetime
from enum import Enum
import re
import time

import pandas as pd
import numpy as np

from evmoon import data

REQUEST_INTERVAL_SEC = 2


class FundSource(Enum):
    IDECO = 1               # iDeCo: https://site0.sbisec.co.jp/marble/insurance/dc401k/search/dc401ksearch.do?
    INVESTMENT_TRUST = 2    # 投資信託: https://site0.sbisec.co.jp/marble/fund/powersearch/fundpsearch.do?


def get_fund_list_data_frame(fund_source: FundSource = FundSource.IDECO) -> pd.DataFrame:
    if fund_source == FundSource.IDECO:
        fund_list = data.get_ideco_fund_list()
    elif fund_source == FundSource.INVESTMENT_TRUST:
        fund_list = data.get_investment_trust_fund_list()
    else:
        raise RuntimeError('Unsupported fund source ({}) is given.'.format(fund_source))

    data_frame = pd.DataFrame(fund_list)
    column_names = list(data_frame)
    rename_dict = {name: _camel_to_snake(name) for name in column_names}
    data_frame.rename(columns=rename_dict, inplace=True)
    return data_frame.set_index('fund_code')


def _camel_to_snake(s: str):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_price_data_frame(fund_codes: list,
                         start_period: datetime.date = None,
                         end_period: datetime.date = None) -> pd.DataFrame:
    sers = {}

    for fund_code in fund_codes:
        if fund_code != fund_codes[0]:
            time.sleep(REQUEST_INTERVAL_SEC)

        prices = data.get_reference_price(fund_code, start_period, end_period)
        df_raw = pd.DataFrame(prices).set_index('date')
        sers[fund_code] = df_raw['reference_price']         # 同じ長さ取れるとは限らないので Series で結合するのが良さそう

    df_price = pd.concat(sers, axis=1)
    return df_price.sort_index()


def calc_rate_of_return(fund_codes: list,
                        start_period: datetime.date = None,
                        end_period: datetime.date = None,
                        investment_period_days: int = 5) -> pd.DataFrame:
    assert investment_period_days > 0, 'investment_period_days must be > 0'

    df_price = get_price_data_frame(fund_codes, start_period, end_period)
    sers = {}

    for fund_code in fund_codes:
        ser = df_price[fund_code]
        ser_shifted = ser.shift(investment_period_days)
        ser_shifted.name = fund_code + '_shifted'
        df_shifted = pd.concat([ser_shifted, ser], axis=1)

        sers[fund_code] = df_shifted.apply(lambda x: (x[1] - x[0]) / x[0], axis=1)

    return pd.concat(sers, axis=1).dropna()


def calc_mean_std(fund_codes: list,
                  start_period: datetime.date = None,
                  end_period: datetime.date = None,
                  investment_period_days: int = 5) -> pd.DataFrame:
    df_return = calc_rate_of_return(fund_codes, start_period, end_period, investment_period_days)
    ser_mean = df_return.mean()
    ser_std = df_return.std(ddof=0)
    df_ret = pd.concat({'mean': ser_mean, 'std': ser_std}, axis=1).sort_index()
    df_ret.index.name = 'fund_code'
    return df_ret


def _calc_portfolio_mean_std(weights: np.array, mean: np.array, cov: np.ndarray) -> tuple:
    p_mean = np.dot(weights, mean).sum()
    p_var = 0
    it = np.nditer(cov, flags=['multi_index'])
    while not it.finished:
        i, j = it.multi_index
        p_var += weights[i] * weights[j] * it[0]
        it.iternext()
    return p_mean, np.sqrt(p_var)


def calc_random_weight_portfolios(num_iter: int, mean: np.array, cov: np.ndarray) -> np.ndarray:
    ret = []
    for i in range(num_iter):
        r = np.random.rand(mean.size)
        weights = r / r.sum()                                           # 乱数で重みを用意
        p_mean, p_std = _calc_portfolio_mean_std(weights, mean, cov)    # その重みポートフォリオの場合の平均・共分散を計算
        ret.append([p_mean, p_std])
    return np.array(ret).transpose()
