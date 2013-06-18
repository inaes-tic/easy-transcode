#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango

import gettext
import subprocess
import re
import os

gettext.bindtextdomain('easy-transcode')
gettext.textdomain ('easy-transcode')
_ = gettext.gettext

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)

try:
    print "got melt from environ: " + os.environ['MELT_BINARY']
except:
    os.environ['MELT_BINARY'] = 'melt'

DRAG_ACTION = Gdk.DragAction.COPY

def which(file):
    for path in os.environ["PATH"].split(":"):
        if os.path.exists(path + "/" + file):
                return path + "/" + file

    raise ("ENOENT")

class DragDropWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=_("Easy Transcode Tool"))

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.drop_area    = DropArea(self)
        self.dropvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        hbox  = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label()
        label.set_markup ("<b>" + _("Destination") + ": </b>")
        self.filechooser = Gtk.FileChooserButton ()
        self.filechooser.set_uri ('file://' + os.environ['PWD'])
        self.filechooser.set_title (_("Destination Folder"))
        self.filechooser.set_action (Gtk.FileChooserAction.SELECT_FOLDER)

        self.filechooser.connect("file-set", self.on_file_set)
        self.filechooser.set_current_folder ("~/")

        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.filechooser, True, True, 0)

        self.dropvbox.pack_start(self.drop_area, True, True, 0)
        self.dropvbox.pack_start(hbox, False, False, 0)

        self.soxvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.soxvbox.set_no_show_all(True)
        self.soxprogress  = Gtk.ProgressBar()
        self.soxprogress.set_show_text (True)

        self.convvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.convvbox.set_no_show_all(True)
        self.convprogress = Gtk.ProgressBar()
        self.convprogress.set_show_text (True)

        self.sox_cmd_label  = Gtk.Label()
        self.sox_cmd_label.set_property ('ellipsize', Pango.EllipsizeMode.END)
        self.conv_cmd_label = Gtk.Label()
        self.conv_cmd_label.set_property ('ellipsize', Pango.EllipsizeMode.END)

        label = Gtk.Label()
        label.set_markup ('<b>' + _("Audio Normalization") + '</b>')
        self.soxvbox.pack_start(label, False, True, 0)
        self.soxvbox.pack_start(self.sox_cmd_label,  False, True, 0)
        self.soxvbox.pack_start(self.soxprogress,  False, True, 0)

        vbox3.pack_start(self.soxvbox, False, True, 0)

        label = Gtk.Label()
        label.set_markup ('<b>' + _("Transcode") + '</b>')
        self.convvbox.pack_start(label, False, True, 0)
        self.convvbox.pack_start(self.conv_cmd_label,  False, True, 0)
        self.convvbox.pack_start(self.convprogress, False, True, 0)

        vbox3.pack_start(self.convvbox, False, True, 0)

