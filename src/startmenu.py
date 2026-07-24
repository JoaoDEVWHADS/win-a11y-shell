import os
import subprocess
import configparser
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Atk

from speech import SpeechEngine


def _parse_desktop_file(path: str):
    """Parse a .desktop file and return (Name, Exec) or None if not showable."""
    try:
        config = configparser.RawConfigParser()
        config.read(path, encoding='utf-8')
        section = 'Desktop Entry'
        if not config.has_section(section):
            return None
        # Skip hidden / NoDisplay entries
        if config.get(section, 'NoDisplay', fallback='false').lower() == 'true':
            return None
        if config.get(section, 'Hidden', fallback='false').lower() == 'true':
            return None
        # Only Applications
        entry_type = config.get(section, 'Type', fallback='')
        if entry_type != 'Application':
            return None
        name = config.get(section, 'Name', fallback='').strip()
        exec_cmd = config.get(section, 'Exec', fallback='').strip()
        if not name or not exec_cmd:
            return None
        return name, exec_cmd
    except Exception:
        return None


def _clean_exec(exec_str: str) -> list:
    """Remove field codes (%f, %u, etc.) and return as a list of args."""
    parts = []
    for part in exec_str.split():
        if not part.startswith('%'):
            parts.append(part)
    return parts


def _get_all_apps() -> list:
    """Return sorted list of (name, exec_args) for all installed apps."""
    apps = {}
    search_dirs = [
        '/usr/share/applications',
        '/usr/local/share/applications',
        os.path.expanduser('~/.local/share/applications'),
    ]
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith('.desktop'):
                continue
            path = os.path.join(d, fname)
            result = _parse_desktop_file(path)
            if result:
                name, exec_str = result
                if name not in apps:
                    apps[name] = _clean_exec(exec_str)
    return sorted(apps.items(), key=lambda x: x[0].lower())


class StartMenuWindow(Gtk.Window):
    """
    Accessible Start Menu — lists all installed system applications.

    Navigation:
    - Down/Up arrows or Tab/Shift+Tab: navigate items
    - Enter: launch selected app
    - Escape: close and return focus to the desktop shell
    """

    def __init__(self, speech: SpeechEngine, on_close_callback=None):
        super().__init__()
        self.speech = speech
        self.on_close_callback = on_close_callback
        self._apps = []
        self._current_idx = 0

        self.set_title("")
        self.set_default_size(600, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)

        atk_win = self.get_accessible()
        if atk_win:
            atk_win.set_name("Menu Iniciar")

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.box.set_margin_top(15)
        self.box.set_margin_bottom(15)
        self.box.set_margin_start(15)
        self.box.set_margin_end(15)
        self.add(self.box)

        self.header_label = Gtk.Label(label="Menu Iniciar")
        self.header_label.set_xalign(0)
        self.box.pack_start(self.header_label, False, False, 0)

        # Scrollable list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.box.pack_start(scroll, True, True, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scroll.add(self.listbox)

        self.connect("key-press-event", self.on_key_press)

    def _populate(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        self._apps = _get_all_apps()
        total = len(self._apps)

        for idx, (name, _) in enumerate(self._apps, start=1):
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

        self.show_all()

    def open(self):
        self._populate()
        self._current_idx = 0
        self.present()
        self._select(0, announce=True)

    def _select(self, idx: int, announce: bool = False):
        children = self.listbox.get_children()
        if not children:
            return
        idx = max(0, min(idx, len(children) - 1))
        self._current_idx = idx
        row = children[idx]
        self.listbox.select_row(row)
        row.grab_focus()
        if announce:
            self.speech.speak(row.get_accessible().get_name())

    def on_key_press(self, widget, event):
        key = event.keyval
        is_shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)
        children = self.listbox.get_children()
        total = len(children)

        if key == Gdk.KEY_Escape:
            self.hide()
            if self.on_close_callback:
                self.on_close_callback()
            return True

        if key in (Gdk.KEY_Down, Gdk.KEY_Right) or (key == Gdk.KEY_Tab and not is_shift):
            self._select((self._current_idx + 1) % total, announce=True)
            return True

        if key in (Gdk.KEY_Up, Gdk.KEY_Left) or (key == Gdk.KEY_Tab and is_shift):
            self._select((self._current_idx - 1) % total, announce=True)
            return True

        if key in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if 0 <= self._current_idx < len(self._apps):
                name, exec_args = self._apps[self._current_idx]
                self.hide()
                self.speech.speak(f"Abrindo {name}")
                try:
                    subprocess.Popen(exec_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    print(f"[StartMenu] Erro ao abrir {name}: {e}")
            return True

        return False
