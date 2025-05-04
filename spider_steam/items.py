# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SpiderSteamItem(scrapy.Item):
    name = scrapy.Field()
    category = scrapy.Field()
    reviews_numbers = scrapy.Field()
    rate = scrapy.Field()
    date = scrapy.Field()
    developer = scrapy.Field()
    tags = scrapy.Field()
    price = scrapy.Field()
    platforms = scrapy.Field()
    pass
