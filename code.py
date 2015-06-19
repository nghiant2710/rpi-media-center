#!/usr/bin/python
"""
    pimc

    A web-based remote control for media on the
    raspberry pi. Uses jquery mobile for tablets/phones.

    Copyright(c)2013-2015, R. Rawson-Tetley
    
    This program is covered by the terms of the GNU General Public Licence v3.
    See the file COPYING for details.

"""

import web, os, sys, urllib2
import history, id3, imdb, omxplayer #, youtube
from config import MEDIA_ROOT, OFF_CMD, VIEW_IMAGE_CMD, VIEW_IMAGE_CLOSE_CMD, VERSION

PATH = os.path.dirname(__file__) + os.sep
sys.path.append(PATH)

player = None
urls = (
    "/", "index",
    "/index", "index",
    "/cd", "cd",
    "/image", "image",
    "/folder_image", "folder_image",
    "/remote_image", "remote_image",
    "/play", "play",
    "/mctrl", "mctrl",
    "/poweroff", "poweroff"
)
app = web.application(urls, globals())
render = web.template.render("%stemplates" % PATH, globals={
    })

application = app.wsgifunc()

def header(allowzoom = False):
    zoom = ""
    if not allowzoom: zoom = ", maximum-scale=1, user-scalable=0"
    return """
        <!DOCTYPE html>
        <html>
        <head>
        <title>
        Pi Media Center
        </title>
        <meta name="viewport" content="width=device-width, initial-scale=1%s"> 
        <link rel="stylesheet" href="http://code.jquery.com/mobile/1.4.2/jquery.mobile-1.4.2.min.css" />
        <script type="text/javascript" src="http://code.jquery.com/jquery-1.11.1.min.js"></script>
        <script type="text/javascript" src="http://code.jquery.com/mobile/1.4.2/jquery.mobile-1.4.2.min.js"></script>
        <script type="text/javascript" src="static/player.js"></script>
        </head>
        <body>
        """ % zoom

def footer():
    return """
        <div data-role='page' id='power'>
        <div data-role='header'><h1>Power Down</h1></div>
        <div data-role='content'>
        <p>Are you sure you want to power down?</p>
        <a href="poweroff" data-role='button' data-icon='power' data-ajax='false' data-theme='b'>Power Down</a>
        <a href="#" data-role='button' data-icon='carat-l' data-rel='back' data-theme='a'>Cancel</a>
        </div>
        </div>
        <div data-role='page' id='about'>
        <div data-role='header'><h1>About</h1></div>
        <div data-role='content'>
        <p style="text-align: center">Pi Media Center<br/><b>%s</b><br/>
        Copyright(c) 2013-2015, R. Rawson-Tetley<br/>
        See the file COPYING for redistribution licensing (GPLv3)
        </p>
        <a href="#" data-role='button' data-icon='carat-l' data-rel='back' data-theme='a'>Back</a>
        </div>
        </div>
        </body>
        </html>
        """ % VERSION

def href(s):
    """
    Escapes any unwanted tokens for an href
    """
    return s.replace(" ", "+").replace("\"", "%22").replace("&", "%26").replace("=", "%3D").replace(":", "%3A").replace("?", "%3F")

def page_header(title, pageid):
    return """
        <div data-role='page' id='%s'>
        <div data-role='header'>
        <div class='ui-btn-left'>
        <a href='#power' data-rel='dialog' data-role='button' data-icon='power' data-theme='b' data-iconpos='notext'>Off</a>
        <a href='#about' data-rel='dialog' data-role='button' data-icon='info' data-theme='b' data-iconpos='notext'>About...</a>
        </div>
        <h1 id="pagetitle">%s</h1><a href='index' class='ui-btn-right' data-icon='home' data-iconpos='notext'data-theme='b'>Home</a></div>
        <div data-role='content'>
        """ % (pageid, title)

def page_footer():
    return "</div></div>"

