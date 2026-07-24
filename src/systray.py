from typing import List
from speech import SpeechEngine
from sysinfo import get_real_clock, get_real_volume, get_real_network

class SysTrayItem:
    def __init__(self, name: str, role: str = "botão", value: str = ""):
        self.name = name
        self.role = role
        self.value = value

    def announce(self) -> str:
        parts = [self.name]
        if self.value:
            parts.append(self.value)
        parts.append(self.role)
        return "  ".join(parts)


class SystemTray:
    """
    Windows System Tray (Win+B) implementation with dynamic real-system metrics.
    No position numbers (e.g. '1 de 7' removed).
    """
    def __init__(self, speech: SpeechEngine):
        self.speech = speech
        self.focused = False
        self.current_index = 0
        self.show_hidden = False

    def get_active_list(self) -> List[SysTrayItem]:
        clock_str = get_real_clock()
        vol_str = get_real_volume()
        net_str = get_real_network()

        if self.show_hidden:
            return [
                SysTrayItem("Gerenciador de Tarefas", role="botão"),
                SysTrayItem("Configurações do Sistema", role="botão"),
                SysTrayItem("Remover Hardware com Segurança", role="botão"),
            ]
        
        return [
            SysTrayItem("Mostrar Ícones Ocultos", role="botão"),
            SysTrayItem(net_str, role="botão"),
            SysTrayItem(vol_str, role="botão"),
            SysTrayItem(f"Relógio {clock_str}", role="botão"),
            SysTrayItem("Mostrar Área de Trabalho", role="botão"),
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
        items = self.get_active_list()
        item = items[self.current_index]
        if "Mostrar Ícones Ocultos" in item.name:
            self.show_hidden = not self.show_hidden
            self.current_index = 0
            new_items = self.get_active_list()
            self.speech.speak(new_items[0].announce())
        else:
            self.speech.speak(f"Ativado: {item.name}")
