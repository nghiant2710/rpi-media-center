#!/usr/bin/python

import os, pexpect, re, subprocess
import threading
from time import time, sleep
from config import AUDIO_FILES, MOVIE_FILES, IMAGE_FILES, BASH_PROMPT, MOVIE_INFO_CMD, MOVIE_INFO_LENGTH_REGEX, MOVIE_PLAY_CMD

def href(s):
    """
    Escapes any unwanted tokens for an href
    """
    return s.replace(" ", "+").replace("\"", "%22").replace("&", "%26").replace("=", "%3D").replace(":", "%3A").replace("?", "%3F")

def is_file_audio(filename):
    if get_extension(filename) in AUDIO_FILES:
        return True
    return False

def is_file_movie(filename):
    if get_extension(filename) in MOVIE_FILES:
        return True
    return False

def is_file_image(filename):
    if get_extension(filename) in IMAGE_FILES:
        return True
    return False

def get_extension(filename):
    fext = filename.lower()
    if fext.find("."):
        return fext[fext.rfind("."):]
    else:
        return ""

def get_next_file(startfile, extension):
    """
    Finds the file after startfile in a directory of extension
    (directory is extracted from startfile and sorted
    alphabetically before locating)
    If no file exists, an empty string is returned.
    """
    wd = str(startfile)
    if wd.find("/") == -1: return ""
    sf = wd[wd.rfind("/")+1:]
    wd = wd[0:wd.rfind("/")]
    dirlist = sorted(os.listdir(wd))
    pos = dirlist.index(sf)
    if pos < (len(dirlist)-1):
        return wd + "/" + dirlist[pos+1]
    return ""

def get_previous_file(startfile, extension):
    """
    Finds the file preceding startfile in a directory of extension
    (directory is extracted from startfile and sorted
    alphabetically before locating).
    If no file exists, an empty string is returned.
    """
    wd = str(startfile)
    if wd.find("/") == -1: return ""
    sf = wd[wd.rfind("/")+1:]
    wd = wd[0:wd.rfind("/")]
    dirlist = sorted(os.listdir(wd))
    pos = dirlist.index(sf)
    if pos > 0:
        return wd + "/" + dirlist[pos-1]
    return ""

