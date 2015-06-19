/*jslint browser: true, forin: true, eqeq: true, white: true, sloppy: true, vars: true, nomen: true */
/*global $, jQuery, alert, player: true */

player = {

    time_of_last_update: null,
    elapsed_in_secs: 0,
    movie_length: 0,
    is_stopped: true,
    is_paused: false,
    play_title: "",
    next_href: "",
    prev_href: "",
    timer: false,

    /** Formats a number of seconds as HH:MM:SS */
    format_time: function(secs) {
        var r = secs, h = 0, m = 0, s = 0, x = "";
        if (r > 3600) {
            h = Math.floor(r / 3600);
            r = r - (h * 3600);
        }
        if (r > 60) {
            m = Math.floor(r / 60);
            r = r - (m * 60);
        }
        s = r;
        if (h < 10) { x = "0"; }
        x += h + ":";
        if (m < 10) { x += "0"; }
        x += m + ":";
        if (s < 10) { x += "0"; }
        x += s;
        return x;
    },

    /**
     * Reloads the on screen widgets based on updated state
     */
    update_state: function() {
        
        // Are we stopped? hide the clock and disable all
        // but the play button
        if (player.is_stopped) {
            $("#minfo").hide();
            $(".pb").prop("disabled", true);
            $("#mplay").prop("disabled", false);
        }
        else {
            // We're playing, show the clock and enable
            // buttons
            $("#minfo").show();
            $(".pb").prop("disabled", false);
            $("#mplay").prop("disabled", true);
        }

        // Are we paused? update the pause button text
        if (player.is_paused) {
            $("#mpause").html("Unpause");
        }
        else {
            $("#mpause").html("Pause");
        }

        // If this isn't an audio track, don't bother
        // showing next and previous file buttons at all
        // since the backend won't do continuous playback
        // for anything but audio (on purpose)
        if (player.play_title.indexOf(".mp3") == -1) {
            $("#mnextfile").hide();
            $("#mprevfile").hide();
        }
        else {
            // Do we have a next href and previous href?
            // If so, enable the buttons accordingly
            if (player.next_href) {
                $("#mnextfile").prop("disabled", false);
            }
            else {
                $("#mnextfile").prop("disabled", true);
            }
            if (player.prev_href) {
                $("#mprevfile").prop("disabled", false);
            }
            else {
                $("#mprevfile").prop("disabled", true);
            }
        }

        // update the on screen clock and title if we aren't paused or stopped
        if (!player.is_paused && !player.is_stopped && player.time_of_last_update) {

            // calculate elapsed time, format and display it
            var csecs = new Date() - player.time_of_last_update;
            csecs /= 1000;
            csecs = Math.floor(csecs);
            var newelapsed = csecs + player.elapsed_in_secs;
            var formatlen = player.format_time(player.movie_length);
            var formatelapsed = player.format_time(newelapsed);
            $("#minfo").html(formatelapsed + " / " + formatlen);
            $("#pagetitle").text(player.play_title);

            // If the elapsed time now exceeds length, wait a few seconds and
            // force a refresh as it could have started to play the next file now.
            if (newelapsed > player.movie_length && player.movie_length > 0) {
                setTimeout(function() {
                    player.acall("info");
                }, 2000);
            }
        }

        // Set our timer going if it isn't already
        if (!player.timer) {
            player.timer = setInterval(player.update_state, 1000);
        }
    },

    /**
     * Send a command to the backend. The response should be a
     * delimited list of elapsed time secs, length in secs, paused (0 or 1),
     * stopped (0 or 1) and title of playing file
     */
    acall: function(cmd, cbsuccess) {
        $.ajax({ type: "GET", url: "mctrl", data: "cmd=" + cmd, dataType: "text",
            success: function(timeclock) {
                if (cbsuccess) { cbsuccess(); }
                var bits = timeclock.split("|");
                player.elapsed_in_secs = parseInt(bits[0], 10);
                player.movie_length = parseInt(bits[1], 10);
                player.is_paused = parseInt(bits[2], 10) == 1;
                player.is_stopped = parseInt(bits[3], 10) == 1;
                player.play_title = bits[4];
                player.next_href = bits[5];
                player.prev_href = bits[6];
                player.time_of_last_update = new Date();
                player.update_state();
            },
            error: function(jqxhr, textstatus, response) {
                alert(response);
            }
        });
    },

    /**
     * Bind events to our on screen widgets
     */
    bind: function() {
        $("#mplay").click(function() {
            player.is_stopped = false;
            player.acall("play");
        });
        $("#mstop").click(function() {
            player.is_stopped = true;
            player.acall("stop");
        });
        $("#mpause").click(function() { 
            player.is_paused = !player.is_paused;
            player.acall("pause");
        });
        $("#mnextfile").click(function() {
            if (player.next_href) {
                window.location = player.next_href;
            }
        });
        $("#mprevfile").click(function() {
            if (player.prev_href) {
                window.location = player.prev_href;
            }
        });
        $("#minfo").click(function() { player.acall("info"); });
        $("#msubtitles").click(function() { player.acall("subtitles"); });
        $("#maudio").click(function() { player.acall("audio"); });
        $("#mrwbit").click(function() { player.acall("rwbit"); });
        $("#mffbit").click(function() { player.acall("ffbit"); }); 
        $("#mffchap").click(function() { player.acall("ffchap"); }); 
        $("#mrwchap").click(function() { player.acall("rwchap"); }); 
        $("#mrwlot").click(function() { player.acall("rwlot"); });
        $("#mfflot").click(function() { player.acall("fflot"); });
        $("#mvolup").click(function() { player.acall("volup"); });
        $("#mvoldn").click(function() { player.acall("voldn"); });
    },

    /**
     * Initialise the player
     */
    init: function(autostart) {
        // Bind events before we go any further
        player.bind();
        // Get an update on where we are
        player.acall("info");
        // If autostart is on, start playing immediately
        if (autostart) {
            player.acall("play");
        }
    }
};

