import os
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from speech import SpeechEngine
from systray import SystemTray
from taskbar import get_running_windows, activate_window
from login import AccessibleLoginWindow

class WindowsFocusController(Gtk.Window):
    """
    Unified Windows + NVDA Focus Controller.
    Supports real desktop files, open Linux window switching (Alt+Tab / Taskbar), and Accessible Login.
    """
    REGIONS = ['desktop', 'start', 'taskbar', 'systray']

    def __init__(self, speech: SpeechEngine):
        super().__init__(title="win-a11y-shell")
        self.speech = speech
        self.systray = SystemTray(speech)
        self.login_window = AccessibleLoginWindow(speech)
        
        self.current_region_idx = 0
        self.desktop_items = []
        self.desktop_idx = 0

        self.taskbar_items = []
        self.taskbar_idx = 0

        self.set_default_size(800, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.box.set_margin_top(15)
        self.box.set_margin_bottom(15)
        self.box.set_margin_start(15)
        self.box.set_margin_end(15)
        self.add(self.box)

        self.label_region = Gtk.Label()
        self.label_region.set_xalign(0)
        self.box.pack_start(self.label_region, False, False, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.box.pack_start(self.listbox, True, True, 0)

        self.reload_real_desktop()
        self.connect("key-press-event", self.on_key_press)

    def reload_real_desktop(self):
        items = []
        desktop_dir = os.path.expanduser("~/Desktop")
        if os.path.exists(desktop_dir):
            for entry in sorted(os.listdir(desktop_dir)):
                if not entry.startswith('.'):
                    items.append((entry, os.path.join(desktop_dir, entry)))

        if not items:
            items = [("Área de Trabalho", "folder")]

        self.desktop_items = items

    def focus_region(self, region_name: str):
        if region_name in self.REGIONS:
            self.current_region_idx = self.REGIONS.index(region_name)
        self.render_region()

    def cycle_tab(self):
        self.current_region_idx = (self.current_region_idx + 1) % len(self.REGIONS)
        self.render_region()

    def render_region(self):
        region = self.REGIONS[self.current_region_idx]
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        if region == 'desktop':
            self.reload_real_desktop()
            total = len(self.desktop_items)
            item_name = self.desktop_items[self.desktop_idx][0]
            speech_str = f"Desktop  lista\n{item_name}  {self.desktop_idx + 1} de {total}"
            self.label_region.set_text("Desktop (Área de Trabalho)")

            for idx, (name, _) in enumerate(self.desktop_items, start=1):
                row = Gtk.ListBoxRow()
                label = Gtk.Label(label=f"{name}  {idx} de {total}")
                label.set_xalign(0)
                row.add(label)
                self.listbox.add(row)

        elif region == 'start':
            speech_str = "Iniciar  botão de alternância  não pressionado"
            self.label_region.set_text("Menu Iniciar")
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="Iniciar  botão de alternância  não pressionado")
            label.set_xalign(0)
            row.add(label)
            self.listbox.add(row)

        elif region == 'taskbar':
            self.taskbar_items = get_running_windows()
            total = len(self.taskbar_items)
            if self.taskbar_idx >= total:
                self.taskbar_idx = 0
            
            wid, wtitle, pos, tot = self.taskbar_items[self.taskbar_idx]
            speech_str = f"{wtitle}  botão  {pos} de {tot}"
            self.label_region.set_text("Barra de Tarefas (Janelas em execução)")

            for wid, wtitle, pos, tot in self.taskbar_items:
                row = Gtk.ListBoxRow()
                label = Gtk.Label(label=f"{wtitle}  botão  {pos} de {tot}")
                label.set_xalign(0)
                row.add(label)
                self.listbox.add(row)

        elif region == 'systray':
            speech_str = "Mostrar Ícones Ocultos Mostrar ícones ocultos  botão"
            self.label_region.set_text("Bandeja do Sistema")
            items = self.systray.get_active_list()
            for item in items:
                row = Gtk.ListBoxRow()
                label = Gtk.Label(label=item.announce())
                label.set_xalign(0)
                row.add(label)
                self.listbox.add(row)

        self.show_all()
        self.present()
        self.listbox.grab_focus()
        self.speech.speak(speech_str)

    def on_key_press(self, widget, event):
        key = event.keyval
        region = self.REGIONS[self.current_region_idx]

        if key == Gdk.KEY_Tab:
            self.cycle_tab()
            return True
        elif key == Gdk.KEY_Escape:
            self.hide()
            return True
        elif key == Gdk.KEY_Return or key == Gdk.KEY_KP_Enter:
            if region == 'taskbar' and self.taskbar_items:
                wid, wtitle, pos, tot = self.taskbar_items[self.taskbar_idx]
                self.hide()
                activate_window(wid)
                return True

        if region == 'desktop':
            total = len(self.desktop_items)
            if key in (Gdk.KEY_Right, Gdk.KEY_Down):
                self.desktop_idx = (self.desktop_idx + 1) % total
                item_name = self.desktop_items[self.desktop_idx][0]
                self.speech.speak(f"{item_name}  {self.desktop_idx + 1} de {total}")
                return True
            elif key in (Gdk.KEY_Left, Gdk.KEY_Up):
                self.desktop_idx = (self.desktop_idx - 1) % total
                item_name = self.desktop_items[self.desktop_idx][0]
                self.speech.speak(f"{item_name}  {self.desktop_idx + 1} de {total}")
                return True

        elif region == 'taskbar':
            total = len(self.taskbar_items)
            if key in (Gdk.KEY_Right, Gdk.KEY_Down):
                self.taskbar_idx = (self.taskbar_idx + 1) % total
                wid, wtitle, pos, tot = self.taskbar_items[self.taskbar_idx]
                self.speech.speak(f"{wtitle}  botão  {pos} de {tot}")
                return True
            elif key in (Gdk.KEY_Left, Gdk.KEY_Up):
                self.taskbar_idx = (self.taskbar_idx - 1) % total
                wid, wtitle, pos, tot = self.taskbar_items[self.taskbar_idx]
                self.speech.speak(f"{wtitle}  botão  {pos} de {tot}")
                return True

        elif region == 'systray' and key in (Gdk.KEY_Left, Gdk.KEY_Right):
            if key == Gdk.KEY_Right:
                self.systray.navigate_right()
            else:
                self.systray.navigate_left()
            return True

        return False
