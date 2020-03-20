#### How to spawn Daily Kickstarter spider

Go to the `<your path>/Kickstarter_Spider/DailyKickstater/` 

Type the following script on `git bash` to have the spider run periodically. 

``` bash
while true;
do scrapy crawl dailykickstarter;
sleep 24h;
done
```

#### How to spawn Video Kickstarter spider

Step 1: prepare the urls json file in advance by following the format of a dictionary in python

Step 2: place the file `urls.json` into the location `D:/kickstarter`.

Step 3: create a new folder called `video` under the location `D:/kickstarter`

Step 4: Go to the `<your path>/Kickstarter_Spider/ScrapyKickstarter/`

If you want to collect the video, set the `video` parameter as `on`

``` bash
crawl kickstarter -a mode=from_file -a video=[off/on]
```

#### How to spawn Creator Kickstarter spider

Go to the `<your path>/Kickstarter_Spider/Kickstater_Creator/` 

Type the following script on `git bash` to have the spider run periodically. 

``` bash
scrapy crawl scrapy_creator
```
Or
run the "main.py" file
