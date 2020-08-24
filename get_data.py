import argparse, os, time
import random
import sqlite3
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import schedule
import csv
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import requests
import sqlite3
import telegram

bitly_token = ['87560fe9b0f92d08b566103bf44591589c4e33c8']


def tag_search(tags):
    # Logging
    browser = webdriver.Chrome('chromedriver.exe')
    browser.get("https://www.linkedin.com")
    browser.maximize_window()
    browser.implicitly_wait(3)
    browser.find_element_by_xpath('//a[contains(@class, "nav__button-secondary")]').click()
    sleep(3)
    browser.find_element_by_id('username').send_keys('viktor.raboshchuk@gmail.com')
    browser.find_element_by_id('password').send_keys('123qweasdzxc')
    browser.find_element_by_class_name('login__form_action_container ').click()
    print("success! Logged in, Bot starting")
    sleep(5)
    # Searching
    search = browser.find_element_by_xpath("//input[@aria-label='Search']")
    search.click()
    sleep(2)
    search.clear()
    search.send_keys(tags)
    search.send_keys(Keys.ENTER)
    sleep(3)
    browser.find_element_by_xpath('//ul[@class = "peek-carousel__slides js-list"]/li[2]/form/button').click()
    browser.find_element_by_xpath(
        '//fieldset[@class = "search-s-facet__values search-s-facet__values--is-floating search-s-facet__values--recency artdeco-card"]/div/ul/li[1]/label').click()
    browser.find_element_by_xpath(
        '//fieldset[@class = "search-s-facet__values search-s-facet__values--is-floating search-s-facet__values--recency artdeco-card"]/div/div/div/button[2]').click()
    sleep(5)
    # Get latest posts
    try:
        post_time = browser.find_element_by_xpath('//*[@class = "sort-dropdown ember-view"]/div/button')
    except NoSuchElementException as e:
        print(e)
        browser.close()
        sys.exit(1)

    post_time.click()
    sleep(7)
    browser.find_element_by_xpath('//*[@class = "sort-dropdown ember-view"]/div/div//div/ul/li[2]/div/button').click()
    sleep(10)
    browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
    sleep(2)
    print('Search step - done')

    return browser


def parse_posts(browser):
    all_posts = browser.find_elements_by_xpath('//ul[contains(@class, "search-results__list list-style-none")]')

    for i in all_posts:
        ids = i.find_elements_by_tag_name('li')
        id_arr = []
        for i in ids:
            id = i.get_attribute("id")
            if id != '':
                id_arr.append(id)

    print('Get all id - done. \nId array length is :', len(id_arr))

    parsed_dict = []

    for i in id_arr:
        element = browser.find_element_by_id(i)
        sleep(3)
        browser.execute_script("arguments[0].scrollIntoView();", element)
        sleep(3)
        link = element.find_element_by_css_selector('a')
        href = link.get_attribute('href')
        sleep(3)
        try:
            btn = element.find_element_by_xpath('//*[contains(text() , "…see more")]')
            btn.click()
            sleep(3)
            browser.execute_script("arguments[0].scrollIntoView();", element)
            post_text = element.find_elements_by_css_selector(
                'div.feed-shared-text.relative.feed-shared-update-v2__commentary.ember-view')
            for post in post_text:
                text_id = post.get_attribute("id")
                text_element = browser.find_element_by_id(text_id)
                text = ''
                text = text_element.find_element_by_css_selector('span.break-words').text
                parsed_dict.append([href, text])
        except (NoSuchElementException, ElementClickInterceptedException) as e:
            print('Full post')
    sleep(3)
    return parsed_dict
    print('Parse posts - done')


def add_data_to_db(parsed_dict):
    count = 0
    contacts = ['Telegram','Skype','Phone','+38','tel','Tel','e-mail','E-mail','email','Email','@','скайпі','Cкайпі']

    conn = sqlite3.connect('my_db.db')
    c = conn.cursor()


    for i in parsed_dict:
        link = i[0]
        text = i[1]
        if len(text) > 105 and 'RECOMMENDATION' not in text and 'Став лайк, щоб допомогти закрити вакансію' not in text :
            print()
            text_data = '%' + str(text.split('\n')[1]) + '%'
            sql_data = c.execute('select * from vacancies where description like ?', (text_data,))
            sql_data_ln = sql_data.fetchall()
            print('sql_data length: ', len(sql_data_ln))
            print('text ln: ', len(text))
            if '¶' in text:
                text = text.replace('¶','- ')
            elif any(x in text for x in contacts):
                if sql_data_ln == 0:
                    print()
                    print('OK')
                    c.execute('INSERT into vacancies (description) values (?)' ,(text,))
                    conn.commit()
                    count += 1
                else:
                    print('Уже есть')
            else:
                if sql_data_ln == 0:
                    header = {
                        "Authorization": bitly_token,
                        "Content-Type": "application/json"
                    }
                    params = {
                        "long_url": link
                    }
                    response = requests.post("https://api-ssl.bitly.com/v4/shorten", json=params, headers=header)
                    data = response.json()
                    if 'link' in data.keys():
                        short_link = data['link']
                    else:
                        short_link = None
                    description = '\nКонтакты: '.join([text, short_link])
                    c.execute('INSERT into vacancies (description) values (?)' ,(description,))
                    conn.commit()
                    count += 1
                else:
                    print('Уже есть')
    conn.close()
    return count
    print('Add data to DB - done')



def post_on_channel(browser, count):
    # chat id for MAIN channel 1001247011548
    # chat id for TEST channel 1001250578685
    TOKEN = "1035844374:AAFGewsW0bUgddti5OznkxgoQJKfZ9UP8FQ"

    # use token generated in first step
    bot = telegram.Bot(token=TOKEN)

    conn = sqlite3.connect('C:\sqlite\my_db.db')
    c = conn.cursor()

    sql_data = c.execute('select * from vacancies order by id desc limit {}'.format(count))
    for post in sql_data.fetchall():
        #     print(post[1])
        sleep(5)
        bot.send_message(chat_id="-1001247011548", text=post[1], parse_mode=telegram.ParseMode.HTML)

    browser.close()

def job():
    browser = tag_search('#vacancy #kiev')
    parsed_posts = parse_posts(browser)
    count = add_data_to_db(parsed_posts)
    post_on_channel(browser, count)


schedule.every(2).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
