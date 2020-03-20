from ConfigParser import RawConfigParser
# URL
SEARCH_BASE_URL = "https://www.kickstarter.com/discover/advanced?ref=nav_search&term=%s"
URL = "https://www.kickstarter.com/discover/advanced?category_id=12&woe_id=23424977&raised=1&sort=popularity&seed=2572311&page=%d"

# XPATH
DISCOVER_PROJECT_XPATH = '//section[@id="projects"]/div[@class="grid-container"]/div[@class="js-project-group"]/div[contains(@class, "grid-row")]/div[contains(@class, "js-react-proj-card")]/@data-project'
URL_PROJECT_XPATH = '//div[@id="react-project-header"]/@data-initial'
PROJECT_STATE_XPATH = '//div[@class="NS_projects__content pt11"]/section/@data-project-state'
SCRIPT_PROJECT_XPATH = '//script[contains(text(), "window.current_project")]/text()'

# FILE_PATH
PROJECT_CSV_PATH = './projectDaily.csv'
FILE_BASE = './'
URLS_FILE_PATH = '%s/urls.json'
DEFAULT_VIDEO_LOC = '%s/video/'
PROJECT_INFO_PATH = '%s/projectInfo.json'

# Project State
LIVE_STATE = 'live'
SUCCESSFUL_STATE = 'successful'
UNSUCCESSFUL_STATE = 'failed'
CANCELED = 'canceled'

# ATTRIBUTE_KEY
PROJECT_LINK = 'ProjectLink'


class FilepathLoader:
    def __init__(self):
        parser = RawConfigParser()
        parser.read('bootstrap.ini')
        self.filebase = parser.get('file','filebase')

    def get_urls_file_path(self):
        return URLS_FILE_PATH % self.filebase

    def get_default_video_loc(self):
        return DEFAULT_VIDEO_LOC % self.filebase

    def get_project_info_path(self):
        return PROJECT_INFO_PATH % self.filebase
