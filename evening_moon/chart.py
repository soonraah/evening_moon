import datetime

import matplotlib.pyplot as plt
import numpy as np

from .analysis import get_price_data_frame, calc_rate_of_return, calc_random_weight_portfolios


def show_price_chart(fund_codes: list,
                     start_period: datetime.date = None,
                     end_period: datetime.date = None) -> None:
    df_price = get_price_data_frame(fund_codes, start_period, end_period)
    ax = df_price.plot(title='Reference Price of Funds', grid=True)
    ax.set_xlabel('Date')
    ax.set_ylabel('Reference Price [yen]')


def show_rate_of_return_chart(fund_codes: list,
                              start_period: datetime.date = None,
                              end_period: datetime.date = None,
                              investment_period_days: int = 5) -> None:
    df_return = calc_rate_of_return(fund_codes, start_period, end_period, investment_period_days)
    ax = df_return.plot(title='Rate of Return of Funds', grid=True)
    ax.set_xlabel("Date")
    ax.set_ylabel("Rate of Return")


def show_mean_std_diagram(fund_codes: list,
                          start_period: datetime.date = None,
                          end_period: datetime.date = None,
                          investment_period_days: int = 5,
                          num_random_feasible_set: int = 0) -> None:
    df_return = calc_rate_of_return(fund_codes, start_period, end_period, investment_period_days)
    matrix = df_return.as_matrix()

    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0, ddof=0)

    fig = plt.figure()
    ax = fig.add_subplot(111)

    plt.grid()

    # ランダムな実現可能集合の要素数が正の場合はそれらもポートフォリオとして表示する
    if num_random_feasible_set > 0:
        cov = np.cov(matrix, rowvar=False, ddof=0)
        portfolio_mean_std_weight = calc_random_weight_portfolios(num_random_feasible_set, mean, cov)
        ax.scatter(x=portfolio_mean_std_weight[1], y=portfolio_mean_std_weight[0], c='lightskyblue', s=5, marker='o',
                   label='random feasible set')

    ax.scatter(x=std, y=mean, c='navy', s=16, marker='x', label='fund')
    ax.legend()

    plt.xlabel('std')
    plt.ylabel('mean')
    plt.title('Mean-Standard Deviation Diagram')
    plt.show()
