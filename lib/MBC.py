#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GLib

import os
import subprocess

import Melt
import Drop

try:
    print "got melt from environ: " + os.environ['MELT_BINARY']
except:
    os.environ['MELT_BINARY'] = 'melt'

def which(file):
    for path in os.environ["PATH"].split(":"):
        if os.path.exists(path + "/" + file):
                return path + "/" + file

    raise ("ENOENT")

def xdg_open (f):
    return subprocess.Popen(['xdg-open', f])

class Transcoder (Gtk.Builder):
    def __init__(self, ui):
        Gtk.Builder.__init__(self)
        self.set_translation_domain ('mbc-zumo')
        self.fail = False
        self.melt = None

        self.add_from_file (ui)
        window = self.get_object('window')
        window.connect('destroy', lambda w: Gtk.main_quit())

        box = self.get_object('box')
        hbox = self.get_object('box3')
        box.remove(hbox)

        self.drop_area = Drop.Window()
        box.pack_start (self.drop_area, True, True, 0)
        box.pack_start (hbox, False, False, 0)

        self.drop_area.qstore.connect('row-inserted', self.check_drop_store)

        self.filechooser = self.get_object('fcbutton')
        self.filechooser.set_uri ('file://' + os.environ['PWD'])

        self.check_bin()
        window.show_all()

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
        self.drop_area.pstore.append ([s])

    def convert_finished_cb (self, o, s, d):
        self.melt = None
        self.drop_area.stop()
        self.check_drop_store()
        self.drop_area.pstore.remove(self.drop_area.pstore.get_iter_first())

    def convert_success_cb (self, o, d):
        self.drop_area.sstore.append ([d])

    def convert_error_cb (self, o, d):
        self.drop_area.fstore.append ([d])

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
        melt = os.environ['MELT_BINARY']
        try:
            which (melt)
        except:
            print "could not find the melt binary:", melt
            raise "ENOENT"

    def get_dest_dir (self):
        return self.filechooser.get_filename()

    def next (self):
        self.drop_area.stop()
        GLib.timeout_add (100, self.check_drop_store)

    def check_drop_store (self, model=None, path=None, iter=None):
        if self.melt:
            return False

        store = self.drop_area.qstore
        if not len(store):
            return False

        it = store.get_iter_first()
        v = store.get_value (it, 0)
        store.remove (it)

        self.convert (v)
        return True
