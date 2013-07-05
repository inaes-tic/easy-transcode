AUTOMAKE_OPTIONS = dist-bzip2

SUBDIRS	= bin lib data po

EXTRA_DIST = config.rpath  config.rpath m4/ChangeLog  config.rpath m4/ChangeLog  \
	ChangeLog \
	NEWS \
	AUTHORS \
	RELEASE \
	$(NULL)

DISTCLEANFILES =                \
        intltool-extract        \
        intltool-merge          \
        intltool-update

EXTRA_DIST +=                   \
        intltool-extract.in     \
        intltool-merge.in       \
        intltool-update.in      \
        $(man_MANS)

locale-uninstalled:
	if test -d po; then \
	    $(MAKE) -C po datadir=../$(top_builddir) install; \
	fi

locale-uninstalled-clean:
	@-rm -rf _trial_temp
	@-rm -rf $(top_builddir)/locale


all-local: locale-uninstalled
clean-local: locale-uninstalled-clean

check-integration:
	cd tests; make check-integration

ACLOCAL_AMFLAGS = -I m4
