import json

projects = {}

projects_res = open("0726_1101_ProjectInfo.json", 'r')
projs = json.load(projects_res)
print(len(projs))

for proj in projs:
    projects[proj['ProjectLink']] = proj

comments_res = open("comments_100_0726_1101.json", 'r')
coms = json.load(comments_res)
print(len(coms))

# for i in range(len(coms)):
#     coms[i]['ProjectId'] = ''
#     if projects.keys().__contains__(coms[i]['ProjectLink']):
#         coms[i]['ProjectId'] = projects[coms[i]['ProjectLink']]['ProjectId']

i = 0
while i < len(coms):
    # print(i)
    if projects.keys().__contains__(coms[i]['ProjectLink']):
        coms[i]['ProjectId'] = projects[coms[i]['ProjectLink']]['ProjectId']
    else:
        del coms[i]
        i = i - 1
    i = i + 1

with open("comments_0726_1101.json", 'w') as jsonFile:
    json.dump(coms, jsonFile)

