# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ProjectInfo(scrapy.Item):
    # define the fields for your item here like:
    ProjectLink = scrapy.Field()
    totalComments = scrapy.Field()
    totalVCommentsSample = scrapy.Field()
    totalVCommentsPercent = scrapy.Field()
    ImageCaption = scrapy.Field()
    TotalImage = scrapy.Field()
    Images = scrapy.Field()
    Comments = scrapy.Field()
    totalCancel = scrapy.Field()