class Player(threading.Thread):
    pe = None
    playstarted = 0
    ispaused = False
    isstopped = True
    pausedat = 0
    pausedelapsed = 0
    adjustment = 0
    length = 0
    filename = ""
    filepath = ""
    prevfile = ""
    nextfile = ""
    prevhref = ""
    nexthref = ""

    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = filepath[filepath.rfind("/")+1:]
        self.set_next_prev()

    def run(self):
        # Monitor for the file finishing playback so we can start playing the next file
        while True:
            # Has playback completed?
            if not self.ispaused and not self.isstopped and self.get_elapsed() >= self.get_length() + 1:
                # Is this an audio track and there's a next one to move to?
                if self.nextfile != "" and is_file_audio(self.filename):
                    self.filepath = self.nextfile
                    self.filename = self.nextfile[self.nextfile.rfind("/")+1:]
                    self.set_next_prev()
                    self.play(False) # Parameter prevents this monitor thread being restarted
                    continue
                else:
                    # There's no next file, or this was a movie -
                    # stop the thread and the player
                    self.stop()
                    break
            if self.isstopped:
                break # User has stopped playback, stop the monitor thread
            sleep(2)

    def set_next_prev(self):
        # Grab references to the next and previous files in the same
        # directory as the current playing file
        self.prevhref = ""
        self.nexthref = ""
        self.prevfile = get_previous_file(self.filepath, get_extension(self.filename))
        self.nextfile = get_next_file(self.filepath, get_extension(self.filename))
        if self.prevfile != "": self.prevhref = "play?start=true&to=%s" % href(self.prevfile)
        if self.nextfile != "": self.nexthref = "play?start=true&to=%s" % href(self.nextfile)

    def status_update(self):
        elapsed = self.get_elapsed()
        if self.ispaused: elapsed = self.pausedelapsed
        return "%d|%d|%d|%d|%s|%s|%s" % \
            (elapsed, self.get_length(), 
            self.ispaused and 1 or 0, 
            self.isstopped and 1 or 0, 
            self.filename,
            self.nexthref,
            self.prevhref)

    def play(self, startmonitor = True):
        # Get runtime in seconds
        try:
            # Read both stdout and stderr as omxplayer 2.5 onwards
            # changes the format and 3 onwards sends info stderr
            so, se = subprocess.Popen(MOVIE_INFO_CMD % self.filepath, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
            rt = so
            if se.strip() != "": rt = se
            rv = re.findall(MOVIE_INFO_LENGTH_REGEX, rt)
            if len(rv) == 0: 
                self.length = 0
            # omxplayer 2.5+, Duration format 00:00:00.000
            elif rv[0].find(":") != -1:
                lc = rv[0].split(":")
                if len(lc) == 3:
                    self.length = float(lc[2])
                    self.length += float(lc[1]) * 60
                    self.length += float(lc[0]) * 60 * 60
            # It's an omxplayer 2.4 version, number of seconds
            else:
                self.length = int(float(rv[0].strip()))
        except:
            self.length = 0

        # Start the player going
        self.pe = pexpect.spawn("bash")
        self.pe.expect(BASH_PROMPT)
        cmd = MOVIE_PLAY_CMD % self.filepath
        self.pe.sendline(cmd)
        self.playstarted = time()
        self.ispaused = False
        self.isstopped = False
        self.pausedat = 0
        self.pausedelapsed =0
        self.adjustment = 0

        # Start the monitoring thread if 
        if startmonitor: 
            threading.Thread.__init__(self) 
            self.start()
        return self.status_update()

    def pause(self):
        self.pe.send("p")
        if self.ispaused:
            self.ispaused = False
            # unpause - adjust for amount of time paused
            self.adjustment -= int(time() - self.pausedat)
        else:
            self.pausedelapsed = self.get_elapsed()
            self.ispaused = True
            self.pausedat = time()
        return self.status_update()

    def stop(self):
        try:
            self.pe.send("q")
            self.pe.expect(BASH_PROMPT)
        except:
            pass
        try:
            self.playstarted = 0
            self.ispaused = False
            self.isstopped = True
            self.pausedat = 0
            self.pausedelapsed =0
            self.adjustment = 0
            self.pe.sendline("uname")
            self.pe.expect(BASH_PROMPT)
            self.pe.sendline("exit")
            sleep(1)
            self.pe.kill(0)
        except:
            pass
        return self.status_update()

    def get_elapsed(self):
        """ returns time elapsed in seconds """
        if self.ispaused:
            return self.pausedelapsed
        else:
            return int(time() - self.playstarted) + self.adjustment

    def get_length(self):
        """ returns video length in seconds """
        return self.length

    def rewind_bit(self):
        self.pe.send("\033[D")
        self.adjustment -= 30
        return self.status_update()

    def rewind_lot(self):
        self.pe.send("\033[B")
        self.adjustment -= 600
        return self.status_update()

    def rewind_chapter(self):
        self.pe.send("i")
        return self.status_update()

    def forward_bit(self):
        self.pe.send("\033[C")
        self.adjustment += 30
        return self.status_update()

    def forward_lot(self):
        self.pe.send("\033[A")
        self.adjustment += 600
        return self.status_update()

    def forward_chapter(self):
        self.pe.send("o")
        return self.status_update()

    def volume_up(self):
        self.pe.send("+")
        return self.status_update()

    def volume_down(self):
        self.pe.send("-")
        return self.status_update()

    def info(self):
        if self.pe == None: return "0|0|0|1|%s|%s|%s" % (self.filename, self.nexthref, self.prevhref)
        self.pe.send("z")
        return self.status_update()

    def audio(self):
        self.pe.send("k")
        return self.status_update()

    def subtitles(self):
        self.pe.send("s")
        return self.status_update()


