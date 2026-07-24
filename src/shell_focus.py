import os
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Atk

from speech import SpeechEngine
from systray import SystemTray
from taskbar import get_running_windows, activate_window
from login import AccessibleLoginWindow
from startmenu import StartMenuWindow

class WindowsFocusController(Gtk.Window):
    """
    Unified Windows + NVDA Focus Controller.
    Clean accessibility labels without forcing keep_above window lock, allowing full Alt+Tab and external window focus.
    """
    REGIONS = ['desktop', 'start', 'taskbar', 'systray']

    def __init__(self, speech: SpeechEngine):
        super().__init__()
        self.set_title("")
        self.speech = speech
        self.systray = SystemTray(speech)
        self.login_window = AccessibleLoginWindow(speech)
        self.start_menu = StartMenuWindow(speech, on_close_callback=self._on_start_menu_closed)
        
        # Clear ATK accessible name so Orca does not speak any window title
        atk_win = self.get_accessible()
        if atk_win:
            atk_win.set_name("")

        self.current_region_idx = 0
        self.desktop_items = []
        self.desktop_idx = 0

        self.taskbar_items = []
        self.taskbar_idx = 0

        self.set_default_size(800, 500)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Do NOT force set_keep_above(True) so external windows like Terminal/TeamTalk can take full focus
        self.set_keep_above(False)

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

    def _on_start_menu_closed(self):
        """Called when StartMenuWindow is closed with Escape — return focus to 'start' region."""
        self.focus_region('start')

    def reload_real_desktop(self):
        items = []
        desktop_dir = os.path.expanduser("~/Desktop")
        if os.path.exists(desktop_dir):
            for entry in sorted(os.listdir(desktop_dir)):
                if not entry.startswith('.'):
                    items.append((entry, os.path.join(desktop_dir, entry)))

        if not items:
            items = [("Nenhum item na Área de Trabalho", "folder")]

        self.desktop_items = items

    def focus_region(self, region_name: str):
        if region_name in self.REGIONS:
            self.current_region_idx = self.REGIONS.index(region_name)
        self.render_region()

    def cycle_tab(self):
        self.current_region_idx = (self.current_region_idx + 1) % len(self.REGIONS)
        self.render_region()

    def cycle_tab_reverse(self):
        self.current_region_idx = (self.current_region_idx - 1) % len(self.REGIONS)
        self.render_region()

    def render_region(self):
        region = self.REGIONS[self.current_region_idx]
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        rows_to_focus = []

        if region == 'desktop':
            self.reload_real_desktop()
            total = len(self.desktop_items)
            self.label_region.set_text("Desktop (Área de Trabalho)")

            for idx, (name, _) in enumerate(self.desktop_items, start=1):
                row = Gtk.ListBoxRow()
                row.set_can_focus(True)
                text = f"{name}  {idx} de {total}"
                label = Gtk.Label(label=text)
                label.set_xalign(0)
                row.add(label)

                atk_row = row.get_accessible()
                atk_row.set_name(text)
                atk_row.set_role(Atk.Role.LIST_ITEM)
                self.listbox.add(row)
                rows_to_focus.append(row)

        elif region == 'start':
            text = "Iniciar  botão de alternância  não pressionado"
            self.label_region.set_text("Menu Iniciar")
            row = Gtk.ListBoxRow()
            row.set_can_focus(True)
            label = Gtk.Label(label=text)
            label.set_xalign(0)
            row.add(label)

            atk_row = row.get_accessible()
            atk_row.set_name(text)
            atk_row.set_role(Atk.Role.TOGGLE_BUTTON)
            self.listbox.add(row)
            rows_to_focus.append(row)

        elif region == 'taskbar':
            self.taskbar_items = get_running_windows()
            self.label_region.set_text("Barra de Tarefas (Janelas em execução)")

            for wid, wtitle, pos, tot in self.taskbar_items:
                text = f"{wtitle}  botão  {pos} de {tot}"
                row = Gtk.ListBoxRow()
                row.set_can_focus(True)
                label = Gtk.Label(label=text)
                label.set_xalign(0)
                row.add(label)

                atk_row = row.get_accessible()
                atk_row.set_name(text)
                atk_row.set_role(Atk.Role.PUSH_BUTTON)
                self.listbox.add(row)
                rows_to_focus.append(row)

        elif region == 'systray':
            self.label_region.set_text("Bandeja do Sistema")
            items = self.systray.get_active_list()
            for item in items:
                text = item.announce()
                row = Gtk.ListBoxRow()
                row.set_can_focus(True)
                label = Gtk.Label(label=text)
                label.set_xalign(0)
                row.add(label)

                atk_row = row.get_accessible()
                atk_row.set_name(text)
                atk_row.set_role(Atk.Role.PUSH_BUTTON)
                self.listbox.add(row)
                rows_to_focus.append(row)

        self.show_all()
        self.present()
        try:
            wid = hex(self.get_window().get_xid())
            subprocess.Popen(["xdotool", "windowactivate", "--sync", wid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        target_idx = 0
        if region == 'desktop':
            target_idx = min(self.desktop_idx, max(0, len(rows_to_focus) - 1))
        elif region == 'taskbar':
            target_idx = min(self.taskbar_idx, max(0, len(rows_to_focus) - 1))

        if rows_to_focus and 0 <= target_idx < len(rows_to_focus):
            target_row = rows_to_focus[target_idx]
            self.listbox.select_row(target_row)
            target_row.grab_focus()
            self.speech.speak(target_row.get_accessible().get_name(), target_row)

    def on_key_press(self, widget, event):
        key = event.keyval
        state = event.state
        region = self.REGIONS[self.current_region_idx]

        is_shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        if key == Gdk.KEY_Tab:
            if is_shift:
                self.cycle_tab_reverse()
            else:
                self.cycle_tab()
            return True
        elif key == Gdk.KEY_Escape:
            self.hide()
            return True
        elif key == Gdk.KEY_Return or key == Gdk.KEY_KP_Enter:
            if region == 'start':
                # Open the Start Menu
                self.hide()
                self.start_menu.open()
                return True
            elif region == 'taskbar' and self.taskbar_items:
                selected_row = self.listbox.get_selected_row()
                idx = selected_row.get_index() if selected_row else self.taskbar_idx
                if 0 <= idx < len(self.taskbar_items):
                    wid, wtitle, pos, tot = self.taskbar_items[idx]
                    self.hide()
                    activate_window(wid)
                    return True
            elif region == 'desktop' and self.desktop_items:
                selected_row = self.listbox.get_selected_row()
                idx = selected_row.get_index() if selected_row else self.desktop_idx
                if 0 <= idx < len(self.desktop_items):
                    name, path = self.desktop_items[idx]
                    self.hide()
                    if path != "folder":
                        subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
            elif region == 'systray':
                self.systray.activate()
                return True

        children = self.listbox.get_children()
        total_children = len(children)

        if region == 'desktop' and total_children > 0:
            if key in (Gdk.KEY_Right, Gdk.KEY_Down):
                self.desktop_idx = (self.desktop_idx + 1) % total_children
                row = children[self.desktop_idx]
                self.listbox.select_row(row)
                row.grab_focus()
                self.speech.speak(row.get_accessible().get_name(), row)
                return True
            elif key in (Gdk.KEY_Left, Gdk.KEY_Up):
                self.desktop_idx = (self.desktop_idx - 1) % total_children
                row = children[self.desktop_idx]
                self.listbox.select_row(row)
                row.grab_focus()
                self.speech.speak(row.get_accessible().get_name(), row)
                return True

        elif region == 'taskbar' and total_children > 0:
            if key in (Gdk.KEY_Right, Gdk.KEY_Down):
                self.taskbar_idx = (self.taskbar_idx + 1) % total_children
                row = children[self.taskbar_idx]
                self.listbox.select_row(row)
                row.grab_focus()
                self.speech.speak(row.get_accessible().get_name(), row)
                return True
            elif key in (Gdk.KEY_Left, Gdk.KEY_Up):
                self.taskbar_idx = (self.taskbar_idx - 1) % total_children
                row = children[self.taskbar_idx]
                self.listbox.select_row(row)
                row.grab_focus()
                self.speech.speak(row.get_accessible().get_name(), row)
                return True

        elif region == 'systray' and total_children > 0:
            if key in (Gdk.KEY_Right, Gdk.KEY_Down):
                self.systray.navigate_right()
                idx = self.systray.current_index % total_children
                row = children[idx]
                self.listbox.select_row(row)
                row.grab_focus()
                return True
            elif key in (Gdk.KEY_Left, Gdk.KEY_Up):
                self.systray.navigate_left()
                idx = self.systray.current_index % total_children
                row = children[idx]
                self.listbox.select_row(row)
                row.grab_focus()
                return True

        return False
