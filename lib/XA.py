from gi.repository import GLib, Gtk

import time

class Animatable ():
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

class InfoBar (Gtk.InfoBar):
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

