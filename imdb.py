#!/usr/bin/python

"""
    mini IMDB search tool for pimc.
    Used imdbpy previously, but it's far too heavyweight
    (and slow!) for what we need.
"""

import os, re, urllib2
from config import IMDB_CACHE

URL_FIND = "http://www.imdb.com/find?ref_=nv_sr_fn&q=%s&s=all"
RE_TT = r"href=\"\/title\/tt(\d+?)\/"

URL_TITLE = "http://www.imdb.com/title/tt%s/?ref_=fn_al_tt_1"
RE_TITLE = r"property=\'og:title' content=\"(.+?)\""
RE_DESCRIPTION = r"property=\"og:description\" content=\"(.+?)\""
RE_PLOT = r"itemprop=\"description\">(.+?)</p>"
RE_COVER = r"property=\'og:image\' content=\"(.+?)\""
COVER_SIZE = "V1_SY80_CR91,0,80,80_AL.jpg"
RE_RATING = r"rated this (.+?)\/1"
RE_DURATION = r"<time.+?>(.+?)</time>"
RE_YEAR = r"\((\d+?)\)"

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
    Searches IMDB for the movie "q" and returns
    a dictionary of values, including 
    title, rating, plotoutline and coverurl
    """
    # Submit the query to the find page
    q = q.replace(" ", "+")
    r = urllib2.urlopen(URL_FIND % q).read()

    # Extract the first title in the result
    tt = re.findall(RE_TT, r)
    if len(tt) == 0: return None

    # If we have one, open the title page
    r = urllib2.urlopen(URL_TITLE % tt[0]).read().replace("\n", " ")
    r = unicode(r, "utf-8")

    # Extract all the bits
    title = _res(re.findall(RE_TITLE, r))
    year = _res(re.findall(RE_YEAR, title))
    if title.find("(") != -1: 
        title = title[0:title.find("(")].strip()

    plotoutline = _res(re.findall(RE_PLOT, r))

    description = _res(re.findall(RE_DESCRIPTION, r))
    director = ""
    cast = ""
    if description != "":
        descbits = description.split(".", 2)
        if len(descbits) == 3:
            director = descbits[0].strip() + "."
            cast = descbits[1].strip() + "."

    coverurl = _res(re.findall(RE_COVER, r))
    if coverurl.find("_V1_") != -1:
        coverurl = coverurl[0:coverurl.find("V1")] + COVER_SIZE

    rating = _res(re.findall(RE_RATING, r))
    if rating.find(".") == -1 and rating != "":
        rating += ".0"

    duration = _res(re.findall(RE_DURATION, r))
        
    summary = "%s %s %s (%s, %s)" % (plotoutline, director, cast, duration, year)

    rv = {
        "movieid":      _res(tt),
        "rating":       rating,
        "director":     director,
        "cast":         cast,
        "plotoutline":  plotoutline,
        "summary":      summary,
        "coverurl":     coverurl,
        "title":        title,
        "duration":     duration,
        "year":         year
    }
    return rv

def movie_info(filepath, filename):
    """
    Contacts IMDB to get some info about the movie and returns
    some info to show in the browser.
    """
    # Does this look like a TV show? Something like S01E01
    if len(re.findall(r"S\d\dE\d\d", filename)) > 0:
        print "%s looks like TV show, skipping info" % filename
        return ("", "", "", "")
    # Is this a sample video
    if filename.lower().startswith("sample."):
        print "%s looks like a sample vid, skipping info" % filename
        return ("", "", "", "")
    # Are we in a subdirectory of TV?
    if filepath.lower().find("/tv/") != -1:
        print "%s path contains /tv/, skipping info" % filepath
        return ("", "", "", "")
    # If our cache doesn't exist, create it
    if not os.path.isfile(IMDB_CACHE):
        f = open(IMDB_CACHE, "w")
        f.close()
    # Do we have a cache entry for this file?
    title = ""
    outline = ""
    rating = ""
    cover = ""
    got_cache = False
    f = open(IMDB_CACHE, "r")
    for l in f.readlines():
        if l.startswith(filename):
            print "imdb cache: %s" % title
            filename, title, outline, rating, cover = l.split("||")
            got_cache = True
            break
    f.close()
    # No, search for it in IMDB
    if not got_cache:
        # Cack that appears in pirated film filenames - punctuation,
        # resolutions, formats, encodings and release groups
        JUNKFILEBITS = ( 
            "-", "{", "}", "(", ")", "[Eng]", "[", "]", \
            "720p", "1080p", "HDTV", "WS", "TS", "5.1", "DTS", "WEB-DL", "IMAX", \
            "BluRay", "bluray", "BDRip", "bdrip", "BrRip", "brrip", "BRRip", \
            "DvDRip", "DvDrip", "DvdRip", "DVDRip", "DVDrip", "DVDRIP", "DVDSCR", \
            "WEBRip", "HDRIP", "HDTV", \
            "x264", "X264", "h264", "H264", "XVID", "XviD", "XViD", "Xvid", "xvid", "DivX", "divx", "AC3", "AAC", "MP3", "R5", "6ch", \
            "Jaybob", "YIFY", "MiSTERE", "MAXSPEED", "Atlas47", "AMIABLE", \
            "UNRATED", "unrated", "www.torentz.3xforum.ro", "SiC", "LiNE", "aXXo", "P2P", \
            "sparks", "Grimmo", "anoXmous", "FxM", "juggs", "s4a", "Judas", "iND", "KLAXXON", \
            "P4DGE", "www.superfundo.org", "ACAB", "RARBG", "BiDA", "EBX", "RETAIL", "PLAYNOW", "EDITION", "PublicHD", \
            "FTW", "Rets", "BTSFilms"
        )
        q = filename
        if q.rfind(".") != -1: q = q[0:q.rfind(".")]
        # Remove anything we consider filename junk from the query
        for j in JUNKFILEBITS:
            q = q.replace(j, "")
        q = q.replace("_", " ").replace(".", " ").lower().strip()
        # Remove years from the query
        # q = re.sub(r"\d\d\d\d", "", q)
        m = search(q)
        # Got a result?
        if m is not None:
            title = m["title"]
            outline = m["summary"]
            cover = m["coverurl"]
            rating = m["rating"]
            print "found IMDB result: %s (%s), %s" % (title, rating, outline)
            # Add this to the cache for this filename
            f = open(IMDB_CACHE, "a")
            f.write("%s||%s||%s||%s||%s\n" % (filename, title, outline, rating, cover))
            f.flush()
            f.close()
        else:
            print "IMDB found no results for '%s'" % q
            # Remember we got no hits in future
            f = open(IMDB_CACHE, "a")
            f.write("%s||%s||%s||%s||%s\n" % (filename, title, outline, rating, cover))
            f.flush()
            f.close()
    # Construct some HTML from our values
    return (title, outline, rating, cover)

if __name__ == "__main__":
    # Test
    r = search("edge of tomorrow")
    print "Search 'edge of tomorrow':\n%s" % r
    assert r["rating"] != ""
    assert r["plotoutline"].startswith("A military")
    assert r["movieid"] == "1631867"
    assert r["title"] == "Edge of Tomorrow"
    assert r["coverurl"].startswith("http")
    assert r["year"] == "2014"
    assert r["duration"] == "113 min"
    assert r["director"].startswith("Directed by Doug")
    assert r["cast"].startswith("With Tom")

