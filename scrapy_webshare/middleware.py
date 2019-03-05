
import logging
from scrapy import signals
from w3lib.http import basic_auth_header

logger = logging.getLogger(__name__)


class WebshareMiddleware(object):
    url = "http://p.webshare.io:80"
    download_timeout = 180
    countries = ['RU', 'US', 'UA', 'NL', 'FR', 'DE', 'PL', 'GB', 'CN', 'CZ',
                       'EE', 'LV', 'ES', 'JP', 'TR', 'PT', 'AM', 'IR', 'EG',
                       'PK', 'MD', 'IT', 'BD', 'FI', 'GR', 'SE', 'GE', 'KZ',
                       'VN', 'ZA', 'BG', 'NG', 'QA', 'HK', 'IS', 'ID', 'KR',
                       'MA', 'SA', 'BY', 'UZ', 'TH', 'CY', 'SG', 'IN', 'IL',
                       'FR', 'DE', 'UA', 'IN', 'AL']
    _settings = [
        ('country', str),
        ('user', str),
        ('password', str),
        ('download_timeout', int),
    ]

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler)
        crawler.signals.connect(o.open_spider, signals.spider_opened)
        return o

    def open_spider(self, spider):
        self.enabled = self.is_enabled(spider)
        if not self.enabled:
            return

        for k, type_ in self._settings:
            setattr(self, k, self._get_setting_value(spider, k, type_))
        logger.info("Using Webshare")

        self._proxy_auth = self._create_proxy_auth()
        logging.info("Using webshare at %s (apikey: %s)" % (
            self.user,
            self.password)
        )

    def is_enabled(self, spider):
        return (
            getattr(spider, 'webshare_enabled', False) or
            self.crawler.settings.getbool("WEBSHARE_ENABLED")
        )

    def _get_setting_value(self, spider, k, type_):
        o = getattr(self, k, None)
        s = self._settings_get(
            type_, 'WEBSHARE_' + k.upper(), o)
        return getattr(
            spider, 'webshare_' + k,  s)

    def _settings_get(self, type_, *a, **kw):
        if type_ is int:
            return self.crawler.settings.getint(*a, **kw)
        elif type_ is bool:
            return self.crawler.settings.getbool(*a, **kw)
        elif type_ is list:
            return self.crawler.settings.getlist(*a, **kw)
        elif type_ is dict:
            return self.crawler.settings.getdict(*a, **kw)
        else:
            return self.crawler.settings.get(*a, **kw)

    def process_request(self, request, spider):
        if self._is_enabled_for_request(request):
            request.meta['proxy'] = self.url
            request.meta['download_timeout'] = self.download_timeout
            request.headers['Proxy-Authorization'] = self._proxy_auth
            self.crawler.stats.inc_value('webshare/request_count')
            self.crawler.stats.inc_value('webshare/request/method/%s' %
                                         request.method)

    def process_response(self, request, response, spider):
        return response

    def _is_enabled_for_request(self, request):
        return self.enabled

    def _create_proxy_auth(self):
        if self.user and self.password:
            if self.country in self.countries:
                user_rotate = '{}-{}-rotate'.format(self.user, self.country)
                return basic_auth_header(user_rotate, self.password)
            else:
                user_rotate = '{}-rotate'.format(self.user)
                return basic_auth_header(user_rotate, self.password)
