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

 $Id: httpget.py 1755 2006-12-11 13:01:23Z recordus $
 
 """
 
import threading
import urllib
import urllib2
import os
import time
import sys
from utils import HasLive

class URLUnreachable(Exception):pass
#############################################################################
#
# multiple threads download module starts here
#
#############################################################################
class HttpGetThread(threading.Thread):
    def __init__(self, name, url, filename, range=0):
        threading.Thread.__init__(self, name=name)
        self.url = url
        self.filename = filename
        self.range = range
        self.totalLength = range[1] - range[0] +1
        try:
            self.downloaded = os.path.getsize(self.filename)
        except OSError:
            self.downloaded = 0
        self.percent = self.downloaded/float(self.totalLength)*100
        self.headerrange = (self.range[0]+self.downloaded, self.range[1])
        self.bufferSize = 8192


    def run(self):
        try:
            self.downloaded = os.path.getsize(self.filename)
        except OSError:
            self.downloaded = 0
        self.percent = self.downloaded/float(self.totalLength)*100
        self.bufferSize = 8192
        downloadAll = False
        retries = 1
        while not downloadAll:
            if retries > 10:
                break
            try: 
                self.headerrange = (self.range[0]+self.downloaded, self.range[1])
                request = urllib2.Request(self.url)
                request.add_header('Range', 'bytes=%d-%d' %self.headerrange)
                conn = urllib2.urlopen(request)
                startTime = time.time()
                data = conn.read(self.bufferSize)
                while data:
                    f = open(self.filename, 'ab')
                    f.write(data)
                    f.close()
                    self.time = int(time.time() - startTime)
                    self.downloaded += len(data)
                    self.percent = self.downloaded/float(self.totalLength) *100               
                    data = conn.read(self.bufferSize)
                downloadAll = True
            except Exception, err:
                retries += 1
                time.sleep(1)
                continue

def Split(size,blocks):
    ranges = []
    blocksize = size / blocks
    for i in xrange(blocks-1):
        ranges.append(( i*blocksize, i*blocksize+blocksize-1))
    ranges.append(( blocksize*(blocks-1), size-1))

    return ranges

def GetHttpFileSize(url):
    length = 0
    try:
        conn = urllib.urlopen(url)
        headers = conn.info().headers
        for header in headers:
            if header.find('Length') != -1:
                length = header.split(':')[-1].strip()
                length = int(length)
    except Exception, err:
        print err
        pass
        
    return length

def MyHttpGet(url, output=None, connections=4):
    """
    arguments:
        url, in GBK encoding
        output, default encoding, do no convertion
        connections, integer
    """
    length = GetHttpFileSize(url)
    mb = length/1024/1024.0
    if length == 0:
        raise URLUnreachable
    blocks = connections
    if output:
        filename = output
    else:
        output = url.split('/')[-1]
    ranges = Split(length, blocks)
    names = ["%s_%d" %(filename,i) for i in xrange(blocks)]
    
    ts = []
    for i in xrange(blocks):
        t = HttpGetThread(i, url, names[i], ranges[i])
        t.setDaemon(True)
        t.start()
        ts.append(t)

    live = HasLive(ts)
    startSize = sum([t.downloaded for t in ts])
    startTime = time.time()
    etime = 0
    while live:
        try:
            etime = time.time() - startTime
            d = sum([t.downloaded for t in ts])/float(length)*100
            downloadedThistime = sum([t.downloaded for t in ts])-startSize
            try:
                rate = downloadedThistime / float(etime)/1024
            except:
                rate = 100.0
            progressStr = u'\rFilesize: %d(%.2fM)  Downloaded: %.2f%%  Avg rate: %.1fKB/s' %(length, mb, d, rate)
            sys.stdout.write(progressStr)
            sys.stdout.flush()
            #sys.stdout.write('\b'*(len(progressStr)+1))
            live = HasLive(ts)
            time.sleep(0.2)
        except KeyboardInterrupt:
            print
            print "Exit..."
            for n in names:
                try:
                    os.remove(n)
                except:
                    pass
            sys.exit(1)
            
    print
    print  u'耗时： %d:%d, 平均速度：%.2fKB/s' %(int(etime)/60, int(etime)%60,rate) 

    f = open(filename, 'wb')
    for n in names:
        try:
            f.write(open(n,'rb').read())
            os.remove(n)
        except:
            pass
    f.close()
