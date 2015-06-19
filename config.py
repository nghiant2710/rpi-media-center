#!/usr/bin/env python
import os

# Where to browse for videos, audio and pictures
MEDIA_ROOT = "/media"

# Play history and IMDB info cache
HISTORY_FILE = "/var/cache/pimc/play_history.txt"
IMDB_CACHE = "/var/cache/pimc/imdb_cache.txt"

# Temporary file for current youtube vid
YOUTUBE_VIDEO_NAME = "/tmp/youtube.mp4"

# Updated by makefile
VERSION = "1.0 [Sat 10 Jan 12:14:50 GMT 2015]"

# Command to run when the power button is clicked
OFF_CMD = "sudo halt"

# Different file types
MOVIE_FILES = [ ".divx", ".mpg", ".avi", ".mp4", ".mkv", ".m4v" ]
AUDIO_FILES = [ ".mp3", ".wav" ]
IMAGE_FILES = [ ".jpg" ]

# Regex to determine a bash prompt in pexpect
BASH_PROMPT = "(.*)[#\\$]"

# Commands for the movie player
MOVIE_INFO_CMD = "omxplayer --info \"%s\""
#MOVIE_INFO_LENGTH_REGEX = "length (.*)" # omxplayer <= 2.4
MOVIE_INFO_LENGTH_REGEX = "Duration: (.+?)," # omxplayer >= 2.5
MOVIE_PLAY_CMD = "omxplayer -b -o hdmi \"%s\""

# Commands for image viewing
VIEW_IMAGE_CMD = "fim -a \"%s\" &"
VIEW_IMAGE_CLOSE_CMD = "pkill -f fim"

# x86 testing with mplayer/totem on GNOME - override with 
# these values if we're not on an arm system
if os.popen("uname -a", "r").read().find("armv6l") == -1:
    MOVIE_INFO_CMD = "mplayer -identify -frames 0 \"%s\""
    MOVIE_PLAY_CMD = "totem \"%s\""
    MOVIE_INFO_LENGTH_REGEX = "ID_LENGTH=(.*)"
    VIEW_IMAGE_CMD = "geeqie \"%s\" &"
    VIEW_IMAGE_CLOSE_CMD = "pkill -f geeqie"

