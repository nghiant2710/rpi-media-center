
all: compile clean

clean:
	rm -f *.pyc

compile:
	pychecker -L 800 -R 20 -J 20 -K 60 -j -b httplib,multiprocessing,threading src/*.py

version:
	# stamp the version in config.py
	sed "s/^VERSION =.*/VERSION = \"`cat VERSION` [`date`]\"/" config.py > configv.py
	mv -f configv.py config.py

dist: version clean
	cd deb && ./makedeb.sh
	cd .. && tar --exclude pimc.tar.gz --exclude .git -czf pimc.tar.gz pimc && mv pimc.tar.gz pimc

archive: dist
	scp pimc.tar.gz robin@netservice:/media/drive1/storage/projects/archive/Python
	scp pimc.tar.gz root@rawsoaa3.miniserver.com:/var/www/rawsontetley.org/oss
	scp deb/pimc_`cat VERSION`_all.deb root@rawsoaa3.miniserver.com:/var/www/rawsontetley.org/oss

updatetest: dist
	scp deb/*.deb pi@netservice:/home/pi/
	ssh pi@netservice "sudo dpkg -i pimc*deb && rm -f pimc*deb"

updaterob: dist
	scp deb/*.deb pi@musicserver:/home/pi/
	ssh pi@musicserver "sudo dpkg -i pimc*deb && rm -f pimc*deb"

updatejon: dist
	scp deb/*.deb pi@192.168.84.33:/home/pi/
	ssh pi@192.168.84.33 "sudo dpkg -i pimc*deb && rm -f pimc*deb"

test: version
	python code.py 55555

