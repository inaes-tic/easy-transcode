all:

install:
	mkdir -p ${DESTDIR}/usr/bin/mbc-transcode
	cp convert.py ${DESTDIR}/usr/bin/mbc-transcode
	mkdir -p ${DESTDIR}/usr/share/applications/
	cp mbc-transcode.desktop ${DESTDIR}/usr/share/applications/
