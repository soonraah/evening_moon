import mock
import unittest
import json
import datetime
from evening_moon import data


def mock_http_request_value(filename):
    f = data.ROOT_DIR + '/tests/resources/' + filename
    return json.load(open(f, 'r'))

# /Users/sakamotoakira/repos/evening_moon/tests/resources/content-get_fund_list.json
# /Users/sakamotoakira/repos/evening_moon/evening_moon/tests/resources/content-get_fund_list.json

class TestDataPy(unittest.TestCase):

    @mock.patch('evening_moon.data._http_request',
                return_value=mock_http_request_value('content-get_fund_list.json'))
    def test_get_fund_list(self, m):
        got = data.get_fund_list()
        self.assertEqual(len(got), 63)
        self.assertDictEqual(got[0], json.loads("""
            {
              "FDDividendsSchedule": "年1回",
              "FDPolicy": "国内外の上場株式を主要な投資対象とし、市場価値が割安と考えられる銘柄を選別して長期的に投資します。銘柄選別にあたっては徹底的な調査・分析を行い、業種や企業規模にとらわれることなく、長期的な将来価値に対してその時点での市場価値が割安と考えられる銘柄に長期的に選別投資します。市場の状況に応じて株式の組入比率を変化させることも特徴です。",
              "FDReservedAssetNum": 0,
              "FDReservedAssetNumFlg": "0",
              "FDTrustChargeNum": 0.8208,
              "FDTrustChargeNumComment": null,
              "FDTrustChargeNumFlg": "0",
              "MFFundAisyo": null,
              "MFName": "レオス－ひふみ年金",
              "baseFundType": "",
              "budget": "NON_SELECT",
              "commissionAll": null,
              "commissionKingak": null,
              "commissionKuchisu": null,
              "commissionNisa": null,
              "comparable": true,
              "dividendsYieldDisp": null,
              "fphAsset": 9108,
              "fphComp": -3,
              "fphPrice": 15457,
              "fundCode": "9C31116A",
              "fundDividend": 0,
              "kingakuCommission1": null,
              "kingakuCommission2": null,
              "kingakuCommission3": null,
              "kingakuCommission4": null,
              "kingakuCommission5": null,
              "kutiCommission1": null,
              "kutiCommission2": null,
              "kutiCommission3": null,
              "kutiCommission4": null,
              "kutiCommission5": null,
              "lr1year": 45.42,
              "lr3years": null,
              "lr6months": 20.83,
              "msCategoryName": "国内株式",
              "msRatingAllName": null,
              "nextAccountingDate": "",
              "nisaCommission": null,
              "nisaFlg": "",
              "regionName": "グローバル",
              "riskMajor3years": null,
              "salseAmountArrowKbn": "3",
              "salseAmountRankDisp": 1,
              "sbiRecommendedFlg": "",
              "sdSigma1year": 5.69,
              "searchCommission1": null,
              "searchCommission2": null,
              "searchCommission3": null,
              "searchCommission4": null,
              "searchCommission5": null,
              "sharpRatio1year": 7.61,
              "totalreturn1year": 43.34,
              "totalreturn3years": null,
              "totalreturn6months": 19.14,
              "tumitateButtonKbn": "",
              "yearDividends": 0
            }
            """))

    @mock.patch('evening_moon.data._http_request',
                return_value=mock_http_request_value('content-get_reference_price.csv'))
    def test_get_reference_price(self, m):
        got = data.get_reference_price('12345678')
        self.assertEqual(len(got), 22)  # 営業日数分のレコードが返る
        self.assertDictEqual(got[0], {
            'date': datetime.datetime(2017, 12, 26, 0, 0),
            'reference_price': 11514.0,
            'diff_prev_day': -31.0,
            'total_net_asset': 292000000.0
        })


if __name__ == '__main__':
    unittest.main()
