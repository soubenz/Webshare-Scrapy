import pytest
from w3lib.http import basic_auth_header
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy.utils.test import get_crawler
from scrapy_webshare.middleware import WebshareMiddleware


def _assert_disabled(mock_crawler, spider, settings=None):
    crawler = get_crawler(spider, settings)
    crawler.engine = mock_crawler
    mw = WebshareMiddleware.from_crawler(crawler)
    mw.open_spider(spider)
    req = Request('http://www.scrapytest.org')
    out = mw.process_request(req, spider)
    assert out is None
    assert req.meta.get('proxy') is None
    assert req.meta.get('download_timeout') is None
    assert req.headers.get('Proxy-Authorization') is None
    res = Response(req.url)
    assert mw.process_response(req, res, spider) is res


def test_disabled_by_lack_of_webshare_settings(_mock_crawler):
    _assert_disabled(_mock_crawler[0], _mock_crawler[1], settings={})


def _assert_enabled(mock_crawler, spider, settings=None, authentification=None,
                    download_timeout=180):
    crawler = get_crawler(spider, settings)
    crawler.engine = mock_crawler
    mw = WebshareMiddleware.from_crawler(crawler)
    mw.open_spider(spider)
    req = Request('http://www.scrapytest.org')
    out = mw.process_request(req, spider)
    assert out is None
    proxy_url = 'http://p.webshare.io:80'
    assert req.meta.get('proxy') == proxy_url
    assert req.meta.get('download_timeout') == download_timeout
    assert req.headers.get('Proxy-Authorization') == authentification
    res = Response(req.url)
    assert mw.process_response(req, res, spider) is res


def test_spider_webshare_enabled(_mock_crawler):
    spider = _mock_crawler[1]
    mock_crawler = _mock_crawler[0]
    _assert_disabled(mock_crawler, spider)
    assert hasattr(spider, 'webshare_enabled') is False
    spider.webshare_enabled = True
    _assert_enabled(mock_crawler, spider)
    spider.webshare_enabled = False
    _assert_disabled(mock_crawler, spider)


def test_download_timeout(_mock_crawler, download_timeout):
    spider = _mock_crawler[1]
    mock_crawler = _mock_crawler[0]
    settings = {}
    spider.webshare_enabled = True
    settings['WEBSHARE_DOWNLOAD_TIMEOUT'] = download_timeout
    _assert_enabled(mock_crawler, spider, settings=settings,
                    download_timeout=download_timeout)


def test_auth(_mock_crawler, _authentification):
    spider = _mock_crawler[1]
    mock_crawler = _mock_crawler[0]
    spider.webshare_enabled = True
    settings = {}
    settings['WEBSHARE_USER'] = 'user'
    settings['WEBSHARE_PASSWORD'] = 'pass'
    _assert_enabled(mock_crawler, spider, settings, _authentification)


def test_country_valid(_mock_crawler, _authentification_country):
    spider = _mock_crawler[1]
    mock_crawler = _mock_crawler[0]
    spider.webshare_enabled = True
    settings = {}
    settings['WEBSHARE_USER'] = 'user'
    settings['WEBSHARE_PASSWORD'] = 'pass'
    settings['WEBSHARE_COUNTRY'] = _authentification_country[1]
    _assert_enabled(mock_crawler, spider, settings, _authentification_country[0])


def test_country_invalid(_mock_crawler, _authentification_country_invalid):
    spider = _mock_crawler[1]
    mock_crawler = _mock_crawler[0]
    spider.webshare_enabled = True
    settings = {}
    settings['WEBSHARE_USER'] = 'user'
    settings['WEBSHARE_PASSWORD'] = 'pass'
    settings['WEBSHARE_COUNTRY'] = _authentification_country_invalid[1]
    _assert_enabled(mock_crawler, spider, settings, _authentification_country_invalid[0])


@pytest.fixture(params=[60, 90, 120])
def download_timeout(request):
    return request.param


@pytest.fixture(params=['US', 'FR'])
def country(request):
    return request.param


def test_enabled(_mock_crawler):
    _assert_disabled(_mock_crawler[0], _mock_crawler[1])
    settings = {}
    settings['WEBSHARE_ENABLED'] = True
    _assert_enabled(_mock_crawler[0], _mock_crawler[1], settings=settings)



@pytest.fixture
def _authentification():
    return basic_auth_header('user-rotate', 'pass')


@pytest.fixture(params=['US', 'FR', 'KR'])
def _authentification_country(request):
    return (basic_auth_header(
                 'user-%s-rotate' % request.param, 'pass'), request.param)


@pytest.fixture(params=['DZ', 'TN'])
def _authentification_country_invalid(request):
    return (basic_auth_header(
                 'user-rotate', 'pass'), request.param)


@pytest.fixture
def _mock_crawler():
    spider = Spider('foo')

    class MockedDownloader(object):
        slots = {}

    class MockedEngine(object):
        downloader = MockedDownloader()

    mock_engine = MockedEngine()

    return mock_engine, spider