def current_dir(cwd):
    nowplaying = ""
    if player != None and not player.isstopped:
        icon = "video"
        if omxplayer.is_file_audio(player.filepath): icon = "audio"
        nowplaying = """
            <a data-ajax='false' data-role="button" data-icon='%s' href=\"play?to=%s\">Now playing: %s</a>
            """ % (icon, href(player.filepath), player.filename)
    cwdname = cwd[cwd.rfind("/")+1:]
    s = page_header(cwdname, "browse")
    s += nowplaying
    s += "<ul data-role='listview' data-filter='true'>"
    if cwd != MEDIA_ROOT:
        backto = href(cwd[0:cwd.rfind("/")])
        s += "<li data-icon='arrow-l'><a data-transition='slide' href=\"cd?to=%s\">[back to %s]</a></li>\n" % (backto, backto)
    for fname in sorted(os.listdir(cwd)):
        filepath = cwd + "/" + fname
        uname = href(filepath)
        showhd = ""
        shownew = ""
        showtheme = "a"
        # directory
        if os.path.isdir(filepath):
            # does the directory contain a "folder.jpg" and at least one mp3? If so,
            # show the folder.jpg as the thumbnail and the album from ID3 as the
            # name with the artist as the smaller text.
            fjpg = filepath + "/folder.jpg"
            album = ""
            artist = ""
            for f in os.listdir(filepath):
                if f.lower().endswith(".mp3"):
                    tag = id3.ID3(filepath + "/" + f)
                    if tag.artist != "": artist = tag.artist
                    if tag.album != "": album = tag.album
                    break
            if os.path.exists(fjpg) and artist != "" and album != "":
                s += "<li><a data-transition='slide' href=\"cd?to=%s\"><img src='folder_image?filepath=%s' /><h2>%s</h2><p>%s</p></a></li>\n" % (uname, href(fjpg), album, artist)
            else:
                s += "<li><a data-transition='slide' href=\"cd?to=%s\">%s</a></li>\n" % (uname, fname)
        # file
        else:
            if omxplayer.is_file_movie(fname):
                # Show a new icon for unwatched movies
                if not history.has_file_been_played(filepath):
                    shownew = " <img src='static/new.png' class='ui-li-icon' border='0' />"
                    showtheme = "a"
                # Show an HD icon for movie files over 1.2GB
                if os.path.getsize(filepath) > int((1024 * 1024 * 1024) * 1.2):
                    showhd = " <img src='static/hd.png' class='ui-li-icon' border='0' /> "
                # Grab IMDB info for the movie
                title, outline, rating, cover = imdb.movie_info(filepath, fname)
                if cover != "":
                    cover = "remote_image?url=%s" % cover
                # If we have IMDB info, show the title, cover thumbnail and rating
                if title != "":
                    s += "<li data-theme='%s' data-icon='video'><a data-transition='slide' data-ajax='false' href=\"play?to=%s\"><img src='%s' /><h2>%s %s%s (%s)</h2><p style='white-space: normal'>%s</p></a></li>\n" % (showtheme, uname, cover, shownew, showhd, title, rating, outline)
                else:
                    s += "<li data-theme='%s' data-icon='video'><a data-transition='slide' data-ajax='false' href=\"play?to=%s\">%s%s</a></li>\n" % (showtheme, uname, fname, shownew)
            elif omxplayer.is_file_audio(fname):
                showname = fname
                if filepath.lower().endswith(".mp3"):
                    tag = id3.ID3(filepath)
                    if tag.title != "":
                        showname = "<h2>%02d %s</h2><p>%s / %s (%s)</p>" % (tag.track is not None and tag.track or 0, tag.title, tag.artist, tag.album, tag.year)
                s += "<li data-theme='%s' data-icon='audio'><a data-transition='slide' data-ajax='false' href=\"play?to=%s\">%s</a></li>\n" % (showtheme, uname, showname)
            elif omxplayer.is_file_image(fname):
                thumb = "<img src='folder_image?filepath=%s' />" % filepath
                s += "<li data-theme='%s' data-icon='camera'><a data-transition='slide' data-ajax='false' href=\"image?to=%s\">%s%s</a></li>\n" % (showtheme, uname, thumb, fname)
    s += "</ul>"
    s += page_footer()
    return s

