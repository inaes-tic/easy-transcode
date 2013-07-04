#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GLib, Pango, GObject

import gettext

import os
import math
import time
import subprocess

import Process
import Melt

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

    def animate_prop (self, fr, to):
        drift = self.drift()
        if (drift > 1):
            self.active = False
        if drift <= 0:
            return fr
        if drift >= 1:
            return to
        return fr - (fr - to)*drift

    def animation_start (self, duration=1):
        self.duration = duration
        self.active = True
        self.start_time = time.time()
        GLib.timeout_add((1/30.)*1000, self.animate)

    def drift(self):
        return (time.time() - self.start_time)/self.duration

    def draw_cb (self, widget, cr, data=None):
        print "DEFAULT DRAW HANDLER"

class XAInfoBar (Gtk.InfoBar):
    def __init__ (self, msgtype = Gtk.MessageType.INFO,
                  responses = {}):
        Gtk.InfoBar.__init__ (self)

        self.responses = {0 : [Gtk.STOCK_OK, None]}
        self.responses.update(responses)

        print self.responses
        self.msgtype = msgtype
        self.set_no_show_all(True)
        self.label = Gtk.Label()
        self.label.set_line_wrap(True)
        self.label.show()
        content_area = self.get_content_area ()

        content_area.add (self.label)
        for r in self.responses.keys():
            self.add_button (self.responses[r][0], r)
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

class DragDropWindow(Gtk.Window, XAAnimatable):
    def __init__(self):
        Gtk.Window.__init__(self, title=_("Easy Transcode Tool"))
        XAAnimatable.__init__(self)

        self.fail = False

        self.set_icon_name ("gtk-sort-ascending")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.infobox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start (self.infobox, False, False, 0)

        self.drop_area    = DropArea(self)
        self.drop_area.store.connect ("row-inserted", self.row_changed_cb)
        self.drop_area.store.connect ("row-deleted", self.row_changed_cb)
        self.queuetree = self.make_tree (_("Queue"), self.drop_area.store)

        self.errorstore = Gtk.ListStore (str)
        self.errortree  = self.make_tree (_("Errors"), self.errorstore)

        self.successtore = Gtk.ListStore (str)
        self.successtree = self.make_tree (_("Success"), self.successtore)

        self.procstore = Gtk.ListStore (str)
        self.proctree = self.make_tree (_("Processing"), self.procstore, rem=False)

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

        treebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        treebox.pack_start (self.proctree, False, True, 0)
        treebox.pack_start (self.queuetree, False, True, 0)
        treebox.pack_start (self.successtree, False, True, 0)
        treebox.pack_start (self.errortree, False, True, 0)

        self.proctree.set_no_show_all (True)
        self.queuetree.set_no_show_all (True)
        self.successtree.set_no_show_all (True)
        self.errortree.set_no_show_all (True)

        treebox.set_size_request (-1, 0)
#        scroll = Gtk.ScrolledWindow()

#        scroll.add(treebox)

        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        pos = self.drop_area.get_size_request()[0]
        print "pos", pos
        self.paned.set_position (pos + 100) # XXX: hack
        print "pos", self.paned.get_position()
#        self.paned.pack1 (self.drop_area, True, False)
#        self.paned.pack2 (scroll, True, False)

