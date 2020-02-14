import scrapy, json, time
import re as regex
import datetime as dt
import logging
from scrapy.utils.log import configure_logging
from scrapy.selector import Selector
from Kickstarter_Creator.items import KickstarterCreatorItem
from Kickstarter_Creator.utils import *

creatorName = []

class scrapy_creator(scrapy.Spider):
    name = "scrapy_creator"
    # allowed_domains = ["kickstarter.com"]

    configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename=dt.datetime.now().strftime("%Y-%m-%d") + ".log",
        filemode='w',
        format='%(levelname)s: %(message)s',
        level=logging.DEBUG
    )

    def __init__(self, **kwargs):
        super(scrapy_creator, self).__init__(**kwargs)
        self.popularity = 0
        self.page_number = 1
        self.url_dict = {}
        self.cancel_projects = []
        self.path_loader = FilepathLoader()

    def new_creator(self, rawProjectJson):
        creatorInfo = KickstarterCreatorItem()
        creatorInfo["Creator"] = rawProjectJson['creator']['name']
        creatorInfo['MaxPledged'] = rawProjectJson['pledged']
        return creatorInfo

    def start_requests(self):

        # creator_processed = open("/home/manlin/PycharmProjects/Kickstarter_Creator/creatorInfo_temp.json", 'r')
        # creators = json.load(creator_processed)
        # for creator in creators:
        #     creatorName.append(creator['Creator'])
        # logging.info(creatorName)

        with open(self.path_loader.get_urls_file_path(), 'r') as json_file:
            data = dict(json.load(json_file))
            for url in data.values():
                yield scrapy.Request(url, callback=self.parse)

    def parse(self,response):

        logging.info('Parse function called on %s', response.url)

        projectText = response.selector.xpath(SCRIPT_PROJECT_XPATH).get().replace("\\\\&quot;", '\\"').replace("&quot;",
                                                                                                            "\"")
        projectJsonStr = regex.search("(window\.current_project = \")(.*)\"", projectText).group(2)
        rawProjectJson = json.loads(projectJsonStr)

        if rawProjectJson['creator']['name'] not in creatorName:
            creatorName.append(rawProjectJson['creator']['name'])
            creatorInfo = self.new_creator(rawProjectJson)
            response.meta['creatorInfo'] = creatorInfo
            request = scrapy.Request(url=rawProjectJson['creator']['urls']['api']['user'],
                                     callback=self.parse_creator_profile)
            # logging.info(rawProjectJson['creator']['urls']['api']['user'])
            request.meta['creatorInfo'] = creatorInfo
            # logging.info(request.meta['creatorInfo'])
            return request
        else:
            logging.info("DUPLICATE CREATOR")

    def parse_creator_profile(self, response):
        creatorInfo = response.meta['creatorInfo']
        creatorProfile = json.loads(response.text)

        creatorInfo['CreatorId'] = creatorProfile['id']
        creatorInfo['BackedProjectsCount'] = creatorProfile['backed_projects_count']
        creatorInfo['CreatedProjectsCount'] = creatorProfile['created_projects_count']
        creatorInfo['ProfileLink'] = creatorProfile['urls']['web']['user']
        creatorInfo['SucceedProjectsCount'] = 0

        URL = creatorInfo['ProfileLink'] + '/created'
        request = scrapy.Request(url=URL, callback=self.parse_creator_link)
        request.meta['creatorInfo'] = creatorInfo

        return request

    def parse_creator_link(self, response):
        creatorInfo = response.meta['creatorInfo']

        logging.info('Parse creator called on %s', response.url)
        # projectsLink = []
        sel = Selector(response)
        base = '//div[@id="react-profile-created"]/'
        projectsStr = sel.xpath(base + '@data-projects').extract()
        projects= json.loads(projectsStr[0])
        for project in projects:
            creatorInfo['MaxPledged'] = max(project['pledged'], creatorInfo['MaxPledged'])
            if project['pledged'] > project['goal']:
                creatorInfo['SucceedProjectsCount'] = creatorInfo['SucceedProjectsCount'] + 1
            # logging.info(project)

        next_base = '//a[@class="next_page"]/'
        page_url = sel.xpath(next_base + '@href').extract()
        # logging.info(len(page_url))
        if len(page_url) > 0:
            URL = 'https://www.kickstarter.com/' + page_url[0]
            request = scrapy.Request(url=URL, callback=self.parse_creator_link)
            request.meta['creatorInfo'] = creatorInfo
            return request
        else:
            return creatorInfo

