#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GLib, Pango

import gettext
import subprocess
import re
import os
import math
import time
import tempfile

gettext.bindtextdomain('easy-transcode')
gettext.textdomain ('easy-transcode')
_ = gettext.gettext

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)

active_color = (0.6, 0.6, 1, 1)

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

def animate (a, b, p):
    if p <= 0:
        return a
    if p >= 1:
        return b
    return a - (a - b)*p

def xdg_open (f):
    return subprocess.Popen(['xdg-open', f])

class XAAnimatable ():
    def __init__ (self):
        self.active = False
        self.start_time = 0
        self.connect("draw", self.draw_cb)

    def animate (self):
        self.queue_draw()
        return self.active

    def animation_start (self):
        self.active = True
        self.start_time = time.time()
        GLib.timeout_add((1/30.)*1000, self.animate)

    def drift (self):
        return (time.time() - self.start_time)

    def draw_cb (self, widget, cr, data=None):
        print "DEFAULT DRAW HANDLER"

class XAInfoBar (Gtk.InfoBar):
    def __init__ (self, msgtype = Gtk.MessageType.INFO,
                  responses = {Gtk.ResponseType.OK : [Gtk.STOCK_OK, None]}):
        Gtk.InfoBar.__init__ (self)

        self.responses = responses
        self.msgtype = msgtype
        self.set_no_show_all(True)
        self.label = Gtk.Label()
        self.label.set_line_warp(True)
        self.label.show()
        content_area = self.get_content_area ()

        content_area.add (self.label)
        for r in responses.keys():
            self.add_button (responses[r][0], r)
        self.connect ("response", self.response_cb);

    def add_response (self, rid, rob):
        if not self.responses.has_key(rid):
            self.add_button (rob[0], rid)
        self.responses[rid] = rob

    def response_cb (self, wid, rid):
        print "called", self.responses, wid
        print self.responses[rid]
        fn = self.responses[rid][1]
        if fn:
            fn(rid)
        self.hide()

    def notify (self, msg):
        self.set_message_type(self.msgtype)
        self.label.set_text(msg)
        self.show()

class DragDropWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=_("Easy Transcode Tool"))
        XAAnimatable.__init__(self)

        self.fail = False

        self.set_icon_name ("gtk-sort-ascending")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.errorbar = XAInfoBar (msgtype = Gtk.MessageType.ERROR)
        self.infobar = XAInfoBar (msgtype = Gtk.MessageType.INFO)

        vbox.pack_start(self.errorbar, True, True, 0)
        vbox.pack_start(self.infobar, True, True, 0)

        self.drop_area    = DropArea(self)
        self.drop_area.store.connect ("row-inserted", self.row_added_cb)
        self.tree = Gtk.TreeView(self.drop_area.store)
        self.tree.set_size_request (-1, 400)
#        self.tree.set_headers_visible (False)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Queue"), renderer, text=0)
        self.tree.append_column(column)

        self.dropvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        hbox  = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label()
        label.set_markup ("<b>" + _("Destination") + ": </b>")
        label.set_size_request (50, 50)
        self.filechooser = Gtk.FileChooserButton ()
        self.filechooser.set_uri ('file://' + os.environ['PWD'])
        self.filechooser.set_title (_("Destination Folder"))
        self.filechooser.set_action (Gtk.FileChooserAction.SELECT_FOLDER)

        self.filechooser.connect("file-set", self.on_file_set)
        self.filechooser.set_current_folder ("~/")

        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.filechooser, True, True, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.add (self.tree)
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        pos = self.drop_area.get_size_request()[0]
        print "pos", pos
        self.paned.set_position (pos + 100) # XXX: hack
        print "pos", self.paned.get_position()
        self.paned.pack1 (self.drop_area, True, True)
        self.paned.pack2 (scroll, False, True)

        self.dropvbox.pack_start(self.paned, True, True, 0)
        self.dropvbox.pack_start(hbox, False, False, 0)

        self.dest_label = Gtk.Label()
        self.dest_label.set_property ('ellipsize', Pango.EllipsizeMode.START)

        vbox3.pack_start(self.dest_label, False, True, 0)

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
            self.errorbar.notify ("could not find the melt binary")
            self.fail = True

    def on_file_set (self, chooser, data=None):
        print 'file ' + chooser.get_filename()

    def get_dest_dir (self):
        return self.filechooser.get_filename()

    def convert (self, src, dst=None):
        src = GLib.filename_from_uri (src)[0]
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
        (fd, self.mlt) = tempfile.mkstemp('.mlt')
        print fd, self.mlt
        os.close(fd)

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
        dst = self.dst
        if self.mlt:
            os.remove (self.mlt)
            self.mlt = None

        self.drop_area.stop()
        self.infobar.notify(_("Transcode complete: ") + dst)
        self.infobar.add_response (0,
                                   [Gtk.STOCK_OPEN,
                                    lambda x: xdg_open(os.path.dirname(dst))])

        GLib.timeout_add (10, self.check_drop_store)

    def check_drop_store (self):
        store = self.drop_area.store
        it = store.get_iter_first()
        v = store.get_value (it, 0)
        store.remove (it)

        self.convert (v)
        return False

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
            try:
                line = self.process.stderr.read()

                if re.findall(r'Failed to load', line):
                    self.errorbar.notify (_("Error: ") + line)
                    self.fail = True
            except:
                pass

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

    def row_added_cb (self, store, pos, ite):
        print "got:", pos.to_string()
        if (pos.to_string() == '0'):
            self.pos = self.paned.get_position()
            print "pos --- > ", self.pos
            self.animation_start()

    def draw_cb (self, widget, cr, data=None):
        if not self.active:
            return False

        drift = self.drift()*2
        if drift > 1:
            self.active = False

        d = animate (self.pos, 200, drift)
        self.paned.set_position (d)

        return False

