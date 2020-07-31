"""
通过用户ID抓取微博，只抓取指定日期
"""
import codecs
import datetime
import re
from lxml import etree
from scrapy import Spider
from scrapy.http import Request
import time
from items import TweetItem
from spiders.utils import time_fix, extract_weibo_content
import os


class UserTweetSpider(Spider):
    name = "user_tweet_spider"
    base_url = "https://weibo.cn"

    date_start = datetime.datetime.strptime("2020-01-01", '%Y-%m-%d')
    date_end = datetime.datetime.strptime("2020-07-20", '%Y-%m-%d')

    def read_user_ids_done(self):
        with codecs.open('data/userid_done.txt', 'r', 'utf-8') as f:
            return [user_id.strip() for user_id in f.read().split('\n') if user_id.strip()]

    def save_user_ids_done(self, ids):
        with codecs.open('data/userid_done.txt', 'w', 'utf-8') as f:
            f.write('\n'.join(ids))

    def start_requests(self):
        def init_url_by_user_id():
            self.user_ids_done = self.read_user_ids_done()

            user_ids = []
            for folder, _, filenames in os.walk('data/userid'):
                for filename in filenames:
                    filepath = "{}/{}".format(folder, filename)
                    with codecs.open(filepath, 'r', 'utf-8') as f:
                        lines = [line.split() for line in f.read().split('\n') if line.strip()]
                        for _, userid in lines:
                            if userid != 'unfound' and userid not in self.user_ids_done:
                                user_ids.append(userid)

            urls = [f'{self.base_url}/{user_id}?page=1' for user_id in user_ids]
            return urls

        urls = init_url_by_user_id()
        for url in urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        page_pattern = re.compile(r'page=(\d+)')
        page = int(page_pattern.search(response.url).group(1))

        userid_pattern = re.compile(r'(\d+)\?page')
        userid = userid_pattern.search(response.url).group(1)

        next_page_url = re.sub(page_pattern, "page={}".format(page + 1), response.url)

        tree_node = etree.HTML(response.body)
        tweet_nodes = tree_node.xpath('//div[@class="c" and @id]')
        for tweet_node in tweet_nodes:
            try:
                tweet_item = TweetItem()

                create_time_info_node = tweet_node.xpath('.//span[@class="ct"]')[-1]
                create_time_info = create_time_info_node.xpath('string(.)')
                if "来自" in create_time_info:
                    tweet_item['created_at'] = time_fix(create_time_info.split('来自')[0].strip())
                    tweet_item['tool'] = create_time_info.split('来自')[1].strip()
                else:
                    tweet_item['created_at'] = time_fix(create_time_info.strip())

                # 如果时间不合法则直接筛除 只取月和日
                date_string = tweet_item['created_at'].split()[0]
                date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
                # 因为微博是默认倒序排列，如果发现第一个小于指定时间的，则视为非法
                if date < self.date_start:
                    self.user_ids_done.append(userid)
                    self.save_user_ids_done(self.user_ids_done)
                    break
                if not self.date_start <= date <= self.date_end:
                    continue

                tweet_item['crawl_time'] = int(time.time())
                tweet_repost_url = tweet_node.xpath('.//a[contains(text(),"转发[")]/@href')[0]
                user_tweet_id = re.search(r'/repost/(.*?)\?uid=(\d+)', tweet_repost_url)
                tweet_item['weibo_url'] = 'https://weibo.com/{}/{}'.format(user_tweet_id.group(2),
                                                                           user_tweet_id.group(1))
                tweet_item['user_id'] = user_tweet_id.group(2)
                tweet_item['_id'] = user_tweet_id.group(1)
                like_num = tweet_node.xpath('.//a[contains(text(),"赞[")]/text()')[-1]
                tweet_item['like_num'] = int(re.search('\d+', like_num).group())

                repost_num = tweet_node.xpath('.//a[contains(text(),"转发[")]/text()')[-1]
                tweet_item['repost_num'] = int(re.search('\d+', repost_num).group())

                comment_num = tweet_node.xpath(
                    './/a[contains(text(),"评论[") and not(contains(text(),"原文"))]/text()')[-1]
                tweet_item['comment_num'] = int(re.search('\d+', comment_num).group())

                images = tweet_node.xpath('.//img[@alt="图片"]/@src')
                if images:
                    tweet_item['image_url'] = images

                videos = tweet_node.xpath('.//a[contains(@href,"https://m.weibo.cn/s/video/show?object_id=")]/@href')
                if videos:
                    tweet_item['video_url'] = videos

                map_node = tweet_node.xpath('.//a[contains(text(),"显示地图")]')
                if map_node:
                    map_node = map_node[0]
                    map_node_url = map_node.xpath('./@href')[0]
                    map_info = re.search(r'xy=(.*?)&', map_node_url).group(1)
                    tweet_item['location_map_info'] = map_info

                repost_node = tweet_node.xpath('.//a[contains(text(),"原文评论[")]/@href')
                if repost_node:
                    tweet_item['origin_weibo'] = repost_node[0]

                all_content_link = tweet_node.xpath('.//a[text()="全文" and contains(@href,"ckAll=1")]')
                if all_content_link:
                    all_content_url = self.base_url + all_content_link[0].xpath('./@href')[0]
                    yield Request(all_content_url, callback=self.parse_all_content, meta={'item': tweet_item},
                                  priority=1)
                else:
                    tweet_html = etree.tostring(tweet_node, encoding='unicode')
                    tweet_item['content'] = extract_weibo_content(tweet_html)
                    yield tweet_item

            except Exception as e:
                self.logger.error(e)
        yield Request(next_page_url, self.parse, dont_filter=True, meta=response.meta)

    def parse_all_content(self, response):
        tree_node = etree.HTML(response.body)
        tweet_item = response.meta['item']
        content_node = tree_node.xpath('//*[@id="M_"]/div[1]')[0]
        tweet_html = etree.tostring(content_node, encoding='unicode')
        tweet_item['content'] = extract_weibo_content(tweet_html)
        yield tweet_item