class index:
    def GET(self):
        web.header("Content-Type", "text/html")
        web.header("Cache-Control", "no-cache")
        s = header()
        # TODO: Landing page with media link to root and youtube
        s += current_dir(MEDIA_ROOT)
        s += footer()
        return s

class cd:
    def GET(self):
        web.header("Content-Type", "text/html")
        web.header("Cache-Control", "no-cache")
        global player
        data = web.input(to = "")
        s = header()
        s += current_dir(data.to)
        s += footer()
        return s

class image:
    def GET(self):
        web.header("Content-Type", "text/html")
        data = web.input(to = "", fname = "")
        toshow = data.to
        fname = data.fname
        if toshow != "":
            # Hide the viewer if we were displaying an image
            os.system(VIEW_IMAGE_CLOSE_CMD)
            # Find the next and previous images
            prev_file = omxplayer.get_previous_file(toshow, ".jpg")
            prev_template = '<div class="ui-block-b"><a data-role="button" data-icon="arrow-l" data-ajax="false" href="image?to=%s">Prev</a></div>'
            prev_link = '<div class="ui-block-b"></div>'
            if prev_file != "": prev_link = prev_template % prev_file
            next_file = omxplayer.get_next_file(toshow, ".jpg")
            next_link = ""
            next_template = '<div class="ui-block-c"><a data-role="button" data-icon="arrow-r" data-ajax="false" href="image?to=%s">Next</a></div>'
            if next_file != "": next_link = next_template % next_file
            # Output the page
            s = header(True)
            s += page_header(toshow, "imageview")
            s += """
                <div class="ui-grid-b">
                <div class="ui-block-a"><a data-role="button" data-icon="carat-l" data-ajax="false" href="cd?to=%s">Back</a></div>
                %s
                %s
                </div>
                <img width="100%%" src="image?fname=%s" />
                """ % (toshow[0:toshow.rfind("/")], prev_link, next_link, toshow)
            s += page_footer()
            s += footer()
            # Open the image on the pi/tv
            os.system(VIEW_IMAGE_CMD % toshow)
            return s
        elif fname != "":
            f = open(fname, "r")
            s = f.read()
            f.close()
            web.header("Content-Type", "image/jpeg")
            return s

class folder_image:
    def GET(self):
        data = web.input(filepath = "")
        if data.filepath != "":
            f = open(data.filepath, "rb")
            imdata = f.read()
            f.close()
            web.header("Content-Type", "image/jpeg")
            web.header("Cache-Control", "max-age=8640000") # Don't refresh this image for 100 days
            return imdata
        raise web.HTTPError("invalid file path")

class remote_image:
    def GET(self):
        data = web.input(url = "")
        if data.url == "":
            f = open("static/blank.png")
            b = f.read()
            f.close()
            web.header("Content-Type", "image/png")
            return b
        else:
            imdata = urllib2.urlopen(data.url).read()
            web.header("Content-Type", "image/jpeg")
            web.header("Cache-Control", "max-age=8640000") # Don't refresh this image for 100 days
            return imdata

