#!/usr/bin/python
# vim: set fileencoding=utf8 sts=4 sw=4 expandtab:

"""
 Copyright (C) 2006 Shixin Zeng <zeng.shixin@gmail.com>
 
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

 $Id: httpdown.py 1755 2006-12-11 13:01:23Z recordus $
 
 """

from urllib2 import Request, urlopen, URLError
import sys
import threading
import time

class Job(object):
    def __init__(self, start, end, worker = None, done = False):
        self.start = start #inclusive
        self.end = end #exclusive
        self.worker = worker
        self.done = done

class TermException(Exception):pass
class ConException(Exception):pass

class FileManager(object):
    def __init__(self, filename, filesize):
        self.file = open(filename, 'wb')
        self.filesize = filesize
        self.fl = threading.Lock()

    def write_data(self, pos, data):
        #print "To write data"
        self.fl.acquire()
        try:
            self.file.seek(pos)
            self.file.write(data)
            self.downloaded += len(data)
        finally:
            self.fl.release()

    def __del__(self):
        self.file.close()

class Task(FileManager):
    def __init__(self, filename, filesize):
        FileManager.__init__(self, filename, filesize)
        self.downloaded = 0
        self.jobs = [] #items are Jobs, start is inclusive, end is exclusive
        self.workers = []
        self.wl = threading.Lock()

    def split(self, n):
        length = self.filesize // n
        start = 0
        while start < self.filesize:
            job = Job(start, start + length)
            self.jobs.append(job)
            start += length
        print "len(jobs) = %d " % len(self.jobs)

    def get_job(self, worker):
        self.wl.acquire()
        i = 0
        ret = None
        for x in self.jobs:
            if not x.done:	
                i += 1
        if i < len(self.workers):
            print "Workers is more than jobs"
            for x in self.jobs:
                if x != worker and x.worker.isAlive():
                    x.worker.suspend() #hange all working worker
            x = self.jobs[0].end - self.jobs[0].start
            max = 0
            for i,v in enumerate(self.jobs):
                if v.done:
                    continue
                if v.end - v.start > x:
                    x = v.end - v.start
                    max = i
            if x < 1024:
                ret = None
            else:
                w = self.find_worker(max)
                if w == None:
                    ret = max
                else:
                    try:
                        newjob = Job(self.jobs[w.job].start, self.jobs[w.job].start + x // 2)
                        print "A new job %d - %d is created" % (newjob.start + x // 2, newjob.start + x)
                        try:
                            worker.set_job(newjob)
                            worker.do_open() #might raise exception
                        except:
                            ret = None
                        else:
                            self.jobs.append(Job(newjob.start + x // 2, newjob.start + x))
                            w.change_job(len(self.jobs) -1)
                            ret = len(self.jobs) - 1
                    except TypeError, e:
                        print "w.job = ", w.job
                    except:
                        raise

            self.wl.release()
            for x in self.jobs:
                if x != worker:
                    x.worker.resume()
            return ret

        print "To find out an inactive job"
        for idx, job in enumerate(self.jobs):
            if not self.jobs[idx].done and not self.find_worker(idx):
                self.wl.release()
                return idx

        print "No inactive job left"
        self.wl.release()
        return None


    def find_worker(self, job_idx):
        return self.jobs[job_idx].worker

    def run(self, n = 1):
        self.split(n)
        bytes = self.filesize
        data = "A" * 1024
        while bytes > 0:
            if bytes < len(data):
                data = data[:bytes]
            bytes -= len(data)
            self.file.write(data)

        for x in xrange(n):
            t = WorkerThread(x, self)
            t.setDaemon(True)
            t.start()
            self.workers.append(t)

    def assign_job(self, job_idx, worker):
        self.jobs[job_idx].worker = worker

    def abort_job(self, job_idx):
        self.jobs[job_idx].worker = None

    def done_job(self, job_idx):
        self.jobs[job_idx].done = True

    def done(self):
        for w in self.workers:
            if w.isAlive():
                return False
        return True

    def good(self):
        return self.filesize == self.downloaded

class HttpTask(Task):
    def __init__(self, url, filename):
        self.url = url
        fs = self.get_filesize()
        Task.__init__(self, filename, fs)

    def get_filesize(self):
        try:
            conn = urlopen(self.url)
            headers = conn.info().headers
            for header in headers:
                if header.find('Length') != -1:
                    length = header.split(':')[-1].strip()
                    length = int(length)
        except:
            length = 0

        return length

class WorkerThread(threading.Thread):
    def __init__(self, name, task):
        threading.Thread.__init__(self, name=name)
        self.task = task
        self.bufferSize = 8192
        self.tries = 0
        self.maxtries = 10
        self.job = None
        self.conn = None
        self.cond = threading.Condition()
        self.susp = 0

    def set_job(self, job):
        self.job = job

    def run(self):
        print "Worker %s begin to work" % self.getName()
        while True:
            try:
                self.tries = 0
                self.job = self.task.get_job(self)
                if self.job == None:
                    break
                self.task.assign_job(self.job, self)
                self.do_job()
            except Exception, e:
                print "Error %s" % e
                raise
                break
        print "Worker %s finished his work" % self.getName()

        print "Remove itself from worker list"
        for idx, x in enumerate(self.task.workers):
            if x == self:
                del self.task.workers[idx]
                return

        raise Exception("Can't find worker %s from worker list" % self.getName())

    def do_open(self, start, end):
        if self.conn != None:
            return
        pos = self.task.jobs[self.job].start
        end = self.task.jobs[self.job].end
        request = Request(self.task.url)
        print "To down bytes %d - %d" % (pos, end - 1)
        request.add_header('Range', 'bytes=%d-' % pos)
        self.conn = urlopen(request)

    def do_write(self, pos=0):
        '''
        @brief Read data from self.conn and write to the file starting with the specified postion.
        @param pos the start postion in the file to start to write
        
        @return the next pos to write
        '''
        end = self.task.jobs[self.job].end
        data = self.conn.read(self.bufferSize)
        while data and pos < end:
            self.cond.acquire()
            while self.susp == 1:
                print "Thread %s was suspended" % self.getName()
                self.cond.wait()
                print "Thread %s resume" % self.getName()
            self.cond.release()
            self.task.write_data(pos, data)
            pos += len(data)
            block = self.bufferSize 
            if self.bufferSize > end - pos:
                block = end - pos
            data = self.conn.read(block)
            end = self.task.jobs[self.job].end # may be changed by change_job
        if pos != end:
            raise IOError("unfinished (end - pos = %d)" % (end - pos))
        return pos

    def do_job(self):
        print "Worker %s is working on job %d" % (self.getName(), self.job)
        if self.job == None:
            print "No more job left\n"
            raise TermException
        pos = self.task.jobs[self.job].start
        while True:
            self.tries += 1
            end = self.task.jobs[self.job].end
            try:
                self.do_open(pos, end)
                pos = self.do_write(pos)
            except URLError, e:
                self.task.abort_job(self.job)
                print "URLError(%s)\n" % e
                self.conn.close()
                self.conn = None
                raise TermException
            except IOError, e:
                print "IOError(%s)\n" % e
                if self.tries >= self.maxtries:
                    self.task.abort_job(self.job)
                    self.conn.close()
                    self.conn = None
                    raise TermException
                print "To try once more\n"
                self.conn.close()
            except Exception, e:
                self.task.abort_job(self.job)
                print "Unkown Error(%s)\n" % e
                self.conn.close()
                self.conn = None
                raise TermException
            else:
                print "Worker %s done" % self.getName()
                self.task.done_job(self.job)
                self.conn.close()
                self.conn = None
                break
    def suspend(self):
        self.cond.acquire()
        self.susp = 1
        self.cond.release()

    def resume(self):
        self.cond.acquire()
        if self.susp == 1:
            self.susp = 0
            self.cond.notifyAll()
        self.cond.release()

    def change_job(self, newjob):
        self.job = newjob
        self.tries = 0

if __name__ == "__main__":
    def main():
        url = "http://easynews.dl.sourceforge.net/sourceforge/filezilla/FileZilla_2_2_29_src.zip"
        filename = "test.zip"
        task = HttpTask(url, filename)
        task.run(3)
        ts = time.time()
        while not task.done():
            print "\rDownload bytes: %d of %d bytes in %d seconds" % (task.downloaded, task.filesize, time.time() - ts),
            sys.stdout.flush()
            time.sleep(1)
        if not task.good():
            print "File is corrupted\n"

    main()
