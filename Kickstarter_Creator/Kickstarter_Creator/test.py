import json

proj_url = open("/home/manlin/PycharmProjects/Kickstarter_Creator/creatorInfo_temp.json", 'r')
urls = json.load(proj_url)

print(len(urls))