class DropArea(XAAnimatable, Gtk.Box):
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        XAAnimatable.__init__(self)

#        self.button = Gtk.Button.new_with_label ("")
#        self.label = self.button.get_child()
        self.motion = False
        self.fraction = 0

        self.label = Gtk.Label()
        self.pack_start (self.label, True, True, 0)

        self.store = Gtk.ListStore(str)

        self.set_size_request (300, 200)
        self.app = app
        self.drag_dest_set(Gtk.DestDefaults.ALL ^ Gtk.DestDefaults.HIGHLIGHT, [], DRAG_ACTION)

        self.set_property ("app-paintable", True)

        self.connect("drag-data-received", self.on_drag_data_received)
        self.connect("drag-motion", self.drag_begin_cb)
        self.connect("drag-leave", self.drag_leave_cb)

        self.stop()

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        print "drag received", drag_context, data, info
        if info == TARGET_ENTRY_TEXT:
            text = data.get_text().split('\n')
            self.app.convert(text[0])
            for u in text[1:]:
                self.store.append([u])
        else:
            print _("Received something I can't handle")


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

        current_color = None
        if self.motion:
            current_color = active_color
        elif self.active:
            current_color = insensitive_color
        elif widget.get_state_flags () & Gtk.StateFlags.BACKDROP:
            current_color = text_color
        else:
            current_color = selected_color

        cr.set_source_rgba (*current_color)
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
        w         = self.get_allocated_width()
        h         = self.get_allocated_height()

        lw        = 6

        aspect        = 1.0     # aspect ratio
        corner_radius = h / 10.0 #   and corner curvature radius
        radius = corner_radius / aspect;

#        if self.active:
#            x  = animate (x, w/2 - radius, self.drift())
#            y  = animate (y, h/2 - radius, self.drift())
#            lw = animate (lw, 10, self.drift())

        width     = w - 2*x
        height    = h - 2*y

        degrees = math.pi / 180.0;

        dashlen = (height + width)/30.0
        start = 0
        if self.active:
            start = -math.floor(time.time()*25)

        cr.set_dash ([dashlen, dashlen], start)
        cr.set_line_width (lw)

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

        start = -math.floor(time.time()*25)

        cr.save()
        cr.set_line_width (10)
        cr.set_dash ([10, 10], start)
        cr.new_sub_path ()

        cr.arc (x + width/2, y + height/2, radius*2, 0, degrees*360)

        cr.stroke()
        cr.restore()

        cr.save()
        cr.set_line_width (10)
        cr.set_source_rgba (*active_color)
        cr.arc (x + width/2, y + height/2, radius*2, 0, self.fraction*degrees*360/100.0)

        cr.stroke()
        cr.restore()

    def set_text (self, text):
        self.label.set_markup('<b><big>' + text + '</big></b>')

    def start (self):
        self.animation_start()
        self.set_text( _("Processing..."))
        self.set_sensitive (False)

    def stop (self):
        self.active = False
        self.set_text(_("Drop something on me !"))
        self.set_sensitive (True)

win = DragDropWindow()
#win.convert('/home/xaiki/10000.mp4')
Gtk.main()
