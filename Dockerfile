FROM resin/rpi-buildpack-deps:wheezy

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
		nano \
		wget \
		python \
		python-pip \
		fonts-freefont-ttf \
		libpcre3 \
		python-pexpect \
		python-webpy \
		libfreetype6 \
		dbus \
		libsmbclient \
		libssh-4 \
		libpcre3-dev \
		libva-dev ca-certificates git-core subversion binutils libva1 libpcre3-dev libidn11-dev libboost1.50-dev libfreetype6-dev libusb-1.0-0-dev \
		libdbus-1-dev libssl-dev libssh-dev libsmbclient-dev  libraspberrypi-dev libraspberrypi0 libraspberrypi-bin \
		fbset \
		htop \
		libnss3 \
		libraspberrypi-bin \
		matchbox \
		psmisc \
		sqlite3 \
		ttf-mscorefonts-installer \
		x11-xserver-utils \
		xinit \
		xwit \
	&& rm -rf /var/lib/apt/lists/*

RUN wget http://omxplayer.sconde.net/builds/omxplayer_0.3.6~git20150505~b1ad23e_armhf.deb \
	&& dpkg -i omxplayer_0.3.6~git20150505~b1ad23e_armhf.deb

COPY . /app

CMD [ "bash", "/app/start.sh" ]
