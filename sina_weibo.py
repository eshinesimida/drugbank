# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# -*- coding: utf-8 -*-
import time
import datetime
import re
import os
import sys
import codecs
import shutil
import urllib
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.action_chains import ActionChains
import xlwt
# import requests
import requests
from lxml import etree
import pymysql

# 先调用无界面浏览器PhantomJS或Firefox
# driver = webdriver.PhantomJS()
driver = webdriver.Chrome()
connect = pymysql.Connect(
    host='rm-wz988to0p0a7js870o.mysql.rds.aliyuncs.com',
    port=3306,
    user='root',
    passwd='zd45+3=48',
    db='ctrip_gengxin',
    use_unicode=1,
    charset='utf8'
)
headers = {'Accept-Charset': 'UTF-8',
           'Accept-Encoding': 'gzip,deflate',
           'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; MI 5 MIUI/V8.1.6.0.MAACNDI)',
           'X-Requested-With': 'XMLHttpRequest',
           'Content-type': 'application/x-www-form-urlencoded',
           'Connection': 'Keep-Alive'}


# ********************************************************************************
#                            第一步: 登陆login.sina.com
#                     这是一种很好的登陆方式，有可能有输入验证码
#                          登陆之后即可以登陆方式打开网页
# ********************************************************************************

def LoginWeibo(username, password):
    try:
        # 输入用户名/密码登录
        print (u'准备登陆Weibo.cn网站...')
        driver.get("http://login.sina.com.cn/")
        elem_user = driver.find_element_by_name("username")
        elem_user.send_keys(username)  # 用户名
        elem_pwd = driver.find_element_by_name("password")
        elem_pwd.send_keys(password)  # 密码
        # <input tabindex="5" class="W_btn_a btn_34px" style="width:202px;" type="submit" value="登 录">
        elem_sub = driver.find_element_by_xpath("//input[@class='W_btn_a btn_34px']")
        elem_sub.click()  # 点击登陆 因无name属性

        try:
            # 输入验证码
            time.sleep(20)
            elem_sub.click()
        except:
            # 不用输入验证码
            pass

        # 获取Coockie 推荐资料：http://www.cnblogs.com/fnng/p/3269450.html
        print ('Crawl in ', driver.current_url)
        print (u'输出Cookie键值对信息:')
        for cookie in driver.get_cookies():
            print (cookie)
            for key in cookie:
                print (key, cookie[key])
        print (u'登陆成功...')
    except Exception as e:
        print ("Error: ", e)
    finally:
        print (u'End LoginWeibo!\n')


# ********************************************************************************
#                  第二步: 访问http://s.weibo.com/页面搜索结果
#               输入关键词、时间范围，得到所有微博信息、博主信息等
#                     考虑没有搜索结果、翻页效果的情况
# ********************************************************************************

def GetSearchContent(key):
    # driver.get("http://s.weibo.com/")
    url1 = 'https://s.weibo.com/weibo?q=' + str(key) + '&Refer=SWeibo_box'
    driver.get(url1)
    #driver.get('https://s.weibo.com/weibo?q=%E4%B8%AA%E7%A8%8E%E8%B5%B7%E5%BE%81%E7%82%B9&Refer=SWeibo_box')
    print ('搜索热点主题：', key)

    # 输入关键词并点击搜索
    # //*[@id="pl_homepage_search"]/div/div[2]/div/input
    # //*[@id="pl_homepage_search"]/div/div[2]/div/input
    # item_inp = driver.find_element_by_xpath("//*[@id='pl_homepage_search']/div/div[2]/div/input")
    # item_inp = driver.find_element_by_xpath("//*[@id='plc_top']/div/div/div[2]/input")
    # item_inp = driver.find_element_by_xpath("//input[@class='searchInp_form']")
    # item_inp.send_keys(key)
    # item_inp.send_keys(Keys.RETURN)  # 采用点击回车直接搜索

    # 获取搜索词的URL，用于后期按时间查询的URL拼接
    current_url = driver.current_url
    current_url = current_url.split('&')[
        0]  # http://s.weibo.com/weibo/%25E7%258E%2589%25E6%25A0%2591%25E5%259C%25B0%25E9%259C%2587

    global start_stamp
    global page

    # 需要抓取的开始和结束日期
    start_date = datetime.datetime(2015, 12, 9, 0)
    end_date = datetime.datetime(2015, 12, 30, 0)
    delta_date = datetime.timedelta(days=1)

    # 每次抓取一天的数据
    start_stamp = start_date
    end_stamp = start_date + delta_date

    global outfile
    global sheet

    outfile = xlwt.Workbook(encoding='utf-8')

    while end_stamp <= end_date:
        page = 1

        # 每一天使用一个sheet存储数据
        sheet = outfile.add_sheet(str(start_stamp.strftime("%Y-%m-%d-%H")))
        initXLS()

        # 通过构建URL实现每一天的查询
        url = current_url + '&typeall=1&suball=1&timescope=custom:' + str(
            start_stamp.strftime("%Y-%m-%d-%H")) + ':' + str(end_stamp.strftime("%Y-%m-%d-%H")) + '&Refer=g'
        driver.get(url)

        handlePage()  # 处理当前页面内容

        start_stamp = end_stamp
        end_stamp = end_stamp + delta_date


