# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ProjectInfo(scrapy.Item):
    # define the fields for your item here like:
    ProjectId = scrapy.Field()
    ProjectTitle = scrapy.Field()
    ProjectDescription = scrapy.Field()
    CreatedBy = scrapy.Field()
    CreatorProfile = scrapy.Field()
    popularity = scrapy.Field()
    ProjectLink = scrapy.Field()
    ProjectTimeLine = scrapy.Field()
    ProjectUpdates = scrapy.Field()
    totalComments = scrapy.Field()
    totalVCommentsSample = scrapy.Field()
    totalVCommentsPercent = scrapy.Field()
    ProjectResults = scrapy.Field()
    ProjectSupports = scrapy.Field()
    ProjectCampaign = scrapy.Field()
    TotalCampaignImage = scrapy.Field()
    CampaignImages = scrapy.Field()
    CampaignVideo = scrapy.Field()
    CampaignVideoLink = scrapy.Field()
