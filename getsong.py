#!/usr/bin/python
# vim: set fileencoding=utf8 sts=4 sw=4 expandtab :

"""
 Copyright (C) 2006 Xupeng Yun <recordus@gmail.com>
 Modify by Yukang Chen <moorekang@gmail.com> 2011-6-7
 
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

 $Id: getsong.py 1755 2006-12-11 13:01:23Z recordus $

Usage:
    Download mp3 file which matches given artist and/or title.
      
      -h --help         show this help message.
      -d --songsdir     dir of your songs repo.
      -1 --100          download Baidu Top100 new songs. 
      -5 --500          download Biadu Top500 new songs.
      -a --artist       songer
      -t --title        song name
      -v --version      show version info
"""

import os
import sys
import socket
import getopt
import urllib
import urllib2
import threading
from sgmllib import SGMLParser
from modules.songlist import GetArtistAndTitle
from modules.httpget import MyHttpGet, URLUnreachable
from modules.songinfo import GetBestUrl
from modules.utils import HasLive
  
def DownloadSong(artist, title, songsdir='Top100'):
    """
    arguments:
        artist (unicode)
        title (unicode)
        songdir (unicode)
    """
    filename = u'%s-%s.mp3' %(artist, title)
    if title == '':
        return
    if artist == '':
        filename = u'%s.mp3' %title
    filename = filename.encode(sys.getfilesystemencoding())
    songdir = songsdir.encode(sys.getfilesystemencoding())

    if os.path.exists(os.path.join(songsdir, filename)) or os.path.exists(filename):
        print u"已经成功下载《%s - %s》"%(artist, title)
        return
    
    print u"准备下载《%s - %s》..." %(artist, title)
    print u'正在选取最快的URL：'
    #fakeurls = __getFakeURLs(artist, title)
    url = GetBestUrl(artist, title)
    print url.decode('gbk', 'ignore')
    try:
        MyHttpGet(url, filename, 3)
    except URLUnreachable:
        print u"Sorry, 目前并没有为(%s - %s)找到合适的下载资源，\n您可以手动下载或稍候再试。" %(artist, title)
    except KeyboardInterrupt:
        print u'Exiting...'


def DownloadTopSongs(type='100', n=100, dumplist=False):
    try:
        outenc = sys.stdin.encoding
        if type == '100':
            songs = GetArtistAndTitle('http://list.mp3.baidu.com/top/top100.html')
        elif type == '500':
            songs = GetArtistAndTitle('http://list.mp3.baidu.com/top/top500.html')
        elif type == 'topn':                
            songs = GetArtistAndTitle('http://list.mp3.baidu.com/top/top500.html')
            topn = songs.keys()[:n]
            topsongs = {}
            for i in topn:
                topsongs[i] = songs[i]
            songs = topsongs
        elif type == 'file':
            songs = {}
            count = 1
            for line in open('songlist').readlines():
                artist, title = line.strip().split('-')
                info = {}
                info['artist'] = artist.decode(outenc)
                info['title'] = title.decode(outenc)
                print artist, title
                songs[count] = info
                count += 1
            print songs

            
        for rank, info in songs.items():
            artist = info['artist']
            title = info['title']
            if dumplist:
                f=open('songlist', 'a')
                f.write('%s-%s\n' %(artist.encode(outenc), title.encode(outenc)))
                f.close()
                continue
            print
            print u"正在下载第%d首（共%d首) 歌手：%s 曲名：%s" %(rank, len(songs), artist, title)
            DownloadSong(artist, title)
    except KeyboardInterrupt:
        print "Exiting..."

def Help():
    helpstr = """Usage: %s [OPTION]
Download mp3 file which matches given artist and/or title.
  
  -h --help                 show this help message.
  -s --songsdir             dir of your songs repo.
  -1 --100                  download Baidu Top100 new songs. 
  -5 --500                  download Baidu Top500 new songs.
  -n --topn=n               download Baidu Top n new songs.
  -l --listonly             list song info only.
  -f --fromfile=songlist    download the song listed in file.
  -a --artist=artist        songer
  -t --title=title          song name
  -x --From Douban FM      get song list from Douban FM.
  -v --version              show version info
    """%sys.argv[0]
    print helpstr
    sys.exit(0)
    
if __name__ == "__main__":
    
    songsdir='/data/Mp3/Top100'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 
                                   '15hdvfxa:t:d:n:', 
                                   ['100','500','help', 'dumplist', 'version', 'fromfile','fromFM',
                                    'artist=','title=', 'songsdir=', 'topn=']
                                   )
    except getopt.GetoptError:
        Help()
        

    if len(opts) == 0:
        Help()
    
    dumplist = False
    type = ''
    topn = 100
    artist = ''
    titles = []
    for o, a in opts:
        if o in ('-h', '--help'):
            Help()
        if o in ('-s', '--songsdir'):
            songsdir = a
        if o in ('-a', '--artist'):
            artist = a
        if o in ('-t', '--title'):
            titles.append(a)
        if o in ('-d', '--dumplist'):
            dumplist = True
        if o in ('-1', '--100'):
            type='100'
        if o in ('-5', '--500'):
            type='500'
        if o in ('-f', '--fromfile'):
            type='file'
        if o in ('-x','--from douban fm'):
            type='dfm'
        if o in ('-n', '--topn'):
            try:
                n = int(a)
                type = 'topn'
                topn = n
            except:
                print 'Invalid top n'
                sys.exit(1)
        if o in ('-v', '--version'):
            print 'v1.0 by Xupeng Yun <recordus@gmail.com>'
    print type
    if type != '':
        if type=='dfm':
            cwd = os.getcwd()

            list_file = cwd + os.sep + "songlist.txt"
            print list_file
    
            try:
                f = file(list_file,'r')
                for eachLine in f:
                    song = eachLine.strip()
                    print song
                    if not song:
                        continue
                    try:
                        DownloadSong("",song.decode('UTF-8','ignore'))
                    except UnicodeEncodeError:
                        print "error encode"
                    except IndexError:
                        print "error occur"

            except IOError:
                print '歌典列表打开失败，请检查文件是否存在!'
                sys.exit()

        else:
            try:
                DownloadTopSongs(type, topn, dumplist)
                sys.exit(0)
            except KeyboardInterrupt, err:
                print '(Main)Exiting...'
                sys.exit(0)
            
            for title in titles:
                title = title.decode(sys.stdin.encoding, 'ignore')
                artist = artist.decode(sys.stdin.encoding, 'ignore')
                DownloadSong(artist, title)
