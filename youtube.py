#!/usr/bin/python

"""
    mini YouTube tool for pimc.
"""

import re, urllib, urllib2, json
from config import YOUTUBE_VIDEO_NAME

URL_FIND = "https://www.youtube.com/results?search_query=%s"
RE_RESULT = r"class=\"yt-lockup-title\"(.+?)</div></li>"
RE_URL = r"href=\"(.+?)\""
RE_TITLE = r"title=\"(.+?)\""
RE_DURATION = r"Duration\: (.+?)<"
RE_DESCRIPTION = r"class=\"yt-lockup-description yt-ui-ellipsis yt-ui-ellipsis-2\" dir=\"ltr\">(.+?)</div"

URL_WATCH = "https://www.youtube.com%s"
RE_YTCONFIG = r"\"args\": {(.+?)}"
RE_FMTURL = r"url=(.+?)\&"

def _res(r):
    if len(r) > 0: 
        s = r[0].strip()
        if s.find("<a") != -1:
            s = s[0:s.find("<a")].strip()
        if type(s) == unicode:
            return s.encode("ascii", "xmlcharrefreplace")
        return s
    return ""

def search(q):
    """
    Searches YouTube and returns a list of dictionaries
    including name and url
    """
    # Submit the query to the find page
    q = q.replace(" ", "+")
    r = urllib2.urlopen(URL_FIND % q).read()

    # Find chunks containing all the results
    results = re.findall(RE_RESULT, r)

    out = []
    for r in results:
        r = r.replace("\n", " ").replace("\r", " ")
        out.append({
            "url": _res(re.findall(RE_URL, r)),
            "title": _res(re.findall(RE_TITLE, r)),
            "duration": _res(re.findall(RE_DURATION, r)),
            "description": _res(re.findall(RE_DESCRIPTION, r))
        })
    return out

def resolve(url):
    """
    Accesses the YouTube page at /watch?xxxxxx, finds the mp4 video link in
    the args javascript object passed to the swf file and returns it
    """
    # Find the video URLs
    r = urllib2.urlopen(URL_WATCH % url).read().replace("\n", " ").replace("\r", " ")
    ytc = _res(re.findall(RE_YTCONFIG, r))
    p = json.loads("{" + ytc + "}")
    fmts = p["url_encoded_fmt_stream_map"]
    link = _res(re.findall(RE_FMTURL, fmts))
    return urllib.unquote(link)

def download(url):
    """
    Downloads a YouTube mp4 video at url and calls it YOUTUBE_VIDEO_NAME
    """
    req = urllib2.urlopen(url)
    CHUNK = 16 * 1024
    fp = open(YOUTUBE_VIDEO_NAME, 'wb')
    while True:
        chunk = req.read(CHUNK)
        if not chunk: break
        fp.write(chunk)
    fp.close()
    return YOUTUBE_VIDEO_NAME

if __name__ == "__main__":
    # Test
    q = "phantom menace"
    r = search(q)
    print "Search '%s'" % q
    assert len(r) > 0
    r = r[0]
    assert r["url"].startswith("/watch")
    assert r["title"] != ""
    assert r["duration"] != ""
    assert r["description"] != ""
    realurl = resolve(r["url"])
    print realurl
    assert realurl != ""
    download(realurl)
    print "Downloaded as %s" % YOUTUBE_VIDEO_NAME

