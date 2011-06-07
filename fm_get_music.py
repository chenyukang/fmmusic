#encoding: utf-8
"""
Copyright (C) 2011 Chen Yukang <moorekang@gmail.com>
is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 """

import time,math,os,re,urllib,urllib2,cookielib
import HTMLParser
from BeautifulSoup import BeautifulSoup

import sys
import string

class MyParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)       

    def handle_starttag(self, tag, attrs):
        # 这里重新定义了处理开始标签的函数
        if tag == 'a':
            # 判断标签<a>的属性
            for name,value in attrs:
                if name == 'href':
                    print value




#配置信息
class douban:
    email = "your_email"
    password = "your_passwd"
    login_path = "http://www.douban.com/accounts/login"

    def __init__(self):
        self.cj = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(self.opener)
        self.opener.addheaders = [('User-agent','Opera/9.23')]

    def gettable(self,str):
        lenth=len(str)
        index1=str.find("<table");
        index2=str.find("table",index1+5);
        ret=str[index1:index2+6]
        return ret
    
    def getvalue(self,str):
        index1=str.find(">")
        index2=str.find("<",index1+2)
        return str[index1+1:index2]

    def getcount(self,str):
        index1=str.find("songs_tabs")
        index2=str.find("首喜欢的")
        return str[index1+19:index2]

    #模拟登陆
    def login(self):
        post_data = urllib.urlencode({
            'form_email':self.email,
            'form_password':self.password,
            'remeber':'on',
            })
        #发起HTTP请求
        print post_data
        request = urllib2.Request(self.login_path,post_data)
        html = self.opener.open(request).read()
        get_url = self.opener.open(request).geturl()
        if get_url == 'http://www.douban.com/':
            print get_url
            self.cj.save('douban.cookie')
            print 'Login success !'

            path = 'http://douban.fm/mine?start=0&type=liked'
            #print path
            response = urllib2.Request(path)
            html = self.opener.open(response).read()
            f = urllib2.urlopen("http://douban.fm/mine?start=100&type=liked")
            res=f.read()
            count=string.atoi(self.getcount(res))
            print count

            gotnum=0
            starter=0
            title=[]
            output = open('songlist.txt', 'w')
            while gotnum<count:
                url = "http://douban.fm/mine?start=%d&type=liked" %starter
                print url
                starter=starter+9
                f = urllib2.urlopen(url)
                res=f.read()
                count=string.atoi(self.getcount(res))
                table=self.gettable(res)
                soup = BeautifulSoup(table,fromEncoding="UTF-8")
            
                musicname=soup.findAll("td")
                i=0
                while i<len(musicname):
                    if i%3==0:
                        now=musicname[i]
                        now=self.getvalue(str(now))
                        output.write(now+'\n')
                        title.append(now)
                    i=i+1

                author=soup.findAll("span")
                i=0
                while i<len(author):
                    now=author[i]
                    now=self.getvalue(str(now))
                    i=i+1
                gotnum=gotnum+9

            return True
        else:
            print get_url
            print 'Login error'
            return False


test=douban()
test.login()
