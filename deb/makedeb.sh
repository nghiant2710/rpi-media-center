#!/bin/sh

cd `dirname $0`

# Clear the image out
rm -rf pimc *.deb

# Remake the paths
mkdir -p pimc/usr/share/lib/pimc
mkdir -p pimc/usr/share/doc/pimc
mkdir -p pimc/usr/lib/pimc
mkdir -p pimc/etc/init.d
mkdir -p pimc/var/cache/pimc
mkdir -p pimc/DEBIAN

# Update the app
cp -rf ../*.py ../static pimc/usr/lib/pimc/

# Add docs
cp ../README pimc/usr/share/doc/pimc

# Create the init.d stop/start script
echo '#!/bin/sh
# /etc/init.d/pimc
### BEGIN INIT INFO
# Provides:          pimc
# Required-Start:    $syslog
# Required-Stop:     $syslog
# Should-Start:      $network
# Should-Stop:       $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start and stop the pi media center server daemon
# Description:       Controls the main pi media center server daemon
### END INIT INFO
DAEMON=/usr/bin/env
ARGS="python /usr/lib/pimc/code.py 55555"
PIDFILE="/var/run/pimc"
WD=/usr/lib/pimc
. /lib/lsb/init-functions
case "$1" in
  start)
    echo "Starting pi media center ..." >&2
    /sbin/start-stop-daemon --start --pidfile $PIDFILE --chdir $WD -b --make-pidfile --exec $DAEMON $ARGS &> /var/log/pimc.log
    ;;
  stop)
    echo "Stopping pi media center ..." >&2
    /sbin/start-stop-daemon --stop --pidfile $PIDFILE --verbose
    ;;
  restart)
    echo "Restarting pi media center ..." >&2
    /sbin/start-stop-daemon --stop --pidfile $PIDFILE --verbose
    /sbin/start-stop-daemon --start --pidfile $PIDFILE --chdir $WD -b --make-pidfile --exec $DAEMON $ARGS &> /var/log/pimc.log
    ;;
  *)
    echo "Usage: /etc/init.d/pimc {start|stop|restart}" >&2
    exit 1
    ;;
esac
exit 0
' > pimc/etc/init.d/pimc
chmod +x pimc/etc/init.d/pimc

# Generate the control file
#echo "Generating control file..."
echo "Package: pimc
Version: `cat ../VERSION`
Section: contrib
Priority: optional
Architecture: all
Essential: no
Depends: python-webpy, python-pexpect, omxplayer (>= 0.3.5), fim
Suggests: fim, omxplayer
Installed-Size: `du -s -k pimc | awk '{print$1}'`
Maintainer: Robin Rawson-Tetley [robin@rawsontetley.org]
Provides: pimc
Description: Smartphone interface to control the raspberry pi
 and play video and audio media." > pimc/DEBIAN/control

# Generate the postinst file
# Puts the init script into default run levels and start the service
echo "#!/bin/sh
update-rc.d pimc defaults
chmod 777 /var/cache/pimc
/etc/init.d/pimc start
" > pimc/DEBIAN/postinst
chmod +x pimc/DEBIAN/postinst

# Generate the prerm file to remove the service 
echo "#!/bin/sh
/etc/init.d/pimc stop
update-rc.d pimc remove
# Don't stop the package manager if these fail
exit 0
" > pimc/DEBIAN/prerm
chmod +x pimc/DEBIAN/prerm

# Build the deb package
dpkg -b pimc pimc_`cat ../VERSION`_all.deb


