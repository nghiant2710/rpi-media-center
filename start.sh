#!/bin/bash

ldconfig

useradd -m pi

gpasswd -a pi video

echo "allowed_users=anybody" > /etc/X11/Xwrapper.config

cp /app/xinitrc /home/pi/.xinitrc;
chown pi: /home/pi/.xinitrc

su - pi -c startx &

rm -rf /data/media
mv /app/media /data/media
cd /app && python code.py 80
