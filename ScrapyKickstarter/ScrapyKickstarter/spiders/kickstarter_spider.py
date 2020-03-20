import scrapy, json, time
import urllib
import pandas as pd
import re as regex
import datetime as dt
import logging
from scrapy.utils.log import configure_logging
from scrapy.selector import Selector
from scrapy.exceptions import CloseSpider
from ScrapyKickstarter.items import ProjectInfo
from ScrapyKickstarter.utils import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Successful projects
# URL = "https://www.kickstarter.com/discover/advanced?state=successful&category_id=12&woe_id=23424977&sort=popularity&seed=2572311&page=%d"

# < 75%
# URL = "https://www.kickstarter.com/discover/advanced?category_id=12&woe_id=23424977&raised=0&sort=popularity&seed=2572311&page=%d"

# [75%, 100%]
class KickstarterSpider(scrapy.Spider):
    name = "kickstarter"
    allowed_domains = ["kickstarter.com"]

    configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename=dt.datetime.now().strftime("%Y-%m-%d") + ".log",
        filemode='w',
        format='%(levelname)s: %(message)s',
        level=logging.DEBUG
    )

    def __init__(self, **kwargs):
        super(KickstarterSpider, self).__init__(**kwargs)
        self.popularity = 0
        self.page_number = 1
        self.url_dict = {}
        self.cancel_projects = []
        self.path_loader = FilepathLoader()

    def formatStr(self, input):
        return regex.sub(r'[^\x00-\x7F]+', ' ', str(input.encode('utf-8')).strip())
        # return str(input.encode('utf-8')).strip()

    def formatNum(self, input):
        return str(input).strip()

    def formatList(self, input):
        return [regex.sub(r'[^\x00-\x7F]+', ' ', text) for text in input]
        # return map(str.strip, [x.encode('ascii', 'ignore').decode('ISO-8859-1').encode('utf-8') for x in input])

    def formatJSon(self, input):
        return "{" + str(input.encode('utf-8'))[1: -1] + "}"

    def formatPercentage(self, pledged, goal):
        return float(pledged) / float(goal)

    def new_project(self, projectJson):
        projectInfo = ProjectInfo()
        projectInfo["ProjectResults"] = {
            "FundedOrNot": self.formatStr(projectJson['state']),
            "AmountAsked": self.formatNum(projectJson['goal']),
            "AmountPledged": self.formatNum(projectJson['pledged']),
            "current_currency": self.formatStr(projectJson['current_currency']),
            "totalBackers": self.formatNum(projectJson['backers_count']),
            "goalFinishedPercentage": self.formatPercentage(projectJson['pledged'], projectJson['goal'])
        }
        projectInfo["ProjectId"] = str(projectJson['id'])
        projectInfo["ProjectTitle"] = self.formatStr(projectJson['name']).replace("/", " ")
        projectInfo["ProjectDescription"] = self.formatStr(projectJson['blurb'])
        projectInfo["CreatedBy"] = self.formatStr(projectJson['creator']['name'])
        projectInfo["ProjectLink"] = str(projectJson['urls']['web']['project'].encode('utf-8'))

        return projectInfo

    def parse(self, response):
        self.page_number += 1
        logging.info("Parse page on page number %d", self.page_number)
        sel = Selector(response)
        project = sel.xpath(DISCOVER_PROJECT_XPATH).extract()
        if not project:
            raise CloseSpider('No more pages')

        self.popularity = 0
        for p in project:
            pStr = "{" + str(p.encode('utf-8'))[1: -1] + "}"
            projectJson = json.loads(pStr)

            # check if the project is not live project
            if projectJson['state'] == "live":
                continue

            # check if the project is not successful
            if float(projectJson['pledged']) >= float(projectJson['goal']):
                continue

            projectInfo = self.new_project(projectJson)

            self.popularity += 1

            request = scrapy.Request(url=projectInfo[PROJECT_LINK], callback=self.parse_project_detail)
            request.meta["projectInfo"] = projectInfo
            yield request

            curPage = response.request.url[response.request.url.index("page=") + 5:]
            projectInfo["popularity"] = 12 * (int(curPage) - 1) + self.popularity

        yield scrapy.Request(URL % self.page_number)

    def parse_project_from_link(self, response):
        logging.info('Parse function called on %s', response.url)
        projectText = response.selector.xpath(SCRIPT_PROJECT_XPATH).get().replace("\\\\&quot;", '\\"').replace("&quot;",
                                                                                                                "\"")

        projectJsonStr = self.formatJSon(regex.search("(window\.current_project = \")(.*)\"", projectText).group(2))

        rawProjectJson = json.loads(projectJsonStr)

        projectInfo = self.new_project(rawProjectJson)
        # logging.info(projectInfo)

        if (self.video == 'on'):
            self.download_video(projectInfo, self.path_loader.get_default_video_loc())
        response.meta['projectInfo'] = projectInfo
        self.parse_project_detail(response)
        request = scrapy.Request(url=rawProjectJson['creator']['urls']['api']['user'], callback=self.parse_creator_profile)
        request.meta['projectInfo'] = projectInfo

        # logging.info(request.meta['projectInfo'])

        return request

    def parse_creator_profile(self, response):
        projectInfo = response.meta['projectInfo']
        creatorProfile = json.loads(response.text)
        projectInfo['CreatorProfile'] = {
            'Description': creatorProfile['biography'],
            'BackedProjectsCount': creatorProfile['backed_projects_count'],
            'CreatedProjectsCount': creatorProfile['created_projects_count']
        }
        # request = scrapy.Request(url= projectInfo['ProjectLink'] + '/updates', callback=self.parse_project_update)
        request = scrapy.Request(url=projectInfo['ProjectLink'] + '/posts', callback=self.parse_project_update)
        request.meta["projectInfo"] = projectInfo
        return request

    # supports, campaign,
    def parse_project_detail(self, response):
        projectInfo = response.meta['projectInfo']
        sel = Selector(response)

        project_state = projectInfo['ProjectResults']['FundedOrNot'].lower()

        # Project Supports
        allLevels = []
        if project_state == LIVE_STATE:
            levelbase = '//div[@class="NS_projects__rewards_list js-project-rewards"]/ol/li[@class="hover-group js-reward-available pledge--available pledge-selectable-sidebar"]'
        elif project_state == SUCCESSFUL_STATE or project_state == UNSUCCESSFUL_STATE or project_state == CANCELED:
            levelbase = '//div[@class="NS_projects__rewards_list js-project-rewards"]/ol/li[@class="hover-group pledge--inactive pledge-selectable-sidebar"]'
        else:
            logging.error('unknown level name %s', project_state)

        levelname = sel.xpath(levelbase + '/div[@class="pledge__info"]/h2/span[@class="money"]/text()').extract()
        levelTitle = sel.xpath(levelbase + '/div[@class="pledge__info"]/h3/text()').extract()
        pledgeRewardDescription = sel.xpath(levelbase + '/div[@class="pledge__info"]'
                                                        '/div[@class="pledge__reward-description pledge__reward-description--expanded"]'
                                                        '/p/text()').extract()
        pledgeEstimateDelivery = sel.xpath(levelbase +
                                           '/div[@class="pledge__info"]/div[@class="pledge__extra-info"]'
                                           '/div[@class="pledge__detail"]/span[@class="pledge__detail-info"]/time/text()').extract()
        pledgeTotalBackers = sel.xpath(levelbase + '/div[@class="pledge__info"]/div[@class="pledge__backer-stats"]'
                                                   '/span/text()').extract()
        totalCount = int(len(sel.xpath(levelbase)))
        if totalCount > 0:
            for i in range(0, totalCount):
                pl = "null" if i >= len(levelname) else self.formatStr(levelname[i])
                pt = "null" if i >= len(levelTitle) else self.formatStr(levelTitle[i])
                prd = "null" if i >= len(pledgeRewardDescription) else self.formatStr(
                    pledgeRewardDescription[i])
                ped = "null" if i >= len(pledgeEstimateDelivery) else self.formatStr(
                    pledgeEstimateDelivery[i])
                ptb = "null" if i >= len(pledgeTotalBackers) else self.formatStr(
                    pledgeTotalBackers[i])

                reward = {
                    "pledgeLevel": pl,
                    "pledgeTitle": pt,
                    "pledgeRewardDescription": prd,
                    "pledgeEstimateDelivery": ped,
                    "pledgeTotalBackers": ptb
                }

                allLevels.append(reward)

        supports = {
            "totalLevels": totalCount,
            "RewardsOfEachLevels": allLevels
        }

        # # Project Campaign
        # # images = sel.xpath('*//div[@class="template asset"]/figure/img/@src').extract()
        # images = self.formatList(sel.xpath('*//div[@class="template asset"]/figure/img/@src').extract())
        # projectInfo['CampaignImages'] = images
        # ti = len(images)
        #
        # # Format campaign text
        # tmp = self.formatList(sel.xpath(
        #     '*//div[@class="full-description js-full-description responsive-media formatted-lists"]//text()').extract())
        # des = [x for x in tmp if len(x) != 0]
        #
        # projectInfo['ProjectCampaign'] = des
        # projectInfo['TotalCampaignImage'] = ti

        # Project timeline
        projectInfo['ProjectTimeLine'] = self.formatList(
            sel.xpath('//div[@class="NS_campaigns__funding_period"]/p/time/@datetime').extract())
        projectInfo['ProjectSupports'] = json.dumps(supports)
        projectInfo['totalComments'] = sel.xpath('//span[@class="count"]/data/@data-value').extract()[0]

        self.parse_project_Campaign(response)


    # Project Campaign
    def parse_project_Campaign(self, response):
        projectInfo = response.meta['projectInfo']
        sel = Selector(response)

        driver = webdriver.Firefox()
        driver.get(projectInfo['ProjectLink'])
        wait = WebDriverWait(driver, 20)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="rte__content"]')))

        images_set = driver.find_elements(By.XPATH, '*//div[@class="template asset"]/figure/img')
        images = [img.get_property('src') for img in images_set]
        # logging.info(images)
        projectInfo['CampaignImages'] = images
        ti = len(images)
        # logging.info(ti)

        # Format campaign text
        # tmp = self.formatList(sel.xpath('*//div[@class="rte__content"]//text()').extract())
        tmp = driver.find_elements(By.XPATH, '*//div[@class="rte__content"]//p')
        des = [p.get_attribute('innerText') for p in tmp]
        logging.info("des")
        logging.info(des)

        projectInfo['ProjectCampaign'] = des
        projectInfo['TotalCampaignImage'] = ti

        driver.quit()

        return projectInfo


    # timelime, updates between each timelime
    def parse_project_update(self, response):
        projectInfo = response.meta['projectInfo']
        sel = Selector(response)
        idx, shipCount, sucCount, lauCount = 0, 0, 0, 0
        for c in sel.xpath('*//div[@class="timeline"]/div/@class').extract():
            cc = self.formatStr(c)
            if "launched" in cc:
                tmp = idx - sucCount
                lauCount = 0 if tmp <= 0 else tmp
            elif "successful" in cc:
                tmp = idx - shipCount
                sucCount = 0 if tmp <= 0 else tmp
            elif "ship" in cc:
                shipCount = idx
            elif "item" in cc:
                idx += 1

        projectInfo['ProjectUpdates'] = {
            "totalUpdatesBeforeFunded": lauCount,
            "totalUpdatesBetweenFundedAndShipped": sucCount,
            "totalUpdatesAfterShipped": shipCount
        }

        project_url_comments = response.request.url[:response.request.url.index("/posts")] + '/comments'
        request = scrapy.Request(project_url_comments, callback=self.parse_project_comments)
        request.meta["projectInfo"] = projectInfo

        return request

    def download_video(self, projectInfo, save_to):
        # Video on title or description and need click
        driver = webdriver.Firefox()
        driver.get(projectInfo['ProjectLink'])
        wait = WebDriverWait(driver, 20)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@class="NS_projects__description_section m-auto"]')))

        project_state = projectInfo['ProjectResults']['FundedOrNot'].lower()

        # find out the click button to load video source
        if project_state == LIVE_STATE or project_state == UNSUCCESSFUL_STATE or project_state == CANCELED:
            play_button_xpath = "//button[contains(@class,'m-auto w20p h20p w15p-md h15p-md p1 p2-md bg-green-700 border border-white border-medium')]"
            video_source_xpath = "*//video[contains(@class, 'aspect-ratio--object z1')]//source"
        elif project_state == SUCCESSFUL_STATE:
            play_button_xpath = "//div[@id='video_pitch']/div[contains(@class, 'play_button_container')]/button"
            video_source_xpath = "//div[@id='video_pitch']/video[contains(@class, 'has_hls landscape')]//source"
        else:
            logging.error("unknown project state %s", project_state)

        # video click and download
        videoClick = driver.find_elements(By.XPATH, play_button_xpath)
        # CampaignVideo
        # CampaignVideoLink
        if videoClick:
            videoClick[0].click()
            time.sleep(0.3)
            video = driver.find_elements(By.XPATH, video_source_xpath)
            if len(video) >= 2:
                url = video[1].get_property('src')
                projectInfo['CampaignVideo'] = "True"
                projectInfo['CampaignVideoLink'] = url

                name = save_to + projectInfo["ProjectId"] + ".mp4"

                logging.info('Downloading %s starts...', name)
                urllib.urlretrieve(url, name)
                logging.info('Download %s completed..!!', name)
        else:
            projectInfo['CampaignVideo'] = "False"
            projectInfo['CampaignVideoLink'] = "No Link"
        driver.quit()

    def parse_project_comments(self, response):
        projectInfo = response.meta['projectInfo']
        driver = webdriver.Firefox()
        driver.get(response.request.url)
        wait = WebDriverWait(driver, 10)
        click_more = True
        count = 0

        items = []

        try:

            # load comments section
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]'))
            )
            # automate click operations to load all comments
            while click_more and len(items) < 1000:
                time.sleep(0.5)
                loadmore = driver.find_elements(By.XPATH, "//button[contains(@class,'bttn') and span='Load more']")
                items = driver.find_elements(By.XPATH,
                                             '*//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]//div[@class="flex mb3"]')
                if loadmore:
                    loadmore[0].click()
                else:
                    click_more = False
                    time.sleep(1)

            # differentiate comments and count the results
            for item in items:
                time.sleep(0.3)
                text = self.formatStr(item.text)
                if "Creator" in text or "Collaborator" in text:
                    count += 1

        except Exception as e:
            projectInfo['totalVCommentsSample'] = "no comments"
            projectInfo['totalVCommentsPercent'] = "no percent"
            logging.warn("Empty comment for project: %s", projectInfo['ProjectTitle'])
            return projectInfo

        else:
            projectInfo['totalVCommentsSample'] = len(items) - count
            if len(items) == 0:
                projectInfo['totalVCommentsPercent'] = 0
            else:
                projectInfo['totalVCommentsPercent'] = 100 * float(projectInfo['totalVCommentsSample']) / float(
                    len(items))
            return projectInfo

        finally:
            driver.quit()

    def search_unknown_urls(self, response):
        """
        fill the unknown url for the given csv file
        :param project_name:
        :return:
        """
        project_title = response.meta['project_title']
        project = response.selector.xpath(DISCOVER_PROJECT_XPATH).getall()
        if len(project) > 0:
            for p in project:
                project_json = json.loads(self.formatJSon(p))
                extracted_name = self.formatStr(project_json['name'])
                if project_title != extracted_name:
                    if 'cancel' in extracted_name.lower():
                        self.cancel_projects.append(extracted_name)
                    logging.warn('Unmatched search result for source [%s] and result [%s], SKIP', project_title,
                                 extracted_name)
                else:
                    project_url = str(project_json['urls']['web']['project'].encode('utf-8'))
                    self.url_dict[project_title] = project_url
                    break
        else:
            logging.warn('%s has been removed from kickstarter SKIP', project_title)

    def start_requests(self):
        if self.mode == 'iterate':
            yield scrapy.Request(url=URL % 1, callback=self.parse)
        elif self.mode == 'search':
            logging.info('Initiate searching for the project csv file')
            projects_df = pd.read_csv(PROJECT_CSV_PATH, thousands=',')
            for index, row in projects_df.iterrows():
                yield scrapy.Request(SEARCH_BASE_URL % row['ProjectTitle'], callback=self.search_unknown_urls,
                                     meta={'project_title': row['ProjectTitle']})
            with open(self.path_loader.get_urls_file_path(), 'w') as fp:
                logging.info('search links result is %d/%d', len(self.url_dict.keys()), projects_df.shape[0])
                fp.write(json.dumps(self.url_dict))
                fp.close()
            logging.info('The length of cancel projects: %d', len(self.cancel_projects))
            logging.debug(self.cancel_projects)

        elif self.mode == 'from_file':
            with open(self.path_loader.get_urls_file_path(), 'r') as json_file:
                data = dict(json.load(json_file))
                for url in data.values():
                    yield scrapy.Request(url, callback=self.parse_project_from_link)
        else:
            logging.error('unknown running mode, now support iterate and search mode')
