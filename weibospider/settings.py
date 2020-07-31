BOT_NAME = 'spider'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

ROBOTSTXT_OBEY = False

# change cookie to yours

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
    'Cookie': '_ga=GA1.2.846900943.1587429258; _T_WM=43691507059; SCF=AlWQFVpBHcsyZrjWFhaeztHQ0lVlVX9ArNeKluGAtp_I3W4TLWeZmLWCzIjUh7B1KBLjmMDqMhD8witriAHVpVM.; SUB=_2A25yGh3CDeRhGeBK6VAU8C7Kzz6IHXVR5KOKrDV6PUJbktAKLUj1kW1NR8DI55KYSW0GUu1rMw-BRY7cn7wQ8Uda; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5BWLFFLMNzsIXye4GK0aXR5JpX5K-hUgL.FoqXeozfeh5cShz2dJLoIEBLxKML12-L12zLxKqL1hzL1-qLxKMLBK.LB.2LxK-L1K-L122t; SUHB=079j5_Vys50OFo; SSOLoginState=1595829650; ALF=1598421650'
}
CONCURRENT_REQUESTS = 16

DOWNLOAD_DELAY = 3

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'middlewares.IPProxyMiddleware': 100,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 101,
}

ITEM_PIPELINES = {
    'pipelines.MongoDBPipeline': 300,
}

MONGO_HOST = '192.168.2.185'
MONGO_PORT = 27017