# ********************************************************************************
#                  辅助函数，考虑页面加载完成后得到页面所需要的内容
# ********************************************************************************

# 页面加载完成后，对页面内容进行处理
def handlePage():
    i = 1
    while True:
        # 之前认为可能需要sleep等待页面加载，后来发现程序执行会等待页面加载完毕
        # sleep的原因是对付微博的反爬虫机制，抓取太快可能会判定为机器人，需要输入验证码
        time.sleep(5)
        # 先行判定是否有内容
        if checkContent():
            i = i + 1

            print ("getContent")
            getContent()
            if i == 50:
                break
            # 先行判定是否有下一页按钮
            if checkNext():
                # 拿到下一页按钮
                next_page_btn = driver.find_element_by_xpath("//a[@class='next']")
                # next_page_btn = driver.find_element_by_xpath("//a[@class='page next S_txt1 S_line1']")
                next_page_btn.click()
            else:
                print ("no Next")
                break
        else:
            print ("no Content")
            break


# 判断页面加载完成后是否有内容
def checkContent():
    # 有内容的前提是有“导航条”？错！只有一页内容的也没有导航条
    # 但没有内容的前提是有“pl_noresult”
    try:
        driver.find_element_by_xpath("//div[@class='pl_noresult']")
        flag = False
    except:
        flag = True
    return flag


# 判断是否有下一页按钮
def checkNext():
    try:
        target = driver.find_element_by_class_name(
            'm-page')
        y = target.location['y']
        ##allCmtComment > div.paging.orangestyle > div
        print (y)
        # print self.driver.page_source
        y = y - 100

        # self.driver.execute_script("arguments[0].scrollIntoView();", target)
        time.sleep(5)
        js = "var q=document.documentElement.scrollTop=" + str(y)
        driver.execute_script(js)
        driver.find_element_by_xpath("//a[@class='next']")
        flag = True
    except:
        flag = False
    return flag


# 在添加每一个sheet之后，初始化字段
def initXLS():
    name = ['博主昵称', '博主主页', '微博认证', '微博达人', '微博内容', '发布时间', '微博地址', '微博来源', '转发', '评论', '赞']

    global row
    global outfile
    global sheet

    row = 0
    for i in range(len(name)):
        sheet.write(row, i, name[i])
    row = row + 1
    outfile.save("./crawl_output_YS.xls")


# 将dic中的内容写入excel
def writeXLS(dic):
    global row
    global outfile
    global sheet

    for k in dic:
        for i in range(len(dic[k])):
            sheet.write(row, i, dic[k][i])
        row = row + 1
    outfile.save("./crawl_output_个税.xls")


