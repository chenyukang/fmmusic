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

 $Id: utils.py 1755 2006-12-11 13:01:23Z recordus $
 """

def HasLive(ts):
    for t in ts:
        if t.isAlive():
            return True
    return False

def AnalysysHttpHeader(headers):
    ret = {}
    for header in headers:
	if header.find('Length') != -1:
	    length = header.split(':')[-1].strip()
	    ret['length'] = int(length)
    return ret
