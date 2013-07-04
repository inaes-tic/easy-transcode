#!/usr/bin/env python
import sys
sys.path.append('lib')

from gi.repository import Gtk
import MBC

win = MBC.DragDropWindow()
Gtk.main()
