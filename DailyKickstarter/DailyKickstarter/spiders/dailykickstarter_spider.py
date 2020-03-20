import scrapy,json
from scrapy.selector import Selector
from scrapy.exceptions import CloseSpider
from DailyKickstarter.items import ProjectInfo
from DailyKickstarter.static import *
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



class DailystarterSpider(scrapy.Spider):
    name = "dailykickstarter"
    allowed_domains = ["kickstarter.com"]
    start_urls = [URL % 1]

    def __init__(self):
        self.popularity = 0
        self.page_number = 0

    def formatStr(self, input):
        return str(input.encode('utf-8')).strip()

    def formatNum(self, input):
        return str(input).strip()

    def formatList(self, input):
        return map(str.strip, [x.encode('ascii', 'ignore').decode('ISO-8859-1').encode('utf-8') for x in input])

    # def spider_closed(self, spider):
    #     mail_from = 'mojiayong7@gmail.com'
    #     mail_to = ['jiayongm@asu.edu']
    #     mail_subject = "%s Daily Kickstarter crawling task is finished" % time.strftime("%Y-%m-%d")
    #     mail_body = "%s task is finished" % time.strftime("%Y-%m-%d")
    #
    #     #TODO dump the report into the mail
    #     mailer = MailSender(mailfrom= mail_from, smtpuser='mojiayong7@gmail.com',
    #                         smtphost='smtp.gmail.com', smtpport=587, smtppass='', smtptls=True)
    #     return mailer.send(to= mail_to, subject=mail_subject, body= mail_body)

    def parse(self, response):
        self.page_number += 1
        print self.page_number
        print "----------"
        sel = Selector(response)
        base = '//div[@id="projects_list"]/div[contains(@class, "grid-row")]/div[contains(@class, "js-react-proj-card")]/'
        project = sel.xpath(base + '@data-project').extract()
        if not project:
            raise CloseSpider('No more pages')

        self.popularity = 0
        for p in project:
            pStr = "{" + str(p.encode('utf-8'))[1: -1] + "}"
            projectJson = json.loads(pStr)

            projectInfo = ProjectInfo()
            projectInfo["ProjectTitle"] = self.formatStr(projectJson['name'])
            projectInfo["ProjectId"] = str(projectJson['id'])
            projectInfo["ProjectDescription"] = self.formatStr(projectJson['blurb'])
            projectInfo["CreatedBy"] = self.formatStr(projectJson['creator']['name'])

            projectInfo["AmountAsked"] = self.formatNum(projectJson['goal'])
            projectInfo["AmountPledged"] = self.formatNum(projectJson['pledged'])
            projectInfo["Current_currency"] = self.formatStr(projectJson['current_currency'])
            projectInfo["TotalBackers"] = self.formatNum(projectJson['backers_count'])
            projectInfo["GoalFinishedPercentage"] = self.formatNum(projectJson['percent_funded'])

            project_url = str(projectJson['urls']['web']['project'].encode('utf-8'))

            projectInfo["ProjectLink"] = project_url

            self.popularity += 1

            request = scrapy.Request(project_url, callback=self.parse_project_detail)
            request.meta["projectInfo"] = projectInfo

            yield request
            curPage = response.request.url[response.request.url.index("page=")+5:]
            projectInfo["Popularity"] = 12*(int(curPage) - 1) + self.popularity

        yield scrapy.Request(URL % self.page_number)


    def parse_project_detail(self, response):
        projectInfo = response.meta['projectInfo']
        sel = Selector(response)
        projectInfo['TotalComments'] = self.formatStr(sel.xpath('//span[@class="count"]/data/@data-value').extract()[0])

        driver = webdriver.Firefox()
        driver.get(response.request.url)
        wait = WebDriverWait(driver, 10)

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, TIME_TO_GO_XPATH))
            )

            items = driver.find_elements(By.XPATH, TIME_TO_GO_XPATH)
            text = items[0].text

        except Exception as e:
            print("Error %s") % e
            projectInfo['TimeToGo'] = 0

        else:
            print("this is text:" + text)
            projectInfo['TimeToGo'] = self.formatNum(text)
            return projectInfo

        finally:
            driver.quit()