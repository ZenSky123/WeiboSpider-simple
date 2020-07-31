"""
把非重要信息过滤掉了
"""
import re
from scrapy import Selector, Spider
from scrapy.http import Request
import time
from items import UserItem
import pymongo

client = pymongo.MongoClient(host="localhost", port=27017)
db = client.weibo


def get_all_user_ids():
    collection = db.Tweets
    user_ids = set()
    for i, doc in enumerate(collection.find()):
        user_id = doc['user_id']
        user_ids.add(user_id)

    return user_ids


def get_visited_user_ids():
    collection = db.Users
    user_ids = set()
    for i, doc in enumerate(collection.find()):
        user_id = doc['_id']
        user_ids.add(user_id)

    return user_ids


class UserSimpleSpider(Spider):
    name = "user_spider"
    base_url = "https://weibo.cn"

    def start_requests(self):
        all_user_ids = get_all_user_ids()
        visited_user_ids = get_visited_user_ids()

        urls = [f'{self.base_url}/{user_id}/info' for user_id in all_user_ids if user_id not in visited_user_ids]

        for url in urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        user_item = UserItem()
        user_item['crawl_time'] = int(time.time())
        selector = Selector(response)
        user_item['_id'] = re.findall('(\d+)/info', response.url)[0]
        user_info_text = ";".join(selector.xpath('body/div[@class="c"]//text()').extract())
        nick_name = re.findall('昵称;?:?(.*?);', user_info_text)
        gender = re.findall('性别;?:?(.*?);', user_info_text)
        brief_introduction = re.findall('简介;?:?(.*?);', user_info_text)
        authentication = re.findall('认证;?:?(.*?);', user_info_text)
        if nick_name and nick_name[0]:
            user_item["nick_name"] = nick_name[0].replace(u"\xa0", "")
        if gender and gender[0]:
            user_item["gender"] = gender[0].replace(u"\xa0", "")
        if brief_introduction and brief_introduction[0]:
            user_item["brief_introduction"] = brief_introduction[0].replace(u"\xa0", "")
        if authentication and authentication[0]:
            user_item["authentication"] = authentication[0].replace(u"\xa0", "")
        request_meta = response.meta
        request_meta['item'] = user_item
        yield Request(self.base_url + '/u/{}'.format(user_item['_id']),
                      callback=self.parse_further_information,
                      meta=request_meta, dont_filter=True, priority=1)

    def parse_further_information(self, response):
        text = response.text
        user_item = response.meta['item']
        tweets_num = re.findall('微博\[(\d+)\]', text)
        if tweets_num:
            user_item['tweets_num'] = int(tweets_num[0])
        follows_num = re.findall('关注\[(\d+)\]', text)
        if follows_num:
            user_item['follows_num'] = int(follows_num[0])
        fans_num = re.findall('粉丝\[(\d+)\]', text)
        if fans_num:
            user_item['fans_num'] = int(fans_num[0])
        yield user_item
