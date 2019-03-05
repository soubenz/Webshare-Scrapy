
import logging
from scrapy import signals
# from itertools import cycle\
from w3lib.http import basic_auth_header

logger = logging.getLogger(__name__)


class WebshareMiddleware(object):
    url = "http://p.webshare.io:80"
    download_timeout = 180
    # enabled = True
    # connection_refused_delay = 90
    # preserve_delay = False
    # header_prefix = 'WEB'
    # prxr_countries = ['FR', 'DE', 'UA','IN','AL','BD',
    countries = ['RU', 'US', 'UA', 'NL', 'FR', 'DE', 'PL', 'GB', 'CN',
                                  'CZ', 'EE', 'LV', 'ES', 'JP', 'TR', 'PT',
                                  'AM', 'IR', 'EG', 'PK', 'MD', 'IT', 'BD'
                                  'FI', 'GR', 'SE', 'GE', 'KZ', 'VN', 'ZA',
                                  'BG', 'NG', 'QA', 'HK', 'IS', 'ID', 'KR',
                                  'MA', 'SA', 'BY', 'UZ', 'TH', 'CY', 'SG',
                                  'IN', 'IL', 'FR', 'DE', 'UA', 'IN', 'AL']
    #                     'BG','CA','CZ','US','GB','HU','ID','NL','RU','ES']
    # prxr_countries = ['RU']
    # r_header = 
    _settings = [
        # ('r_header', bool),
        # ('user', str),
        ('country', str),
        ('user', str),
        ('password', str),
        # ('url', str),
        ('download_timeout', int),
        # ('preserve_delay', bool),
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
        # self.pool = cycle(self.prxr_countries)

    def is_enabled(self, spider):
        """Hook to enable middleware by custom rules."""
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
        # print(self.url)
        if self._is_enabled_for_request(request):
            request.meta['proxy'] = self.url
            request.meta['download_timeout'] = self.download_timeout
            request.headers['Proxy-Authorization'] = self._proxy_auth
            self.crawler.stats.inc_value('webshare/request_count')
            self.crawler.stats.inc_value('webshare/request/method/%s'
                                                               %  request.method)
        # else:            
        #      request.meta['proxy'] = "dddddddd"                                      
    def process_response(self, request, response, spider):
        return response

    def _is_enabled_for_request(self, request):
        return self.enabled
        # return True

    def _create_proxy_auth(self):
        if self.user and self.password:
            if self.country in self.countries:
                user_rotate = '{}-{}-rotate'.format(self.user, self.country)
                return basic_auth_header(user_rotate, self.password)
            else:
                user_rotate = '{}-rotate'.format(self.user)
                return basic_auth_header(user_rotate, self.password)
        # else:
        #     return basic_auth_header('user', '')
            
