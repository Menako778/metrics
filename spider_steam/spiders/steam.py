import scrapy
import re
from ..items import SpiderSteamItem
from urllib.parse import urlencode
from urllib.parse import urlparse


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

        name = response.xpath('//div[@id="appHubAppName" and @class="apphub_AppName"]/text()').extract()
        print(name)
        name = name[0]
        category = response.xpath('//div[@class="blockbg"]/a/text()')[1:].extract()
        reviews_numbers = response.xpath('//meta[@itemprop="reviewCount"]/@content').extract()
        rate = response.xpath('//div[@itemprop="aggregateRating"]//span[@itemprop="description"]/text()').extract()
        date = response.xpath('//div[@class="date"]/text()').extract()
        developer = response.xpath('//div[@id="developers_list"]/a/text()').extract()
        print(developer)
        developers = ''
        for dev in developer:
            developers += dev
            if dev != developer[-1]:
                developers += '/'

        tags = response.xpath('//div[@class="glance_tags popular_tags"]/a/text()').extract()
        print(tags)
        cleaned_tags = ''
        for tag in tags:
            cleaned_tags += re.sub(r'[\n]+', '', re.sub(r'[\t]+', '', tag))
            # проверка на последний элемент
            if tag != tags[-1]:
                cleaned_tags += '/'

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
        items['developer'] = developers
        items['tags'] = re.sub(r'[\n]+', '', re.sub(r'[\t]+', '', cleaned_tags))
        items['price'] = price.strip()
        items['platforms'] = ' '.join(platforms).strip().split()

        items['multiplayer'] = 'Yes' if any(tag in ['Multiplayer', 'Co-op'] for tag in tags) else 'No'

        # Языки
        languages = response.xpath('//table[contains(@class, "game_language_options")]//tr[td[@class="ellipsis"]]/td[@class="ellipsis"]//text()').getall()
        items['languages'] = ', '.join([lang.strip() for lang in languages if lang.strip()]) or 'N/A'

        # Возрастной рейтинг
        age_rating = response.xpath('//div[@class="game_rating_icon"]/a/img/@alt').get()
        items['age_rating'] = age_rating.strip() if age_rating else 'N/A'

        # Размер файла
        storage_div = response.xpath('//div[contains(@class, "game_area_sys_req")]//li[contains(., "Miejsce na dysku:")]')
        items['file_size'] = storage_div.xpath('./text()').re_first(r'(\d+\s?[GM]B)') or 'N/A'

        # Кроссплатформа
        items['cross_platform'] = 'Yes' if 'win' in platforms and ('mac' in platforms or 'linux' in platforms) else 'No'

        app_id = urlparse(response.url).path.split('/')[2]
        steamcharts_url = f'https://steamcharts.com/app/{app_id}'
        print('steamcharts_url:', steamcharts_url)
        
        yield scrapy.Request(
            url=steamcharts_url,
            callback=self.parse_steamcharts,
            meta={'items': items},
            errback=self.handle_error
        )

        # yield items
       
    def parse_steamcharts(self, response):
        items = response.meta['items']
        print('items:', items)
        print(response.xpath('//div[@class="app-stat"][1]//span[@class="num"]/text()').get().strip())
        items['current_players'] = response.xpath('//div[@class="app-stat"][1]//span[@class="num"]/text()').get().strip()
        items['peak_24h'] = response.xpath('//div[@class="app-stat"][2]//span[@class="num"]/text()').get().strip()
        items['peak_all_time'] = response.xpath('//div[@class="app-stat"][3]//span[@class="num"]/text()').get().strip()
        yield items

    def handle_error(self, failure):
        print('Error:', failure)
        items = failure.request.meta['items']
        items['current_players'] = 'N/A'
        items['peak_24h'] = 'N/A'
        items['peak_all_time'] = 'N/A'
        return items