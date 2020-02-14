# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class KickstarterCreatorItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    Creator = scrapy.Field()
    ProfileLink = scrapy.Field()
    CreatorId = scrapy.Field()
    CreatedProjectsCount = scrapy.Field()
    SucceedProjectsCount = scrapy.Field()
    BackedProjectsCount = scrapy.Field()
    MaxPledged = scrapy.Field()


    pass
