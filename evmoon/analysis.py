import datetime
import re
import time
from typing import Tuple, Union

import pandas as pd
import numpy as np
from scipy import optimize

from evmoon import data

REQUEST_INTERVAL_SEC = 2


def get_fund_list_data_frame(fund_source: Union[data.FundSource, str]) -> pd.DataFrame:
    if isinstance(fund_source, data.FundSource):
        pass
    elif fund_source == 'ideco':
        fund_source = data.FundSource.IDECO
    elif fund_source == 'investment_trust':
        fund_source = data.FundSource.INVESTMENT_TRUST
    else:
        raise RuntimeError("Fund sourse '{}' is not supported.".format(fund_source))

    fund_list = data.get_fund_list(fund_source)
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


def optimize_weights(expected_rate_of_returns: float,
                     mean: np.ndarray,
                     cov: np.ndarray,
                     can_sell_short: bool = False) -> Tuple[np.ndarray, float]:
    num_funds = mean.shape[0]

    # 初期値
    weights0 = np.full(num_funds, 1.0 / num_funds)

    # 空売りできない場合は非負制約を付与
    bounds = None if can_sell_short else optimize.Bounds(lb=0.0, ub=np.inf)

    # 目的関数
    def objective_function(weights):
        sum = 0.0
        it = np.nditer(cov, flags=['multi_index'])
        while not it.finished:
            i, j = it.multi_index
            sum += weights[i] * weights[j] * it[0]
            it.iternext()
        return np.sqrt(sum)

    # 重み和の制約
    def weight_sum_constraint(weights):
        return np.sum(weights) - 1.0

    # ポートフォリオリターンの制約
    def portfolio_return_constraint(weights):
        return np.dot(weights, mean) - expected_rate_of_returns

    constraints = [
        {'type': 'eq', 'fun': weight_sum_constraint},
        {'type': 'eq', 'fun': portfolio_return_constraint}
    ]

    # 最適化の実行
    optimize_result = optimize.minimize(fun=objective_function,
                                        x0=weights0,
                                        method='SLSQP',
                                        bounds=bounds,
                                        constraints=constraints,
                                        options={'maxiter': 1000})

    if not optimize_result.success:
        msg = 'Optimization failed. expected_rate_of_returns may not be appropriate. status={}, message="{}"'.format(
            optimize_result.status, optimize_result.message)
        raise RuntimeError(msg)

    # ファンドごとの重みとその重みのときのリスク (標準偏差) を返す
    return optimize_result.x, optimize_result.fun
