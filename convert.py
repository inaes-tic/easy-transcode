#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango

import gettext
import subprocess
import re
import os
import math
import time

gettext.bindtextdomain('easy-transcode')
gettext.textdomain ('easy-transcode')
_ = gettext.gettext

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)

active_color = (0.6, 0.6, 1)

try:
    print "got melt from environ: " + os.environ['MELT_BINARY']
except:
    os.environ['MELT_BINARY'] = 'melt'

DRAG_ACTION = Gdk.DragAction.COPY


def ps_to_floats (c):
    return (c.red, c.green, c.blue)

def which(file):
    for path in os.environ["PATH"].split(":"):
        if os.path.exists(path + "/" + file):
                return path + "/" + file

    raise ("ENOENT")

class DragDropWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=_("Easy Transcode Tool"))

        self.fail = False

        self.set_icon_name ("gtk-sort-ascending")
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
        self.fail = True

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

        self.drop_area.set_text (_("Audio Normalization"))
        return self.run(prog)

    def do_pass2 (self):
        prog = ['melt','-progress', self.mlt.strip(),
                '-consumer', 'avformat:' + self.dst.strip(),
                'properties=H.264', 'strict=experimental', 'progressive=1']

        self.drop_area.set_text (_("Video Transcoding"))
        proc = self.run(prog)
        self.then(proc, self.alldone)

    def alldone (self, arg=None):
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
            line = self.process.stderr.read()
            if re.findall(r'Failed to load', line):
                print "error"
                self.error (_("Error: ") + line)

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
            if self.fail:
                self.fail = False
                self.drop_area.stop()
                return False

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
            self.drop_area.fraction = perc
        return True

class DropArea(Gtk.Box):
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
#        self.button = Gtk.Button.new_with_label ("")
#        self.label = self.button.get_child()
        self.motion = False
        self.active = False
        self.fraction = 0

        self.label = Gtk.Label()
        self.pack_start (self.label, True, True, 0)

        self.set_size_request (300, 200)
        self.app = app
        self.drag_dest_set(Gtk.DestDefaults.ALL ^ Gtk.DestDefaults.HIGHLIGHT, [], DRAG_ACTION)

        self.set_property ("app-paintable", True)

        self.connect("drag-data-received", self.on_drag_data_received)
        self.connect("drag-motion", self.drag_begin_cb)
        self.connect("drag-leave", self.drag_leave_cb)
        self.connect("draw", self.draw_cb)

        self.stop()

    def drag_begin_cb (self, widget, context, x, y, time, data=None):
        if (self.motion):
            return True

        self.motion = True
        self.queue_draw()

    def drag_leave_cb (self, widget, context, time, data=None):
        self.motion = False
        self.queue_draw()

    def draw_cb (self, widget, cr, data=None):
        style =  widget.get_style_context()

        fg_color = style.get_color (Gtk.StateFlags.ACTIVE)
        text_color = style.get_color (Gtk.StateFlags.FOCUSED)
        selected_color = style.get_color (Gtk.StateFlags.SELECTED)
        insensitive_color = style.get_color (Gtk.StateFlags.BACKDROP)

        if self.motion:
#            cr.set_source_rgb (*ps_to_floats(fg_color))
            cr.set_source_rgb (*active_color)
        elif self.active:
            cr.set_source_rgba (*insensitive_color)
        elif widget.get_state_flags () & Gtk.StateFlags.BACKDROP:
            cr.set_source_rgba (*text_color)
        else:
            cr.set_source_rgba (*selected_color)

        cr.save()
        self.draw_dashed_drop(cr)
        cr.restore()

        if self.active:
            cr.save()
            self.draw_progress(cr)
            cr.restore()

        return False

    def draw_dashed_drop (self, cr):
        x         = 25.6        # parameters like cairo_rectangle 
        y         = 25.6
        width         = self.get_allocated_width() - 2*x
        height        = self.get_allocated_height() - 2*y
        aspect        = 1.0     # aspect ratio 
        corner_radius = height / 10.0 #   and corner curvature radius

        radius = corner_radius / aspect;
        degrees = math.pi / 180.0;

        dashlen = (height + width)/30.0
        start = 0
        if self.active:
            start = -math.floor(time.time()*25)

        cr.set_dash ([dashlen, dashlen], start)
        cr.set_line_width (6)

        cr.new_sub_path ()
        cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees);
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees);
        cr.close_path ()

        cr.stroke()

    def draw_progress (self, cr):
        x         = 25.6        # parameters like cairo_rectangle 
        y         = 25.6
        width         = self.get_allocated_width() - 2*x
        height        = self.get_allocated_height() - 2*y
        aspect        = 1.0     # aspect ratio 
        corner_radius = height / 10.0 #   and corner curvature radius

        radius = corner_radius / aspect;
        degrees = math.pi / 180.0;

        cr.set_line_width (radius*2)
        cr.new_sub_path ()

        cr.arc (x + width/2, y + height/2 + radius, radius*2, 0, degrees*360)

        cr.stroke()

        cr.set_source_rgb (*active_color)
        cr.arc (x + width/2, y + height/2 + radius, radius*2, 0, self.fraction*degrees*360/100.0)

        cr.stroke()


    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        if info == TARGET_ENTRY_TEXT:
            text = data.get_text()
            print "Got: %s" % text
            self.app.convert(GLib.filename_from_uri (text)[0])
        else:
            print _("Received something I can't handle")

    def animate (self):
        self.queue_draw()
        return self.active

    def set_text (self, text):
        self.label.set_markup('<b><big>' + text + '</big></b>')

    def start (self):
        self.active = True
        GLib.timeout_add((1/30.)*1000, self.animate)
        self.set_text( _("Processing..."))
        self.set_sensitive (False)

    def stop (self):
        self.active = False
        self.set_text(_("Drop something on me !"))
        self.set_sensitive (True)

win = DragDropWindow()
#win.convert('/home/xaiki/10000.mp4')
Gtk.main()
