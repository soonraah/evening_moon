import os
import re
import json
import datetime
from enum import Enum
import logging
import time
import urllib.request
import urllib.parse
from functools import lru_cache


ROOT_DIR = os.path.abspath(__file__ + '/../../')

REQUEST_INTERVAL_SEC = 2
MAX_PAGE_SIZE = 100


class FundSource(Enum):
    IDECO = 1               # iDeCo: https://site0.sbisec.co.jp/marble/insurance/dc401k/search/dc401ksearch.do?
    INVESTMENT_TRUST = 2    # 投資信託: https://site0.sbisec.co.jp/marble/fund/powersearch/fundpsearch.do?


def get_fund_list(fund_source: FundSource) -> [dict]:
    total_page = MAX_PAGE_SIZE
    page_no = 0
    results = []

    if fund_source == FundSource.IDECO:
        url = 'https://site0.sbisec.co.jp/marble/insurance/dc401k/search/dc401ksearch/search.do?pageNo={' \
              'page_no}&pageRows=100'
    elif fund_source == FundSource.INVESTMENT_TRUST:
        url = 'https://site0.sbisec.co.jp/marble/fund/powersearch/fundpsearch/search.do?pageNo={' \
              'page_no}&fundName=&pageRows=100&tabName=base&sortColumn=090&sortOrder=1&unyouColumnName' \
              '=totalReturnColumns&hitLimit=0&searchWordsMode=1&commission=X&trustCharge=X&yield=X&sharpRatio=X&sigma' \
              '=X&flow=X&asset=X&standardPrice=X&redemption=X&period=X&company=--&budget=1'
    else:
        raise RuntimeError('Unsupported fund source ({}) is given.'.format(fund_source))

    while page_no <= min(total_page, MAX_PAGE_SIZE):
        cur_url = url.format(page_no=page_no)
        (_, _, body) = _http_request(cur_url)
        loaded_body = json.loads(body)
        results.extend(loaded_body['records'])

        total_page = loaded_body['pager']['totalPage']  # 総ページ数ではなく最後のページ番号 (0 start) が入る
        page_no += 1

        time.sleep(REQUEST_INTERVAL_SEC)
        logging.info("Got fund page {}/{}".format(page_no, total_page + 1))

    return results


@lru_cache(maxsize=32)
def get_reference_price(fund_code: str, start_period=None, end_period=None) -> [dict]:
    postdata = None
    if start_period and end_period:
        postdata = _build_post_data(start_period, end_period)
    elif start_period or end_period:
        raise NotImplementedError("now we need to specifiy both. start_period:{}, end_period:{}".format(start_period, end_period))

    url = 'https://site0.sbisec.co.jp' \
          '/marble/fund/history/standardprice/standardPriceHistoryCsvAction.do' \
          '?fund_sec_code={fundCode}'
    (_, _, body) = _http_request(
        url.format(fundCode=fund_code),
        data=postdata,
        decode='sjis'  # csvがsjisで返される
    )

    ret = []
    for line in body.split("\n"):
        row = line.replace('"', '').split(',')
        if len(row) is 4 and re.match(r'\d{4}/\d{2}/\d{2}', row[0]):
            ret.append(dict(
                date=datetime.datetime.strptime(row[0], '%Y/%m/%d'),
                reference_price=float(row[1]),
                diff_prev_day=float(row[2]),
                total_net_asset=float(row[3]) * 100 * 10000  # 単位百万円で入ってくる
            ))
    return ret


def _http_request(url: str, **kw) -> (str, dict, str):
    decode = kw.pop('decode', 'utf8')
    if 'data' in kw and kw['data'] is None:
        del kw['data']

    def r():
        req = urllib.request.Request(url, **kw)
        res = urllib.request.urlopen(req)
        return (
            res.status,
            dict(res.getheaders()),
            res.read().decode(decode)
        )

    # 開発用: 環境変数にDEBUGを入れておくとレスポンスをキャッシュする
    if os.getenv('DEBUG'):
        filename = '{}/evmoon/debug/{}'.format(ROOT_DIR, _normalize_ascii(url))
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump(r(), f, indent=2)
        return json.load(open(filename, 'r'))
    else:
        return r()


def _build_post_data(start_period: datetime.date,
                     end_period: datetime.date) -> dict:
    """see: https://github.com/soonraah/evening_moon/issues/3#issuecomment-354466415"""
    (from_yyyy, from_mm, from_dd) = datetime.date.strftime(start_period, "%Y-%m-%d").split('-')
    (to_yyyy, to_mm, to_dd) = datetime.date.strftime(end_period, "%Y-%m-%d").split('-')
    dict_ = dict(
        in_term_from_yyyy=from_yyyy,
        in_term_from_mm=from_mm,
        in_term_from_dd=from_dd,
        in_term_to_yyyy=to_yyyy,
        in_term_to_mm=to_mm,
        in_term_to_dd=to_dd,
        dispRows=365*20,
        page=0
    )
    return urllib.parse.urlencode(dict_).encode('utf8')


def _normalize_ascii(s: str) -> str:
    _ = s.strip().replace(' ', '-')
    _ = re.sub(r'^https?://', '', _)
    _ = re.sub(r'[^A-Za-z0-9./_-]', '', _)
    _ = re.sub(r'--*', '-', _)
    _ = _.replace('/', '--')
    return _.lower()


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        print(get_ideco_fund_list(),
              get_reference_price(
                  '64311081',
                  datetime.date(2015, 12, 1),
                  datetime.date(2018, 2, 1)))
    elif sys.argv[1] == 'clear-debug':
        import glob
        for filename in glob.glob(ROOT_DIR + '/evmoon/debug/site*'):
            os.remove(filename)
