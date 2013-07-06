from gi.repository import Gtk, Gdk, GLib

import math
import time
import XA

import configure

(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)

active_color = (0.6, 0.6, 1, 1)

DRAG_ACTION = Gdk.DragAction.COPY

class Widget (XA.Animatable, Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        XA.Animatable.__init__(self)

        self.builder = Gtk.Builder()
        self.motion = False
        self.fraction = 0

        self.builder.add_from_file (configure.get_ui_dir() + '/dropwidget.ui')

        self.label = self.builder.get_object('label')
        self.default_text = self.label.get_text()
        self.label.unparent ()
        self.pack_start (self.label, True, True, 0)

        self.set_property ("app-paintable", True)

    def set_fraction (self, f):
        self.fraction = f
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
        return False

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
        self.set_text( "Processing...")

    def stop (self):
        self.active = False
        self.set_text(self.default_text)


class Window (Gtk.Box, XA.Animatable):
    def __getattr__(self, v):
        return getattr(self.drop_widget, v)

    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.builder = Gtk.Builder()
        self.motion = False

        self.builder.add_from_file (configure.get_ui_dir() + '/dropwindow.ui')
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL) # self.builder.get_object('paned')
        box = self.builder.get_object('box2')
        paned.unparent ()
	box.unparent()

        self.pack_start (paned, True, True, 0)
        self.drop_widget = Widget()

        paned.pack1 (self.drop_widget, False, False)
        paned.pack2 (box, False, False)

#        self.button = Gtk.Button.new_with_label ('')
#        self.drop_widget = self.button.get_child()

        self.qstore = self.builder.get_object('qstore')
        self.pstore = self.builder.get_object('pstore')
        self.sstore = self.builder.get_object('sstore')
        self.fstore = self.builder.get_object('fstore')

        self.drag_dest_set(Gtk.DestDefaults.ALL ^ Gtk.DestDefaults.HIGHLIGHT, [], DRAG_ACTION)
        self.add_text_targets()

        self.connect("drag-data-received", self.on_drag_data_received)
        self.connect("drag-motion", self.drag_begin_cb)
        self.connect("drag-leave", self.drag_leave_cb)

        self.prenderer = self.builder.get_object ('prenderer')
        self.pview = self.builder.get_object ('pview')
        GLib.timeout_add((1/30.)*1000, self.pulse_proc)

        self.builder.connect_signals(self)
        self.stop()

    def pulse_proc (self):
        now = time.time()*2
        off = math.cos(now)
        color = Gdk.RGBA (196, 160, 0, 0.40 + 0.3*off)

        self.prenderer.set_property ('background-rgba', color)
        self.pview.queue_draw()
        return True

    def add_text_targets(self, button=None):
        self.drag_dest_set_target_list(Gtk.TargetList.new([]))
        self.drag_dest_add_text_targets()

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        if info == TARGET_ENTRY_TEXT:
            text = data.get_text().splitlines()
            for u in text:
                self.qstore.append([u])
        else:
            print "Received something I can't handle"

    def drag_begin_cb (self, widget, context, x, y, time, data=None):
        if (self.motion):
            return True

        self.motion = True
        self.drop_widget.queue_draw()

    def drag_leave_cb (self, widget, context, time, data=None):
        self.motion = False
        self.drop_widget.queue_draw()

    def check_hide (self, tree, path=None, iter=None):
        model = tree.get_model()
        if not len(model):
            return tree.hide()
        return tree.show()

    def delete_row (self, tree, path, column):
        model = tree.get_model()
        model.remove (model.get_iter(path))

    def row_changed_cb (self, store, pos, ite=None):
        length = len(store)
        if length <= 1:
            self.queuetree.show()
            self.pos = self.paned.get_position()
            self.length = length
            self.drop_widget.animation_start()

class caca():
    def set_fraction (self, f):
        return self.drop_widget.set_fraction(f)

    def start(self):
        self.drop_widget.start()

    def stop(self):
        self.drop_widget.stop()

    def set_text(self, t):
        self.drop_widget.set_text(t)

if __name__ == '__main__':
    for t in [Window(), Widget()]:
        w = Gtk.Window()
        w.set_title(repr(t))
        w.connect ('destroy', lambda w: Gtk.main_quit())
        w.add (t)
        w.show_all()

    Gtk.main()
