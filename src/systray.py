import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from typing import List
from speech import SpeechEngine
from sysinfo import get_real_clock, get_real_volume, get_real_network



class SysTrayItem:
    def __init__(self, name: str, role: str = "botão", value: str = "", key: str = ""):
        self.name = name
        self.role = role
        self.value = value
        self.key = key  # internal identifier

    def announce(self) -> str:
        parts = [self.name]
        if self.value:
            parts.append(self.value)
        parts.append(self.role)
        return "  ".join(parts)


class SystemTray:
    """
    Windows System Tray (Win+B) implementation with dynamic real-system metrics.
    Volume item opens VolumeControlPanel on Enter.
    """
    def __init__(self, speech: SpeechEngine):
        self.speech = speech
        self.focused = False
        self.current_index = 0
        self.show_hidden = False
        self._volume_panel = None  # lazy-init to avoid circular import

    def _get_volume_panel(self):
        if self._volume_panel is None:
            from volumecontrol import VolumeControlPanel
            self._volume_panel = VolumeControlPanel(self.speech, on_close_callback=self._on_volume_closed)
        return self._volume_panel

    def _on_volume_closed(self):
        """Called when VolumeControlPanel is closed with Escape — re-announce the volume button."""
        vol_str = get_real_volume()
        self.speech.speak(f"{vol_str}  botão")

    def get_active_list(self) -> List[SysTrayItem]:
        clock_str = get_real_clock()
        vol_str = get_real_volume()
        net_str = get_real_network()

        if self.show_hidden:
            return [
                SysTrayItem("Gerenciador de Tarefas", role="botão", key="task_manager"),
                SysTrayItem("Configurações do Sistema", role="botão", key="settings"),
                SysTrayItem("Remover Hardware com Segurança", role="botão", key="hw_remove"),
            ]

        return [
            SysTrayItem("Mostrar Ícones Ocultos", role="botão", key="hidden_icons"),
            SysTrayItem(net_str, role="botão", key="network"),
            SysTrayItem(vol_str, role="botão", key="volume"),
            SysTrayItem(f"Relógio {clock_str}", role="botão", key="clock"),
            SysTrayItem("Mostrar Área de Trabalho", role="botão", key="show_desktop"),
        ]

    def focus(self):
        self.focused = True
        self.current_index = 0
        items = self.get_active_list()
        self.speech.speak(items[self.current_index].announce())

    def navigate_right(self):
        items = self.get_active_list()
        self.current_index = (self.current_index + 1) % len(items)
        self.speech.speak(items[self.current_index].announce())

    def navigate_left(self):
        items = self.get_active_list()
        self.current_index = (self.current_index - 1) % len(items)
        self.speech.speak(items[self.current_index].announce())

    def activate(self):
        """Called when Enter is pressed on the focused systray item."""
        items = self.get_active_list()
        item = items[self.current_index]

        if item.key == "hidden_icons":
            self.show_hidden = not self.show_hidden
            self.current_index = 0
            new_items = self.get_active_list()
            self.speech.speak(new_items[0].announce())

        elif item.key == "volume":
            panel = self._get_volume_panel()
            GLib.idle_add(panel.open)

        else:
            self.speech.speak(f"Ativado: {item.name}")
