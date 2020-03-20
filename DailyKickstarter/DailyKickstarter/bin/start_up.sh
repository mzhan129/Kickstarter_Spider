#!/bin/bash

while true; do
    cd $DAILY_SCRAPY_PATH
    crawl dailykickstarter -a smtp_pass=$SMTP_PASS
    sleep 24h
done