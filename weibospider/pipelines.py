import pymongo
from pymongo.errors import DuplicateKeyError
from settings import MONGO_HOST, MONGO_PORT


class MongoDBPipeline(object):
    def __init__(self):
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        db = client['weibo']
        self.Users = db["Users"]
        self.Tweets = db["Tweets"]
        self.Comments = db["Comments"]
        self.Relationships = db["Relationships"]
        self.UsersTweets = db["UsersTweets"]
        self.NicknameTweets = db["NicknameTweets"]

    def process_item(self, item, spider):
        if spider.name == 'comment_spider':
            self.insert_item(self.Comments, item)
        elif spider.name == 'fan_spider':
            self.insert_item(self.Relationships, item)
        elif spider.name == 'follower_spider':
            self.insert_item(self.Relationships, item)
        elif spider.name == 'user_spider':
            self.insert_item(self.Users, item)
        elif spider.name == 'tweet_spider':
            self.insert_item(self.Tweets, item)
        elif spider.name == 'user_tweet_spider':
            self.insert_item(self.UsersTweets, item)
        elif spider.name == 'nickname_tweet_spider':
            self.insert_item(self.NicknameTweets, item)
        return item

    @staticmethod
    def insert_item(collection, item):
        try:
            collection.insert(dict(item))
        except DuplicateKeyError:
            pass
