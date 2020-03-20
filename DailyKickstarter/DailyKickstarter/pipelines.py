# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
import json

class DailykickstarterPipeline(object):
    idx = 0

    def open_spider(self, spider):
        self.file = open('./daily' + str(time.strftime("%Y-%m-%d")) + '.json', 'w')
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
