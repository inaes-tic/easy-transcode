#!/usr/bin/env python
import sys
sys.path.append('lib')

from gi.repository import Gtk
import MBC

if __name__ == '__main__':
    mbc = MBC.Transcoder('simple.ui')
    Gtk.main()
