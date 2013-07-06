AC_PREREQ(2.52)

dnl Note for packagers: see pitivi/check.py for the dependencies

dnl initialize autoconf
dnl when going to/from release please set the nano (fourth number) right !
dnl releases only do Wall, cvs and prerelease does Werror too
AC_INIT(mbc-zumo, 0.1.0,
    github.com/inaes-tic/mbc-zumo,
    mbc-zumo)

dnl initialize automake
AM_INIT_AUTOMAKE

AC_SUBST_FILE(AUTHORS)
AUTHORS=$srcdir/AUTHORS

AM_PATH_PYTHON([2.5])

dnl ALL_LINGUAS="fr"
GETTEXT_PACKAGE="mbc-zumo"
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], "$GETTEXT_PACKAGE", [Gettext package])
AM_GLIB_GNU_GETTEXT

AM_GNU_GETTEXT_VERSION([0.17])
AM_GNU_GETTEXT([external])
IT_PROG_INTLTOOL([0.35.0])

CONFIGURED_PYTHONPATH=$PYTHONPATH
AC_SUBST(CONFIGURED_PYTHONPATH)

CONFIGURED_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
AC_SUBST(CONFIGURED_LD_LIBRARY_PATH)

LIBDIR=$LIBDIR
AC_SUBST(LIBDIR)

DATADIR=data
AC_SUBST(DATADIR)

AC_CONFIG_FILES([bin/mbc-zumo], [chmod +x bin/mbc-zumo])

dnl output stuff
AC_OUTPUT(
Makefile
bin/Makefile
lib/Makefile
lib/configure.py
po/Makefile.in
data/Makefile
data/mbc-zumo.desktop.in
data/ui/Makefile
)