#        self.dropvbox.pack_start(self.paned, True, True, 0)
	self.dropvbox.pack_start(self.drop_area, True, True, 0)
        self.dropvbox.pack_start(treebox, False, True, 0)
        self.dropvbox.pack_start(hbox, False, False, 0)

        vbox.pack_start(self.dropvbox, True, True, 0)
        vbox.pack_start(vbox3, False, True, 0)

        self.add_text_targets()

        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        self.check_bin()


    def notify (self, msg, t=Gtk.MessageType.INFO, r={0 : [Gtk.STOCK_OK, None]}):
        infobar = XAInfoBar (msgtype = t, responses = r)
        self.infobox.pack_end (infobar, True, False, 0)
        infobar.notify(msg)
    def convert (self, s):
        destdir = self.get_dest_dir()
        self.melt = Melt.Transcode (s, destdir=destdir)

        self.melt.connect ('start',  self.convert_start_cb)
        self.melt.connect ('finished', self.convert_finished_cb)
        self.melt.connect ('error',    self.convert_error_cb)
        self.melt.connect ('success',  self.convert_success_cb)
        self.melt.connect ('start-audio', lambda o:
                           self.drop_area.set_text (_("Audio Normalization")))
        self.melt.connect ('start-video', lambda o:
                           self.drop_area.set_text (_("Video Transcoding")))
        self.melt.connect ('progress', lambda o, p: self.drop_area.set_fraction(p))

        self.melt.start()

    def convert_start_cb (self, o, s, d):
        self.drop_area.start()
        self.procstore.append ([s])
        self.proctree.show()

    def convert_finished_cb (self, o, s, d):
        self.drop_area.stop()
        self.check_drop_store()
        self.procstore.remove(self.procstore.get_iter_first())

    def convert_success_cb (self, o, d):
        self.successtore.append ([d])
        self.successtree.show()

    def convert_error_cb (self, o, d):
        self.errorstore.append ([d])
        self.errortree.show()

    def _convert_success_cb (self, o, d):
        self.notify (_("Success: ") + d,
                     r={1: [Gtk.STOCK_OPEN,
                                 lambda x: xdg_open(os.path.dirname(d))]})

    def _convert_error_cb (self, o, d):
        self.notify (_("Error: ") + d,
                     t=Gtk.MessageType.ERROR,
                     r={2: [Gtk.STOCK_OPEN,
                          lambda x: self.show_err()]})

    def show_err (self):
        w = Gtk.Window(title = _("Error Log"))
        l = Gtk.Label()
        l.set_line_wrap (True)
        try:
            l.set_text (self.melt.errstr)
        except:
            return False

        w.add(l)
        w.show_all()

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

    def next (self):
        self.drop_area.stop()
        GLib.timeout_add (100, self.check_drop_store)

    def check_drop_store (self):
        store = self.drop_area.store
        if not len(store):
            return False

        it = store.get_iter_first()
        v = store.get_value (it, 0)
        store.remove (it)

        self.convert (v)
        return True

    def add_text_targets(self, button=None):
        self.drop_area.drag_dest_set_target_list(Gtk.TargetList.new([]))
        self.drop_area.drag_dest_add_text_targets()

    def make_tree (self, name, store, rem=True):
        tree = Gtk.TreeView (store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(name, renderer, text=0)
        tree.append_column(column)
        store.connect ('row-deleted', self.check_hide, tree)
        if rem:
            tree.connect ('row-activated', self.delete_row)
        return tree

    def check_hide (self, model, path, tree):
        if not len(model):
            tree.hide()

    def delete_row (self, tree, path, column):
        model = tree.get_model()
        model.remove (model.get_iter(path))

    def row_changed_cb (self, store, pos, ite=None):
        length = len(store)
        print "row added", length
        if length <= 1:
            self.queuetree.show()
            self.pos = self.paned.get_position()
            self.length = length
            self.animation_start()

    def draw_cb (self, widget, cr, data=None):
        if not self.active:
            return False

        dest = 300
        if self.length:
            dest = 200

        d = self.animate_prop (self.pos, dest)
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

    def set_fraction (self, f):
        self.fraction = f
        self.queue_draw()

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        print "drag received", drag_context, data, info
        if info == TARGET_ENTRY_TEXT:
            text = data.get_text().splitlines()
            print "text", text
            if not len(self.store):
                self.app.convert(text.pop())
            for u in text:
                print "adding:", u
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
#            x  = self.animate_prop (x, w/2 - radius)
#            y  = self.animate_prop (y, h/2 - radius)
#            lw = self.animate_prop (lw, 10)

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
        print "start"
        self.animation_start()
        self.set_text( _("Processing..."))
#        self.set_sensitive (False)

    def stop (self):
        print "stop"
        self.active = False
        self.set_text(_("Drop something on me !"))
 #       self.set_sensitive (True)

win = DragDropWindow()
#win.convert('/home/xaiki/10000.mp4')
Gtk.main()
