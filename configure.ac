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

dnl define PACKAGE_VERSION_* variables
AS_VERSION

dnl can autoconf find the source ?
AC_CONFIG_SRCDIR([bin/zumo.py])

AC_SUBST_FILE(AUTHORS)
AUTHORS=$srcdir/AUTHORS

AM_INIT_AUTOMAKE($PACKAGE, $VERSION)
AC_SUBST(ACLOCAL_AMFLAGS, "-I common/m4")

AS_AC_EXPAND(LIBDIR, $libdir)
AC_MSG_NOTICE(Storing library files in $LIBDIR)

AS_AC_EXPAND(DATADIR, $datadir)
AC_MSG_NOTICE(Storing data files in $DATADIR)

AS_AC_EXPAND(SYSCONFDIR, $sysconfdir)
AC_MSG_NOTICE(Storing configuration files in $SYSCONFDIR)

AS_AC_EXPAND(LOCALSTATEDIR, $localstatedir)
AC_MSG_NOTICE(Using localstatedir $LOCALSTATEDIR)

dnl check for python
AS_PATH_PYTHON(2.5)

dnl ALL_LINGUAS="fr"
GETTEXT_PACKAGE="mbc-zumo"
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], "$GETTEXT_PACKAGE", [Gettext package])
AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL([0.35.0])

CONFIGURED_PYTHONPATH=$PYTHONPATH
AC_SUBST(CONFIGURED_PYTHONPATH)

CONFIGURED_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
AC_SUBST(CONFIGURED_LD_LIBRARY_PATH)

CONFIGURED_GST_PLUGIN_PATH=$GST_PLUGIN_PATH
AC_SUBST(CONFIGURED_GST_PLUGIN_PATH)

AC_CONFIG_FILES([bin/mbc-zumo], [chmod +x bin/mbc-zumo])

dnl output stuff
AC_OUTPUT(
Makefile
bin/Makefile
po/Makefile.in
data/Makefile
data/mbc-zumo.desktop.in
data/ui/Makefile
)
