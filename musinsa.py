# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxp-506652758256-506747893024-507363499668-19b492d4719babc19e3d94720d96be47"
slack_client_id = "506652758256.506928372897"
slack_client_secret = "e41b147e97554914599df4d6ecc9f933 "
slack_verification = "HmkVWbGuAYthZkQ3ekwvomr3"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    keywords = []
    if "세일" in text:
        
        url = "https://store.musinsa.com/app/contents/onsale?sale_yn=Y&sale_dt_yn=Y&chk_timesale=on"
        req = urllib.request.Request(url)
        
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")
        
        #함수를 구현해 주세요

        keywords = []
        titles = []
        prices = []

        keywords.append("---- 세일 상품 목록 ----" +'\n')
        for data in (soup.find_all("div", class_="list-box box")):
            for data1 in data.find_all("p", class_="list_info"):
                titles.append(data1.get_text().strip())
            for data2 in data.find_all("p", class_="price"):
                prices.append(str(data2.get_text()).replace('					',' >> '))
    
        for i in range(10):  
                keywords.append(str(i+1)+". "+titles[i] +prices[i])    




    elif ("상품" in text) and (("순위" in text) or ("랭크" in text) or ("랭킹" in text)):
        url = "https://store.musinsa.com/app/contents/bestranking"
        req = urllib.request.Request(url)
        
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")
        
        #함수를 구현해 주세요

        keywords = []
        titles = []
        prices = []
        ranks = []
        
        keywords.append("---- 상품 순위 ----" +'\n')
        for data in (soup.find_all("div", class_="list-box box")):
            for data1 in data.find_all("p", class_="list_info"):
                titles.append(data1.get_text().strip())
            for data2 in data.find_all("p", class_="price"):
                for data3 in data2.find_all("del", class_="box_origin_price"):
                    prices.append(str(data2.get_text()).replace(data3.get_text(),'').replace('					',' '))
            
        for i in range(10):
                keywords.append("No."+str(i+1)+'\n'+titles[i] +prices[i])    



    elif ("브랜드" in text) and (("순위" in text) or ("랭크" in text) or ("랭킹" in text)):
        url = "https://store.musinsa.com/app/usr/brand_rank"
        req = urllib.request.Request(url)
        
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")
        
        #함수를 구현해 주세요

        keywords = []
        titles = []
        entitles = []
        ranks = []
        
        keywords.append("---- 브랜드 순위 ----" +'\n')
        for data in (soup.find_all("div", class_="list-box box")):
            for data1 in data.find_all("p", class_="brand_name"):
                titles.append(data1.get_text())
            for data2 in data.find_all("p", class_="brand_name_en"):
                entitles.append(data2.get_text())
            
        for i in range(10):
                keywords.append("No."+str(i+1)+'\n'+titles[i] +" ( "+entitles[i]+" )")    



                
    elif ("검색어" in text) and (("순위" in text) or ("랭크" in text) or ("랭킹" in text)):
        url = "https://store.musinsa.com/app/usr/search_ranking"
        req = urllib.request.Request(url)

        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")

        #함수를 구현해 주세요

        keywords = []
        titles = []
        prices = []
        ranks = []

        keywords.append("---- 검색어 순위 ----" +'\n')
        for data in (soup.find_all("div", class_="tbl_box_sranking")):
            for data1 in data.find_all("p", class_="p_srank"):
                titles.append(data1.get_text().strip())
            for data2 in data.find_all("p", class_="p_srank_last"):
                #for data3 in data2.find_all("span", class_="arrow"):
                prices.append(str(data2.get_text()))
                #prices.append(str(data2.get_text()).replace(data3.get_text(),'').replace('                    ',' '))


        for i in range(10):
                keywords.append(titles[i]+ " "+prices[i]+"\n")

    else:
        keywords.append("올바른 검색어를 입력하세요 ㅡㅡ")   
   

    
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
