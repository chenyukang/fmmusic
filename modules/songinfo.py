#coding=utf8
# vim: set fileencoding=utf8 sts=4 sw=4 expandtab :
"""
 Copyright (C) 2006 Xupeng Yun <recordus@gmail.com>
 
 This file is part of getsong. getsong is a tool for downloading mp3 
 automatically, with getsong you can download mp3 in a flash:)

 getsong is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 
 pygetsong is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA
 
 Changelog:
 2006-11-14 
     Shixin Zeng <zeng.shixin@gmail.com> rewrite URLChecker and GetBestUrl,
     a more efficient algorithm is used.
     
 $Id: songinfo.py 1755 2006-12-11 13:01:23Z recordus $
 """

import re
import time
import socket
import string
import urllib
import urllib2
import threading
from utils import HasLive, AnalysysHttpHeader
  
class TooSmall(Exception):pass

def QuoteURL(url):
    """
    arguments:
        url, in GBK encoding.
    return vlaues:
        url, in GBK encoding.
    """
    pattern = u'[\u4e00-\u9fa5]+'.encode('utf8')
    rs = re.findall(pattern, url.decode('gbk', 'ignore').encode('utf8'))
    for word in rs:
        url = url.replace(word, urllib.quote(word.decode('utf8', 'ignore').encode('gbk')))
    
    return url

def __getFakeURLs(artist, title):
    """Search results in baidu can't be downloaded directly,
       this function get top 30(or less) urls from the results.
       arguments:
           artist (unicode)
           title (unicode)
       return values:
           urls: urls got from search results, in GBK encoding.
    """
    baseurl = 'http://mp3.baidu.com/m?f=ms&tn=baidump3&ct=134217728&lf=&rn=&lm=0&word='
    #baseurl = 'http://mp3.baidu.com/m?f=ms&rf=idx&tn=baidump3&ct=134217728&lf=&rn=&word='
    #multi artist are seperated by '_', replace it with space here
    artist = artist.replace('_', ' ')
    keyword = '%s+%s' %(artist, title)
    keyword = keyword.encode('gbk')
    url = baseurl + urllib.quote(keyword, string.punctuation)
    
    urls = []
    try:
        html = urllib2.urlopen(url).read()
    except UnicodeDecodeError:
        return urls
    except:
        return urls
    
    pattern = 'http://.*?baidusg.*?&titlekey=\d+,\d+'
    urls = re.findall(pattern, html)

    if len(urls) >= 20:
        return urls[:20]
    else:
        return urls

def GetRealMp3URL(fake_url): 
    """
    arguments:
        fakeurl, in GBK encoding.
    return values:
        realurl, in GBK encoding.
    """
    def GetSeeds(fake_url):
        re_num = re.compile('song_(\d+);')
        #re_j = re.compile('J="([^"]+)"')
        re_j = re.compile('subulrs = \[(.*?)\]')
        #re_seeds = re.compile('N\((\d+),(\d+),(\d+)\)')
        re_seeds = re.compile( 'init\((\d+), (\d+), (\d+)\)' )

        html = urllib.urlopen(fake_url).read().decode('gbk','ignore')

        num = re_num.findall(html)
        num = num and int(num[0]) or None
        #print 'num',num

        j = re_j.findall(html)
        if j==None:
            return None

        j = j[0].replace('"','').split(',')
        j = j and j[0] or None
        #print 'encoded url', j
        if j == None : j = ''

        seeds = re_seeds.findall(html)
        seeds = [(int(s[0]), int(s[1]), int(s[2])) for s in seeds]
        #print 'seeds',seeds

        return (num, j, seeds)
     

    def Decode(song_number, encoded_url, seeds):

        def GeneratePasswordBook(seed):
            s = seed[0]
            p = seed[1]
            q = seed[2]
            for r in xrange(s, p+1):
                k[r] = r + q 
                h[r+q] = r 

        k = {}
        h = {}

        for seed in seeds:
            GeneratePasswordBook(seed)

        m= song_number % 26
        m = m and m or 1

        s = ''
        for i in encoded_url:
            if i.isdigit() or i.isalpha():
                u = ord(i)
                if h.has_key(u):
                    u = h[u] - m
                    if u < 0:
                        u += 62
                    i = chr(k[u])
            s += i
        return s

    re_remove = re.compile('baidusg,(.*)&word')
    res = re_remove.findall(fake_url)
    if res:
        fake_url = fake_url.replace(res[0], urllib.quote(res[0]))
    song_number, encoded_url, seeds =  GetSeeds(fake_url)
    return Decode(song_number, encoded_url, seeds)


class URLChecker(threading.Thread):
    fastest_url_cond = threading.Condition()
    fastest_url = ''
    failed_url = 0
    total_url = 0
    def __init__(self, fakeurl):
        threading.Thread.__init__(self, name='')
        self.length = 0
        self.url = GetRealMp3URL(fakeurl)
         
    def run(self):
        if not self.url:
            self.etime = 200000
            URLChecker.fastest_url_cond.acquire()
            URLChecker.failed_url += 1
            if URLChecker.failed_url == URLChecker.total_url:
                URLChecker.fastest_url_cond.notify()
            URLChecker.fastest_url_cond.release()
            return
        socket.setdefaulttimeout(10)
        try:
            conn = urllib2.urlopen(self.url)
            length = AnalysysHttpHeader(conn.info().headers)['length']
            if length < 1024 * 1024:
                raise TooSmall("The file is smaller than 1 M, considered as a broken file")
            conn.read(1024) #read 1024 bytes before concluding which is the fastest one.
            URLChecker.fastest_url_cond.acquire()
            if URLChecker.fastest_url != '': # the URLChecker.fastest url was detected already by other threads
                URLChecker.fastest_url_cond.release()
                return
            #print "%s detected the fastest url" % self.getName()
            URLChecker.fastest_url = self.url
            URLChecker.fastest_url_cond.notify()
            URLChecker.fastest_url_cond.release()
        except Exception, e:
            URLChecker.fastest_url_cond.acquire()
            URLChecker.failed_url += 1
            if URLChecker.failed_url == URLChecker.total_url:
                URLChecker.fastest_url_cond.notify()
            URLChecker.fastest_url_cond.release()
            #print "Exception (%s) raised in URLChecker" % e

def GetBestUrl(artist, title):
    """
    arguments:
        artist, unicode
        title, unicode
    """
    cthreads = []
    urls = __getFakeURLs(artist, title)
    URLChecker.total_url = len(urls)
    if URLChecker.total_url == 0:
        return ''
    if URLChecker.total_url == 1:
        return urls[0]

    URLChecker.fastest_url = ''
    URLChecker.failed_url = 0
    for url in urls:
        t = URLChecker(url)
        cthreads.append(t)
        t.start()

    URLChecker.fastest_url_cond.acquire()
    while URLChecker.fastest_url == '' \
        and URLChecker.failed_url < URLChecker.total_url:
        URLChecker.fastest_url_cond.wait()
    URLChecker.fastest_url_cond.release()
    return URLChecker.fastest_url
