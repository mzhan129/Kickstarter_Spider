# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ProjectInfo(scrapy.Item):
    # define the fields for your item here like:
    ProjectTitle = scrapy.Field()
    ProjectId = scrapy.Field()
    ProjectDescription = scrapy.Field()
    CreatedBy = scrapy.Field()
    ProjectLink = scrapy.Field()
    Popularity = scrapy.Field()
    AmountAsked = scrapy.Field()
    AmountPledged = scrapy.Field()
    Current_currency = scrapy.Field()
    TotalBackers = scrapy.Field()
    GoalFinishedPercentage = scrapy.Field()
    TimeToGo = scrapy.Field()
    TotalComments = scrapy.Field()
