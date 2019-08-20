import datetime
import unittest

import mock
import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal

from evmoon import analysis

DATES = [datetime.date(2017, 1, 4),
         datetime.date(2017, 1, 5),
         datetime.date(2017, 1, 6),
         datetime.date(2017, 1, 10),
         datetime.date(2017, 1, 11)]

REFERENCE_PRICE_1 = [10354.0, 10317.0, 10265.0, 10272.0, 10275.0]
REFERENCE_PRICE_2 = [11097.0, 11151.0, 11158.0, 11231.0, 11189.0]
REFERENCE_PRICE_3 = [10911.0, 10954.0, 10986.0, 10970.0, 10953.0]


def mock_get_reference_price(fund_code: str, start_period=None, end_period=None):
    if fund_code == 'AAA111':
        return [{'date': DATES[i], 'reference_price': REFERENCE_PRICE_1[i]} for i in range(0, 5)]
    elif fund_code == 'BBB222':
        return [{'date': DATES[i], 'reference_price': REFERENCE_PRICE_2[i]} for i in range(0, 5)]
    elif fund_code == 'CCC333':
        return [{'date': DATES[i], 'reference_price': REFERENCE_PRICE_3[i]} for i in range(0, 5)]
    else:
        return None


@mock.patch('evmoon.data.get_reference_price', new=mock_get_reference_price)
class TestAnalysisPy(unittest.TestCase):

    def test_get_price_data_frame(self):
        # -- setup --
        fund_codes = ['AAA111', 'BBB222', 'CCC333']
        start_period = datetime.date(2017, 1, 4)
        end_period = datetime.date(2017, 1, 11)

        # -- exercise --
        actual = analysis.get_price_data_frame(fund_codes, start_period, end_period)

        # -- verify --
        expected = pd.DataFrame.from_dict(
            {'date': DATES,
             'AAA111': REFERENCE_PRICE_1,
             'BBB222': REFERENCE_PRICE_2,
             'CCC333': REFERENCE_PRICE_3}
        ).set_index('date')

        assert_frame_equal(actual, expected)

    def test_calc_rate_of_return(self):
        # -- setup --
        fund_codes = ['AAA111', 'BBB222', 'CCC333']
        start_period = datetime.date(2017, 1, 4)
        end_period = datetime.date(2017, 1, 11)
        investment_period_days = 2

        # -- exercise --
        actual = analysis.calc_rate_of_return(fund_codes, start_period, end_period, investment_period_days)

        # -- verify --
        expected = pd.DataFrame.from_dict(
            {'date': DATES[2:],
             'AAA111': [(REFERENCE_PRICE_1[i] - REFERENCE_PRICE_1[i - 2]) / REFERENCE_PRICE_1[i - 2] for i in range(2, 5)],
             'BBB222': [(REFERENCE_PRICE_2[i] - REFERENCE_PRICE_2[i - 2]) / REFERENCE_PRICE_2[i - 2] for i in range(2, 5)],
             'CCC333': [(REFERENCE_PRICE_3[i] - REFERENCE_PRICE_3[i - 2]) / REFERENCE_PRICE_3[i - 2] for i in range(2, 5)]}
        ).set_index('date')

        assert_frame_equal(actual, expected)

    def test_calc_mean_std(self):
        # -- setup --
        fund_codes = ['AAA111', 'BBB222', 'CCC333']
        start_period = datetime.date(2017, 1, 4)
        end_period = datetime.date(2017, 1, 11)
        investment_period_days = 2

        # -- exercise --
        actual = analysis.calc_mean_std(fund_codes, start_period, end_period, investment_period_days)

        # -- verify --
        rate_of_return_1 = [(REFERENCE_PRICE_1[i] - REFERENCE_PRICE_1[i - 2]) / REFERENCE_PRICE_1[i - 2] for i in range(2, 5)]
        rate_of_return_2 = [(REFERENCE_PRICE_2[i] - REFERENCE_PRICE_2[i - 2]) / REFERENCE_PRICE_2[i - 2] for i in range(2, 5)]
        rate_of_return_3 = [(REFERENCE_PRICE_3[i] - REFERENCE_PRICE_3[i - 2]) / REFERENCE_PRICE_3[i - 2] for i in range(2, 5)]
        expected = pd.DataFrame.from_dict(
            {'fund_code': ['AAA111', 'BBB222', 'CCC333'],
             'mean': [np.mean(rs) for rs in [rate_of_return_1, rate_of_return_2, rate_of_return_3]],
             'std': [np.std(rs, ddof=0) for rs in [rate_of_return_1, rate_of_return_2, rate_of_return_3]]}
        ).set_index('fund_code')

        assert_frame_equal(actual, expected)

    # ファンド重み
    WEIGHTS = np.array([0.5, 0.3, 0.2])

    @mock.patch('numpy.random.rand', return_value=WEIGHTS * 1.2)
    def test_calc_random_weight_portfolios(self, m):
        # -- setup --
        # 3つのファンドそれぞれの4つの期間の利益率がある想定
        rate_of_returns = np.array([[-0.003573, -0.005040, 0.000682, 0.000292],
                                    [0.004866, 0.000628, 0.006542, -0.003740],
                                    [0.003941, 0.002921, -0.001456, -0.001550]])

        num_iter = 1
        mean = np.mean(rate_of_returns, axis=1)     # ファンドごとの平均
        cov = np.cov(rate_of_returns, ddof=0)       # ファンド間の共分散

        # -- exercise --
        actual = analysis.calc_random_weight_portfolios(num_iter, mean, cov)

        # -- verify --
        # ファンドごとの重みから収益率系列を作成、平均と標準偏差を計算する
        weighted_rate_of_returns = rate_of_returns.transpose() * self.WEIGHTS
        summed_rate_of_returns = weighted_rate_of_returns.sum(axis=1)
        expected_mean = np.mean(summed_rate_of_returns)
        expected_std = np.std(summed_rate_of_returns, ddof=0)
        expected = np.array([[expected_mean], [expected_std]])

        np.testing.assert_almost_equal(actual, expected, decimal=7)
