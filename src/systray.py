from typing import List, Dict, Any
from speech import SpeechEngine

class SysTrayItem:
    def __init__(self, name: str, role: str = "botão", value: str = "", position: int = 1, total: int = 1, hidden: bool = False):
        self.name = name
        self.role = role
        self.value = value
        self.position = position
        self.total = total
        self.hidden = hidden

    def announce(self) -> str:
        parts = [self.name]
        if self.value:
            parts.append(self.value)
        parts.append(self.role)
        if self.total > 1:
            parts.append(f"{self.position} de {self.total}")
        return "  ".join(parts)


class SystemTray:
    """
    Windows System Tray (Win+B) implementation with exact NVDA focus & key navigation behavior.
    """
    def __init__(self, speech: SpeechEngine):
        self.speech = speech
        self.focused = False
        self.current_index = 0
        self.show_hidden = False
        
        # Default system items matching Windows SysTray structure
        self.main_items: List[SysTrayItem] = []
        self.hidden_items: List[SysTrayItem] = []
        self.reload_items()

    def reload_items(self):
        """Populate system tray items (Volume, Network, Battery, Clock, Microphones, Hidden Icons)."""
        self.main_items = [
            SysTrayItem("Mostrar Ícones Ocultos Mostrar ícones ocultos", role="botão", position=1, total=7),
            SysTrayItem("Privacidade Microfone em uso por: TeamTalk Conferencing Client", role="botão", position=2, total=7),
            SysTrayItem("Rede Orochi-5G Acesso à Internet", role="botão", position=3, total=7),
            SysTrayItem("Volume Headphone (Realtek(R) Audio): 100%", role="botão", position=4, total=7),
            SysTrayItem("Ligar/Desligar Status da bateria: totalmente carregada 100%", role="botão", position=5, total=7),
            SysTrayItem("Relógio 09:48 24/07/2026", role="botão", position=6, total=7),
            SysTrayItem("Mostrar Área de Trabalho Mostrar área de trabalho", role="botão", position=7, total=7),
        ]
        
        self.hidden_items = [
            SysTrayItem("No virtual machines running Virtual machines running: 1", role="botão", position=1, total=4, hidden=True),
            SysTrayItem("NVDA", role="botão", position=2, total=4, hidden=True),
            SysTrayItem("Google Drive", role="botão", position=3, total=4, hidden=True),
            SysTrayItem("Remover Hardware e Ejetar Mídia com Segurança", role="botão", position=4, total=4, hidden=True),
        ]

    def focus(self):
        """Focus the System Tray (Triggered via Win+B)."""
        self.focused = True
        self.current_index = 0
        active_list = self.get_active_list()
        item = active_list[self.current_index]
        self.speech.speak(item.announce())

    def get_active_list(self) -> List[SysTrayItem]:
        return self.hidden_items if self.show_hidden else self.main_items

    def navigate_right(self):
        if not self.focused:
            return
        active_list = self.get_active_list()
        self.current_index = (self.current_index + 1) % len(active_list)
        item = active_list[self.current_index]
        self.speech.speak(item.announce())

    def navigate_left(self):
        if not self.focused:
            return
        active_list = self.get_active_list()
        self.current_index = (self.current_index - 1) % len(active_list)
        item = active_list[self.current_index]
        self.speech.speak(item.announce())

    def activate(self):
        """Press Enter or Space on the focused tray item."""
        if not self.focused:
            return
        active_list = self.get_active_list()
        item = active_list[self.current_index]
        
        if "Mostrar Ícones Ocultos" in item.name:
            self.show_hidden = not self.show_hidden
            self.current_index = 0
            new_list = self.get_active_list()
            self.speech.speak(new_list[0].announce())
        else:
            self.speech.speak(f"Ativado: {item.name}")
