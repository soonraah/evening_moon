import mock
import unittest
import json
import datetime
from evmoon import data


def mock_http_request_value(filename):
    f = data.ROOT_DIR + '/tests/resources/' + filename
    return json.load(open(f, 'r'))


class TestDataPy(unittest.TestCase):

    @mock.patch('evmoon.data._http_request',
                return_value=mock_http_request_value('content-get_fund_list.json'))
    def test_get_fund_list_ideco(self, m):
        got = data.get_fund_list(data.FundSource.IDECO)
        self.assertEqual(m.call_count, 1)
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

    @mock.patch('evmoon.data._http_request',
                side_effect=[mock_http_request_value('content-get_investment_trust_fund_list-0.json'),
                             mock_http_request_value('content-get_investment_trust_fund_list-1.json'),
                             mock_http_request_value('content-get_investment_trust_fund_list-2.json')],
                autospec=True)
    def test_get_fund_list_investment_trust(self, m):
        got = data.get_fund_list(data.FundSource.INVESTMENT_TRUST)
        self.assertEqual(m.call_count, 3)
        self.assertEqual(len(got), 300)
        self.assertEqual(got[0]['fundCode'], '2931113C')
        self.assertEqual(got[-1]['fundCode'], '7931306C')

    def test_get_fund_list_invalid_fund_source(self):
        invalid_segment_source = 100
        with self.assertRaises(RuntimeError):
            data.get_fund_list(invalid_segment_source)

    @mock.patch('evmoon.data._http_request',
                return_value=mock_http_request_value('content-get_reference_price.csv'))
    def test_get_reference_price(self, m):
        got = data.get_reference_price('12345678',
                                       datetime.date(2017, 11, 26),
                                       datetime.date(2017, 12, 26))
        self.assertEqual(len(got), 22)  # 営業日数分のレコードが返る
        self.assertDictEqual(got[0], {
            'date': datetime.datetime(2017, 12, 26, 0, 0),
            'reference_price': 11514.0,
            'diff_prev_day': -31.0,
            'total_net_asset': 292000000.0
        })


    def test__build_post_data(self):
        from_ = datetime.date(2017, 12, 1)
        to = datetime.date(2018, 2, 1)
        got = data._build_post_data(from_, to)
        self.assertEqual(got, b'in_term_from_yyyy=2017&in_term_from_mm=12&in_term_from_dd=01&in_term_to_yyyy=2018&in_term_to_mm=02&in_term_to_dd=01&dispRows=7300&page=0')


if __name__ == '__main__':
    unittest.main()
