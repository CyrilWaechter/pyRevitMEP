#! python3
# coding: utf8
import sys
sys.path.append(r"C:\msys64\mingw64\lib\python3.7\site-packages")
sys.path.append(r"C:\msys64\mingw64\lib")
sys.path.append(r"C:\msys64\mingw64\bin")
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class LoginWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Database Connection")

        grid = Gtk.Grid()
        self.add(grid)

window = LoginWindow()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()