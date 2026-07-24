import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from speech import SpeechEngine
from systray import SystemTray

class AccessibleShellWindow(Gtk.Window):
    """
    Native accessible GTK3 Window for win-a11y-shell.
    Forced foreground focus stealing to break out of active terminal windows.
    """
    def __init__(self, speech: SpeechEngine, systray: SystemTray):
        super().__init__(title="")
        self.speech = speech
        self.systray = systray
        
        self.set_default_size(700, 450)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)
        self.set_accept_focus(True)
        self.set_decorated(True)
        
        # Main layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.box.set_margin_top(15)
        self.box.set_margin_bottom(15)
        self.box.set_margin_start(15)
        self.box.set_margin_end(15)
        self.add(self.box)

        # Header Label
        self.header = Gtk.Label(label="Bandeja do Sistema (Área de Notificação)")
        self.header.set_xalign(0)
        self.box.pack_start(self.header, False, False, 0)

        # Accessible ListBox
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.box.pack_start(self.listbox, True, True, 0)

        self.listbox.connect("row-selected", self.on_row_selected)
        self.listbox.connect("row-activated", self.on_row_activated)
        self.connect("key-press-event", self.on_key_press)

        self.populate_systray()

    def populate_systray(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        items = self.systray.get_active_list()
        for item in items:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=item.announce())
            label.set_xalign(0)
            row.add(label)
            row.item_ref = item
            self.listbox.add(row)

        self.show_all()

    def on_row_selected(self, listbox, row):
        if row and hasattr(row, 'item_ref'):
            item = row.item_ref
            self.speech.speak(item.announce())

    def on_row_activated(self, listbox, row):
        if row and hasattr(row, 'item_ref'):
            self.systray.current_index = row.get_index()
            self.systray.activate()
            self.populate_systray()

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def open_systray_window(self):
        self.populate_systray()
        self.show_all()
        self.present()
        self.listbox.grab_focus()
        
        # Force window focus over active terminal using xdotool / wmctrl
        try:
            subprocess.run(["xdotool", "search", "--name", "win-a11y-shell", "windowactivate"], check=False)
        except Exception:
            pass