# 在页面有内容的前提下，获取内容
def getContent():
    # 寻找到每一条微博的class
    # //*[@id="pl_feedlist_index"]/div[2]/div[1]
    nodes = driver.find_elements_by_xpath("//div[@class='card-wrap']")
    # nodes = driver.find_elements_by_xpath("//div[@class='WB_cardwrap S_bg2 clearfix']")

    # 在运行过程中微博数==0的情况，可能是微博反爬机制，需要输入验证码
    if len(nodes) == 0:
        # print (driver.current_url)
        raw_input("请在微博页面输入验证码！")
        # print ('输入验证码')
        # url = driver.current_url
        # driver1 = webdriver.Chrome()
        #driver.get(url)

        getContent()
        return

    dic = {}

    global page
    print (str(start_stamp.strftime("%Y-%m-%d-%H")))
    print '页数:', page
    page = page + 1
    print '微博数量', len(nodes)

    for i in range(len(nodes)):
        dic[i] = []
        # print(nodes[i].find_element_by_xpath(".//div[@class='content']/div[@class='info']"))

        try:
            BZNC = nodes[i].find_element_by_xpath(".//div[@class='info']/div[2]/a[@class='name']").text
            # BZNC = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='W_texta W_fb']").text
        except:
            BZNC = 'None'
        #print u'博主昵称:', BZNC
        dic[i].append(BZNC)

        try:
            BZZY = nodes[i].find_element_by_xpath(
                ".//div[@class='info']/div[2]/a[@class='name']").get_attribute("href")


        except:
            BZZY = ''
        #print '博主主页:', BZZY
        dic[i].append(BZZY)
        id1 =  BZZY.split('/')[-1].split('?')[0]
        url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + str(id1)
        html = requests.get(url, headers = headers)
        info  = html.json()
        #print info
        if('data' in info.keys()):
            if('userInfo' in info['data'].keys()):
                name = info['data']['userInfo']['screen_name']
                num_weibo = info['data']['userInfo']['statuses_count']
                sex = info['data']['userInfo']['gender']
                followers = info['data']['userInfo']['followers_count']
                follow = info['data']['userInfo']['follow_count']
                level = info['data']['userInfo']['urank']
                des = info['data']['userInfo']['description']
            else:
                name = 'null'
                num_weibo = 'null'
                sex = 'null'
                followers = 'null'
                follow = 'null'
                level = 'null'
                des = 'null'




        #print info['data']


        else:
            name = 'null'
            num_weibo = 'null'
            sex = 'null'
            followers = 'null'
            follow = 'null'
            level = 'null'
            des = 'null'


        #driver.get(BZZY)
        #driver.close()
        # num = driver.find_elements_by_xpath(
        #     '//*[@id="Pl_Core_T8CustomTriColumn__3"]/div/div/div/table/tbody/tr/td[1]/a/strong')
        #print num

        ID1 = nodes[i].get_attribute('mid')
       # print 'ID1,',ID1
        url_comment = 'https://m.weibo.cn/api/comments/show?id=' + str(ID1)
        html2 = requests.get(url_comment, headers = headers)

        if('data' in html2.json().keys()):
            D = []
            for jj in range(len(html2.json()['data']['data'])):
                data = html2.json()['data']['data'][jj]['text']
                hanzi = ''.join(re.findall('[\u4e00-\u9fa5]', data))
                time1 = html2.json()['data']['data'][jj]['created_at']
                user = html2.json()['data']['data'][jj]['user']['screen_name']
                D.append(user)
                D.append(data)
                D.append(time1)
            comment = ';'.join(D)
                #print user,time1,data
        else:
            comment = 'null'
        #print

        #


        # try:
        #     WBRZ = nodes[i].find_element_by_xpath(
        #         ".//div[@class='feed_content wbcon']/a[@class='approve_co']").get_attribute('title')  # 若没有认证则不存在节点
        # except:
        #     WBRZ = ''
        # #print WBRZ
        # # print ('微博认证:', WBRZ)
        # dic[i].append(WBRZ)
        #
        # try:
        #     WBDR = nodes[i].find_element_by_xpath(
        #         ".//div[@class='feed_content wbcon']/a[@class='ico_club']").get_attribute('title')  # 若非达人则不存在节点
        # except:
        #     WBDR = ''
        # # print ('微博达人:', WBDR)
        # dic[i].append(WBDR)

        try:
            WBNR = nodes[i].find_element_by_xpath(".//div[@class='content']/p[@class='txt']").text
            # WBNR = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/p[@class='comment_txt']").text
        except:
            WBNR = ''
        #print '微博内容:', WBNR
        dic[i].append(WBNR)

        try:
            FBSJ = nodes[i].find_element_by_xpath(".//div[@class='content']/p[@class='from']/a[1]").text
            #FBSJ = str(u'2018年')+ str(FBSJ)
            #s1 + unicode(s2, 'utf-8')
            #print '2018年' + unicode(FBSJ,'utf-8')
            #print FBSJ, type(FBSJ)

            # FBSJ = nodes[i].find_element_by_xpath(".//div[@class='feed_from W_textb']/a[@class='W_textb']").text
        except:
            FBSJ = ''
        #print '发布时间:', FBSJ
        dic[i].append(FBSJ)

        try:
            WBDZ = nodes[i].find_element_by_xpath(
                ".//div[@class='feed_from W_textb']/a[@class='W_textb']").get_attribute("href")
        except:
            WBDZ = ''
        # print ('微博地址:', WBDZ)
        dic[i].append(WBDZ)

        try:
            WBLY = nodes[i].find_element_by_xpath(".//div[@class='content']/p[@class='from']/a[2]").text
            # WBLY = nodes[i].find_element_by_xpath(".//div[@class='feed_from W_textb']/a[@rel]").text
        except:
            WBLY = ''
        # print ('微博来源:', WBLY)
        dic[i].append(WBLY)

        try:
            ZF_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_forward']").text
            if ZF_TEXT == '':
                ZF = 0
            else:
                ZF = re.sub('\D','',ZF_TEXT)
                #ZF = int(ZF_TEXT)
                if(ZF):
                    ZF = ZF
                else:
                    ZF = 0
        except:
            ZF = 0
        print '转发:', ZF
        dic[i].append(str(ZF))

        try:
            PL_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_comment']").text  # 可能没有em元素
            if PL_TEXT == '':
                PL = 0
            else:
                PL = re.sub('\D','',PL_TEXT)
                if(PL):
                    PL = PL
                else:
                    PL = 0
                #PL = int(PL_TEXT)
        except:
            PL = 0
        print '评论:', PL
        dic[i].append(str(PL))

        try:
            ZAN_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_like']//em").text  # 可为空
            if ZAN_TEXT == '':
                ZAN = 0
            else:
                ZAN = int(ZAN_TEXT)
        except:
            ZAN = 0
        # print ('赞:', ZAN)
        dic[i].append(str(ZAN))
        year = '2017'
        cursor = connect.cursor()
        sql = "INSERT INTO yimiao_17(`ID`,`name`,`year` ,`num`, `sex`,`guanzhu`, `fans`,`level`,`des`, `comment`,`time`,`text`," \
              "`zf`,`pl`,`zan`) VALUES ( '%s','%s', '%s', '%s', '%s','%s', '%s', '%s', '%s','%s', '%s', '%s','%s', '%s', '%s')"
        data = (ID1,name,year, num_weibo, sex, follow, followers, level, des,comment,FBSJ,WBNR,ZF,PL,ZAN)
        try:
            cursor.execute(sql % data)
        except:
            print(ID1)

        connect.commit()
        print ID1
        #print ID1,name, num_weibo, sex, follow, followers, level, des,comment,FBSJ,WBNR

        # print ('\n')

    # 写入Excel
    #print(dic)
    #writeXLS(dic)


# *******************************************************************************
#                                程序入口
# *******************************************************************************
if __name__ == '__main__':
    # 定义变量
    username = '852223801@qq.com'  # 输入你的用户名
    password = '112407@yqh'  # 输入你的密码

    # 操作函数
    LoginWeibo(username, password)  # 登陆微博

    # 搜索热点微博 爬取评论
    key = '疫苗'
    GetSearchContent(key)