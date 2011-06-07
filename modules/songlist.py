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

 $Id: songlist.py 1755 2006-12-11 13:01:23Z recordus $
 """
 
import re
import urllib
from sgmllib import SGMLParser

#############################################################################
#
# get artist-title pairs from baidu top songs list
#
#############################################################################
class SongParser(SGMLParser):
    def reset(self):
        SGMLParser.reset(self)
        self.songs = {}
        self.cursong = ''
        self.insong = False
        self.newsong = False
        self.name = ''
        self.currank = 0
        
    def handle_data(self, text):
        txt = text.strip()
        if txt == '':
            return
        #res = re.search('^(\d{1,3})\.$', txt)
        res = re.search('^(\d{1,3})$', txt)
        if res:
            rank = int(res.groups()[0])
            if rank == self.currank + 1 :
                self.currank = rank
                self.cursong = rank
                self.songs[rank] = {}
                self.insong = True
                self.name = 'artist'
        else:
            if self.insong:
                if not self.songs[self.cursong].has_key('title') :
                    self.songs[self.cursong]['title'] = txt.decode('utf8', 'ignore')
                elif not self.songs[self.cursong].has_key('artist') :
                    self.songs[self.cursong]['artist'] = txt.decode('utf8', 'ignore')

                    self.insong = False
   
def GetArtistAndTitle(url):
    html = urllib.urlopen(url).read()
    html = html.decode('gbk', 'ignore').encode('utf8')
    parser = SongParser()
    parser.feed(html)
    songs = parser.songs
        
    return songs    