#        label = Gtk.Label()
#        label.set_markup ('<b>' + _("Destination") + '</b>')
#        vbox3.pack_start(label, False, True, 0)

        self.dest_label = Gtk.Label()
        vbox3.pack_start(self.dest_label, False, True, 0)

        self.infobar = Gtk.InfoBar()
        self.infobar.set_no_show_all(True)
        self.infolabel = Gtk.Label()
        self.infolabel.show()
        content_area = self.infobar.get_content_area ()

        content_area.add (self.infolabel)
        self.infobar.add_button (Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.infobar.connect ("response", lambda x,y: self.infobar.hide());

        vbox.pack_start(self.infobar, True, True, 0)
        vbox.pack_start(self.dropvbox, True, True, 0)
        vbox.pack_start(vbox3, False, True, 0)

        self.add_text_targets()

        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        self.check_bin()

    def check_bin (self):
        try:
            which (os.environ['MELT_BINARY'])
        except:
            self.error ("could not find the melt binary")

    def error (self, msg):
        self.infobar.set_message_type(Gtk.MessageType.ERROR)
        self.infolabel.set_text(msg)
        self.infobar.show()

    def on_file_set (self, chooser, data=None):
        print 'file ' + chooser.get_filename()

    def get_dest_dir (self):
        return self.filechooser.get_filename()

    def convert (self, src, dst=None):
        self.drop_area.start()
        destdir = self.get_dest_dir()

        if (dst == None):
            if (destdir):
                dst = destdir + '/' + src.split('/')[-1].strip() + '.m4v'
            else:
                dst = src.strip() + '.m4v'

#        self.dropvbox.set_sensitive(False)
        self.dest_label.set_text (dst)

        self.src = src
        self.dst = dst
        self.mlt = dst + '.mlt'

        proc = self.do_pass1()
        self.then(proc, self.do_pass2)

    def do_pass1 (self):
        prog = ['melt','-progress', self.src.strip(),
                '-filter', 'sox:analysis',
                '-consumer', 'xml:' + self.mlt.strip(),
                'video_off=1', 'all=1']

        self.convprogress.set_fraction(0);
        self.soxprogress.set_fraction (0);

        self.sox_cmd_label.set_text (' ')
        self.sox_cmd_label.set_text (' '.join (prog))
        self.progress = self.soxprogress

        self.soxvbox.show()
        self.convvbox.hide()

        return self.run(prog)

    def do_pass2 (self):
        prog = ['melt','-progress', self.mlt.strip(),
                '-consumer', 'avformat:' + self.dst.strip(),
                'properties=H.264', 'strict=experimental', 'progressive=1']

        self.soxprogress.set_fraction(1);
        self.convprogress.set_fraction(0);

        self.conv_cmd_label.set_text (' '.join (prog))
        self.progress = self.convprogress

        self.soxvbox.show()
        self.convvbox.show()

        proc = self.run(prog)
        self.then(proc, self.alldone)

    def alldone (self, arg=None):
        self.sox_cmd_label.set_text (' ')
        self.conv_cmd_label.set_text (' ')
        self.convprogress.set_fraction(1);
        self.dropvbox.set_sensitive(True)

        self.drop_area.stop()

    def add_text_targets(self, button=None):
        self.drop_area.drag_dest_set_target_list(Gtk.TargetList.new([]))
        self.drop_area.drag_dest_add_text_targets()

    def run(self, command):
        import fcntl

        print _("Running: ") + ' '.join (command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.process = process

        # make stderr a non-blocking file
        fd = self.process.stderr.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        GLib.timeout_add (200, self.status, [self.update_progress, process])

        return process

    def status (self, args):
        (handler, proc) = args

        if (proc.poll() != None):
            return False

        line=''
        try:
            line = self.process.stderr.read()
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
        if (line and handler):
            handler(line)

        return True

    def then (self, proc, command, arg=None):
        GLib.timeout_add (500, self.check_runing, [proc, command, arg])

    def check_runing (self, args=None):
        (proc, nextcmd, arg) = args

        if (proc.poll() != None):
            if (arg):
                nextcmd(arg)
            else:
                nextcmd()
            return False

        return True

    def update_progress (self, line):
        perc = 0
        try:
            perc = float(re.findall(r'percentage:\s+(\d+).$', line)[0])
        except:
            return True
        if (perc):
            self.progress.set_fraction(perc/100)

class DropArea(Gtk.Box):
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.button = Gtk.Button.new_with_label ("")
        self.label = self.button.get_child()
        self.label.set_markup('<b>' + _("Drop something on me!") + '</b>')

        self.spinner = Gtk.Spinner()

        self.pack_start (self.button, True, True, 0)

        self.set_size_request (300, 200)
        self.app = app
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], DRAG_ACTION)

        self.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        if info == TARGET_ENTRY_TEXT:
            text = data.get_text()
            print "Got: %s" % text
            self.app.convert(GLib.filename_from_uri (text)[0])
        else:
            print _("Received something I can't handle")

    def start (self):
        try:
            self.remove (self.label)
            self.pack_start (self.spinner, True, True, 0)
            self.spinner.start()
            self.spinner.set_visible (True)
        except:
            pass

    def stop (self):
        try:
            self.remove (self.spinner)
            self.spinner.stop()
            self.pack_start (self.label, True, True, 0)
            self.label.set_visible (True)
        except:
            pass


win = DragDropWindow()
#win.convert('/home/xaiki/10000.mp4')
Gtk.main()
