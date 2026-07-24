import os
import glob
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from speech import SpeechEngine

class AccessibleDesktopWindow(Gtk.Window):
    """
    Accessible Desktop Window (Win+M / Win+D)
    Lists real user desktop shortcuts and applications in ~/Desktop and /usr/share/applications.
    """
    def __init__(self, speech: SpeechEngine):
        super().__init__(title="")
        self.speech = speech
        
        self.set_default_size(800, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)
        
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.box.set_margin_top(15)
        self.box.set_margin_bottom(15)
        self.box.set_margin_start(15)
        self.box.set_margin_end(15)
        self.add(self.box)

        self.header = Gtk.Label(label="Área de Trabalho (Desktop)")
        self.header.set_xalign(0)
        self.box.pack_start(self.header, False, False, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.box.pack_start(self.listbox, True, True, 0)

        self.listbox.connect("row-selected", self.on_row_selected)
        self.listbox.connect("row-activated", self.on_row_activated)
        self.connect("key-press-event", self.on_key_press)

        self.populate_desktop()

    def get_desktop_files(self):
        items = []
        desktop_dir = os.path.expanduser("~/Desktop")
        if os.path.exists(desktop_dir):
            for entry in os.listdir(desktop_dir):
                items.append((entry, os.path.join(desktop_dir, entry)))
                
        # System applications
        apps = [
            ("Gerenciador de Arquivos", "thunar"),
            ("Terminal", "x-terminal-emulator"),
            ("Configurações", "gnome-control-center"),
            ("Navegador Web", "firefox"),
        ]
        for name, cmd in apps:
            items.append((name, cmd))
        return items

    def populate_desktop(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        items = self.get_desktop_files()
        for idx, (name, cmd) in enumerate(items, start=1):
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=f"{name}  lista")
            label.set_xalign(0)
            row.add(label)
            row.cmd = cmd
            row.item_name = name
            self.listbox.add(row)

        self.show_all()

    def on_row_selected(self, listbox, row):
        if row and hasattr(row, 'item_name'):
            self.speech.speak(f"{row.item_name}  lista")

    def on_row_activated(self, listbox, row):
        if row and hasattr(row, 'cmd'):
            self.speech.speak(f"Abrindo {row.item_name}")
            try:
                subprocess.Popen([row.cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def open_desktop_window(self):
        self.populate_desktop()
        self.show_all()
        self.present()
        self.listbox.grab_focus()
        self.speech.speak("Desktop  lista")
