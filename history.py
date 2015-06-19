#!/usr/bin/python

"""
    Manage playback history
"""

import os
from config import HISTORY_FILE

def has_file_been_played(filepath):
    if not os.path.isfile(HISTORY_FILE):
        f = open(HISTORY_FILE, "w")
        f.close()
    filepath = filepath.strip()
    f = open(HISTORY_FILE, "r")
    for line in f:
        if line.strip() == filepath:
            f.close()
            return True
    f.close()
    return False

def mark_file_played(filepath):
    if not os.path.isfile(HISTORY_FILE):
        f = open(HISTORY_FILE, "w")
        f.close()
    f = open(HISTORY_FILE, "a")
    f.write("%s\n" % filepath)
    f.flush()
    f.close()