class play:
    def GET(self):
        web.header("Content-Type", "text/html")
        web.header("Cache-Control", "no-cache")
        global player
        data = web.input(to = "", start = "false")
        toplay = data.to
        start = data.start

        # Hide the viewer if we were displaying an image
        os.system(VIEW_IMAGE_CLOSE_CMD)

        if player is not None and toplay == player.filepath:
            # We're being told to play the thing already playing, do nothing
            pass

        elif player is not None:
            # Something is already going and it's not what was requested, stop it
            player.stop()
            player = omxplayer.Player(toplay)

        elif player is None:
            # First run through, create the player for this file
            player = omxplayer.Player(toplay)

        s = header()
        s += page_header(player.filename, "play")
        s += """
            <button data-theme="a" data-icon='info' id="minfo" class="pb">Loading...</button>
            <div data-role="controlgroup">
            <button data-theme="a" data-icon='carat-r' id="mplay" class="pb">Play</button>
            <button data-theme="a" data-icon='recycle' id="mpause" class="pb">Pause</button>
            <button data-theme="a" data-icon='carat-l' id="mstop" class="pb">Stop</button>
            </div>
            <div class="ui-grid-a">
            <div class="ui-block-a"><button data-theme="a" data-icon='comment' id="msubtitles" class="pb">Subtitles</button></div>
            <div class="ui-block-b"><button data-theme="a" data-icon='audio' id="maudio" class="pb">Track #</button></div>
            </div>
            <div class="ui-grid-a">
            <div class="ui-block-a"><button data-theme="a" data-icon='minus' id="mvoldn" class="pb">Vol-</button></div>
            <div class="ui-block-b"><button data-theme="a" data-icon='plus' id="mvolup" class="pb">Vol+</button></div>
            </div>
            <div class="ui-grid-a" >
            <div class="ui-block-a"><button data-theme="a" data-icon='back' id="mrwbit" class="pb">-30s</button></div>
            <div class="ui-block-b"><button data-theme="a" data-icon='forward' id="mffbit" class="pb">+30s</button></div>
            <div class="ui-block-a"><button data-theme="a" data-icon='back' id="mrwlot" class="pb">-10m</button></div>
            <div class="ui-block-b"><button data-theme="a" data-icon='forward' id="mfflot" class="pb">+10m</button></div>
            <!--<div class="ui-block-a"><button data-theme="a" data-icon='back' id="mffchap" class="pb">-Chap</button></div>-->
            <!--<div class="ui-block-b"><button data-theme="a" data-icon='forward' id="mrwchap" class="pb">+Chap</button></div>-->
            <div class="ui-block-a"><button data-theme="a" data-icon='arrow-l' id="mprevfile">&lt;&lt;</button></div>
            <div class="ui-block-b"><button data-theme="a" data-icon='arrow-r' id="mnextfile">&gt;&gt;</button></div>
            </div>
            <script type="text/javascript">
                $(document).bind('pagecreate', function(event) {
                    player.init(%(auto_start)s);
                });
            </script>
            """ % {
                "title": player.filename,
                "auto_start": start
            }
        s += page_footer()
        s += footer()
        return s

class mctrl:
    def GET(self):
        global player
        data = web.input(cmd = "")
        cmd = data.cmd
        web.header("Content-Type", "text/plain")
        web.header("Cache-Control", "no-cache")
        if player is None: return "0|0|0|1|||"
        if cmd == "play":
            if omxplayer.is_file_movie(player.filename) and not history.has_file_been_played(player.filepath):
                history.mark_file_played(player.filepath)
            return player.play()
        elif cmd == "pause":
            return player.pause()
        elif cmd == "stop":
            return player.stop()
        elif cmd == "rwbit":
            return player.rewind_bit()
        elif cmd == "rwlot":
            return player.rewind_lot()
        elif cmd == "rwchap":
            return player.rewind_chapter()
        elif cmd == "ffbit":
            return player.forward_bit()
        elif cmd == "fflot":
            return player.forward_lot()
        elif cmd == "ffchap":
            return player.forward_chapter()
        elif cmd == "volup":
            return player.volume_up()
        elif cmd == "voldn":
            return player.volume_down()
        elif cmd == "info":
            return player.info()
        elif cmd == "subtitles":
            return player.subtitles()
        elif cmd == "audio":
            return player.audio()

class poweroff:
    def GET(self):
        web.header("Content-Type", "text/html")
        web.header("Cache-Control", "no-cache")
        s = header()
        s += page_header("Power Down", "poweroff")
        s += "<p>Powering down...</p>"
        s += page_footer()
        os.system(OFF_CMD)
        return s

if __name__ == "__main__":
    app.run()
    if player != None: player.stop()

