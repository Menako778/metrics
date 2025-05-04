import scrapy
from ..items import SpiderSteamItem
from urllib.parse import urlencode


steam_tags = [
    "Action",
    "Adventure",
    "RPG",
    "Indie",
    "Casual",
    "Strategy",
    "Simulation",
    "Racing",
    "Sports",
    "Multiplayer",
    "Singleplayer",
    "Co-op",
    "Open World",
    "Sandbox",
    "Horror",
    "Survival",
    "Shooter",
    "First-Person",
    "Third Person",
    "Puzzle",
    "Platformer",
    "Story Rich",
    "Visual Novel",
    "Anime",
    "Pixel Graphics",
    "Retro",
    "Sci-fi",
    "Fantasy",
    "Mystery",
    "Stealth",
    "Comedy",
    "Physics",
    "Crafting",
    "Building",
    "Exploration",
    "Roguelike",
    "Roguelite",
    "Turn-Based",
    "Real-Time",
    "Tactical",
    "Card Game",
    "Fighting",
    "Rhythm",
    "Narration",
    "Hack and Slash",
    "2D",
    "3D",
    "VR",
    "Early Access",
    "Free to Play"
]


class SteamSpider(scrapy.Spider):
    name = "steam"

    def start_requests(self):
        for i in steam_tags:
            for page in range(1, 3):
                url = 'https://store.steampowered.com/search/?' + urlencode({'term': i, 'page': str(page)})
                yield scrapy.Request(url=url, callback=self.parse_keyword_response)

    def parse_keyword_response(self, response):
        for res in response.xpath('//div[@id="search_resultsRows"]/a/@href').extract():
            yield scrapy.Request(url=res, callback=self.parse)

    def parse(self, response):
        items = SpiderSteamItem()

        name = response.xpath('//div[@id="appHubAppName" and @class="apphub_AppName"]/text()').extract()[0]
        category = response.xpath('//div[@class="blockbg"]/a/text()')[1:].extract()
        reviews_numbers = response.xpath('//meta[@itemprop="reviewCount"]/@content').extract()
        rate = response.xpath('//div[@itemprop="aggregateRating"]//span[@itemprop="description"]/text()').extract()
        date = response.xpath('//div[@class="date"]/text()').extract()
        developer = response.xpath('//div[@id="developers_list"]/a/text()').extract()
        tags = response.xpath('//div[@class="glance_tags popular_tags"]/a/text()').extract()
        
        try:
            # Основная цена без скидки
            price = response.xpath('//div[@class="game_purchase_price price"]/text()').get()
            if not price:
                # Цена со скидкой
                price = response.xpath('//div[contains(@class, "discount_final_price")]/text()').get()
            if not price:
                # Бесплатная игра
                price = response.xpath('//div[contains(@class, "game_purchase_price")]/text()').get()
            price = price.strip() if price else 'None'
            if price == 'None':
                free_check = response.xpath('//div[contains(@class, "game_area_purchase_game_free")]')
                if free_check:
                    price = 'Free'
        except (IndexError, AttributeError):
            price = 'None'

        platforms = response.xpath('//div[contains(@class,"game_area_sys_req sysreq_content")]/@data-os').extract()

        items['name'] = ''.join(name).strip()
        items['category'] = '/'.join(category).strip()
        items['reviews_numbers'] = ''.join(reviews_numbers).strip()
        items['rate'] = ''.join(rate).strip()
        items['date'] = ''.join(date).strip()
        items['developer'] = ''.join(developer).strip()
        items['tags'] = ''.join(tags).strip().split()
        items['price'] = price.strip()
        items['platforms'] = ' '.join(platforms).strip().split()

        yield items
