# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#
#
# class KickstarterCreatorPipeline(object):
#     def process_item(self, item, spider):
#         return item

# -*- coding: utf-8 -*-
import json
from Kickstarter_Creator.utils import FilepathLoader
from scrapy.exceptions import DropItem

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html



class KickstarterCreatorPipeline(object):

    idx = 0

    def open_spider(self, spider):
        self.file = open(FilepathLoader().get_creator_info_path(), 'w')
        self.file.write("[\n")

    def close_spider(self, spider):
        self.file.write("]\n")
        self.file.close()

    def process_item(self, item, spider):
        if self.idx != 0:
            self.file.write(",\n")
        line = json.dumps(dict(item))
        self.file.write(line)
        self.idx += 1
        return item

