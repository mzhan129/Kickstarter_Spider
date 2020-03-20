import scrapy,json,time
import urllib
from scrapy.selector import Selector
from scrapy.exceptions import CloseSpider
from selenium import webdriver
from ScrapyKickstarter.items import ProjectInfo
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options


class KickstarterSpider(scrapy.Spider):
    name = "kickstarter_comments"
    allowed_domains = ["kickstarter.com"]

    def formatStr(self, input):
        return str(input.encode('utf-8')).strip()

    def formatNum(self, input):
        return str(input).strip()

    def formatList(self, input):
        return map(str.strip, [x.encode('ascii', 'ignore').decode('ISO-8859-1').encode('utf-8') for x in input])

    def percentage(part, whole):
        return 100 * float(part) / float(whole)

    def start_requests(self):
        list = []
        # import pandas as pd
        # df = pd.read_excel('excel_projectLinks.xls',sheet_name='matched')
        # list=df['Project_name'].tolist()

        # projects_res = open("urls_0726_1101.json", 'r')
        projects_res = open("ScrapyKickstarter/urls_0726_1101.json", 'r')
        projs = json.load(projects_res)
        for key in projs.keys():
            list.append(projs[key])

        for url in list:
            if url != "":
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        projectInfo = ProjectInfo()
        sel = Selector(response)
        projectInfo['ProjectLink'] = response.url
        print(projectInfo['ProjectLink'])

        # Project Champaign
        ti = len(sel.xpath('*//div[@class="template asset"]/figure/img'))
        images = sel.xpath('*//div[@class="template asset"]/figure/img/@src').extract()

        # Format champaign text
        tmp = self.formatList(sel.xpath(
            '*//div[@class="full-description js-full-description responsive-media formatted-lists"]//text()').extract())
        des = [x for x in tmp if len(x) != 0]

        # Project timeline
        projectInfo['ImageCaption'] = des
        projectInfo['TotalImage'] = ti
        projectInfo['Images'] = images
        projectInfo['totalComments'] = sel.xpath('//span[@class="count"]/data/@data-value').extract()[0]

        project_url_update = response.url + '/comments'

        request = scrapy.Request(project_url_update, callback=self.parse_project_comments)
        request.meta["projectInfo"] = projectInfo
        #print(request)
        return request


    def parse_project_comments(self, response):
        projectInfo = response.meta['projectInfo']
        cap = DesiredCapabilities().FIREFOX
        cap["marionette"] = True
        binary = r"/usr/bin/firefox"
        options = Options()
        options.headless = True
        options.set_headless(headless=True)
        options.binary = binary
        url=r"/home/manlin/geckodriver"
        driver = webdriver.Firefox(firefox_options=options, capabilities=cap,executable_path=url)
        # driver = webdriver.Firefox(executable_path=url)
        driver.get(response.request.url)
        wait = WebDriverWait(driver, 5)
        click_more = True
        count = 0
        cancelCount = 0
        comments = []
        items = []

        try:
            # load comments section
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]'))
            )
            # automate click operations to load all comments
            while click_more and len(items) < 100:
                time.sleep(0.3)
                loadmore = driver.find_element_by_id('react-project-comments').find_elements(By.XPATH,
                                                                                                 "//button[contains(@class,'bttn')]")
                items = driver.find_elements(By.XPATH,
                                                 '*//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]//div[@class="flex mb3"]')

                commentsItems = driver.find_elements(By.XPATH,
                                             '*//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]//div[@class="flex"]')

                cancelItems = driver.find_elements(By.XPATH,
                                                 '*//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]//a[@class="bold soft-black"]')

                if loadmore:
                    loadmore[0].click()
                else:
                    click_more = False
                    time.sleep(0.5)

            # differentiate comments and count the results
            for item in items:
                time.sleep(0.1)
                text = self.formatStr(item.text)
                if "Creator" in text or "Collaborator" in text:
                    count += 1

            for comment in commentsItems:
                time.sleep(0.1)
                text = self.formatStr(comment.text)
                comments.append(text)

            cancelCount += len(cancelItems)

        except Exception:
            projectInfo['totalVCommentsSample'] = "no comments"
            projectInfo['totalVCommentsPercent'] = "no percent"
            projectInfo['Comments'] = "no comments"
            projectInfo['totalCancel'] = "no cancel"
            return projectInfo

        else:
            projectInfo['totalVCommentsSample'] = len(items) - count
            if len(items) == 0:
                projectInfo['totalVCommentsPercent'] = 0
            else:
                projectInfo['totalVCommentsPercent'] = 100 * float(projectInfo['totalVCommentsSample']) / float(len(items))

            projectInfo['Comments'] = comments
            projectInfo['totalCancel'] = cancelCount

            return projectInfo

        finally:
            driver.quit()

def main():
    KickstarterSpiderObject=KickstarterSpider()
    a=[p for p in KickstarterSpiderObject.start_requests()]
    print(a)
    print("yes")
    
if __name__== "__main__":
    main()