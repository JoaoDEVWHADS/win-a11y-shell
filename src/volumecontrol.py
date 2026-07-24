import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Atk, GLib

from speech import SpeechEngine
from sysinfo import get_volume_percent, set_volume_percent, toggle_mute, get_mute_state


class VolumeControlPanel(Gtk.Window):
    """
    Accessible Volume Control Panel — same pattern as shell_focus.py.

    Uses ListBoxRow + grab_focus() on row + xdotool windowactivate.

    Focus items:
      0 = Slider  (Up/Down/Left/Right to change volume)
      1 = Mute button (Enter/Space to toggle)

    Tab: next item
    Shift+Tab: previous item
    Escape: close and run on_close_callback
    """

    ITEMS = ['slider', 'mute']

    def __init__(self, speech: SpeechEngine, on_close_callback=None):
        super().__init__()
        self.speech = speech
        self.on_close_callback = on_close_callback
        self._focus_idx = 0

        self.set_title("")
        self.set_default_size(400, 180)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)
        self.set_can_focus(True)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)

        # Clear ATK window name
        atk_win = self.get_accessible()
        if atk_win:
            atk_win.set_name("Configurações rápidas  grupo")

        # Layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.box.set_margin_top(15)
        self.box.set_margin_bottom(15)
        self.box.set_margin_start(15)
        self.box.set_margin_end(15)
        self.add(self.box)

        # Group header label
        header = Gtk.Label(label="Configurações rápidas")
        header.set_xalign(0)
        self.box.pack_start(header, False, False, 0)

        # ListBox — same as shell_focus
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.box.pack_start(self.listbox, True, True, 0)

        # Row 0: Slider
        self.row_slider = Gtk.ListBoxRow()
        self.row_slider.set_can_focus(True)
        self.lbl_slider = Gtk.Label(label="")
        self.lbl_slider.set_xalign(0)
        self.row_slider.add(self.lbl_slider)
        atk_slider = self.row_slider.get_accessible()
        atk_slider.set_role(Atk.Role.SLIDER)
        self.listbox.add(self.row_slider)

        # Row 1: Mute toggle
        self.row_mute = Gtk.ListBoxRow()
        self.row_mute.set_can_focus(True)
        self.lbl_mute = Gtk.Label(label="")
        self.lbl_mute.set_xalign(0)
        self.row_mute.add(self.lbl_mute)
        atk_mute = self.row_mute.get_accessible()
        atk_mute.set_role(Atk.Role.TOGGLE_BUTTON)
        self.listbox.add(self.row_mute)

        self.connect("key-press-event", self.on_key_press)

    def _rows(self):
        return [self.row_slider, self.row_mute]

    def _refresh_atk(self):
        vol = get_volume_percent()
        muted = get_mute_state()

        slider_text = f"Saída de som  deslizante  {vol}"
        self.lbl_slider.set_text(slider_text)
        self.row_slider.get_accessible().set_name(slider_text)

        mute_state = "pressionado" if muted else "não pressionado"
        mute_text = f"Ativar mudo do volume  botão de alternância  {mute_state}  2 de 2"
        self.lbl_mute.set_text(mute_text)
        self.row_mute.get_accessible().set_name(mute_text)

    def _focus_row(self, idx: int, speak: bool = True):
        self._focus_idx = idx
        self._refresh_atk()
        rows = self._rows()
        row = rows[idx]
        self.listbox.select_row(row)
        row.grab_focus()
        if speak:
            self.speech.speak(row.get_accessible().get_name())

    def open(self):
        self._focus_idx = 0
        self._refresh_atk()
        self.show_all()
        self.present()

        # Force X11 focus — same pattern as shell_focus.py
        try:
            wid = hex(self.get_window().get_xid())
            subprocess.Popen(
                ["xdotool", "windowactivate", "--sync", wid],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

        # Speak group name first, then focus slider
        self.speech.speak("Configurações rápidas  grupo")
        GLib.timeout_add(350, self._open_delayed)
        return False  # GLib.idle_add compatible

    def _open_delayed(self):
        self._focus_row(0, speak=True)
        return False

    def on_key_press(self, widget, event):
        key = event.keyval
        is_shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)

        # Escape — close and return to caller
        if key == Gdk.KEY_Escape:
            self.hide()
            if self.on_close_callback:
                self.on_close_callback()
            return True

        # Tab / Shift+Tab — switch between slider and mute
        if key in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab):
            if is_shift:
                self._focus_row((self._focus_idx - 1) % len(self.ITEMS))
            else:
                self._focus_row((self._focus_idx + 1) % len(self.ITEMS))
            return True

        # Slider controls
        if self._focus_idx == 0:
            if key in (Gdk.KEY_Up, Gdk.KEY_Right):
                vol = min(100, get_volume_percent() + 5)
                set_volume_percent(vol)
                self._refresh_atk()
                self.speech.speak(str(vol))
                return True
            if key in (Gdk.KEY_Down, Gdk.KEY_Left):
                vol = max(0, get_volume_percent() - 5)
                set_volume_percent(vol)
                self._refresh_atk()
                self.speech.speak(str(vol))
                return True

        # Mute toggle
        if self._focus_idx == 1:
            if key in (Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space):
                toggle_mute()
                self._refresh_atk()
                muted = get_mute_state()
                mute_state = "pressionado" if muted else "não pressionado"
                self.speech.speak(f"Ativar mudo do volume  botão de alternância  {mute_state}")
                return True

        return False
