#!/usr/bin/env python3
"""
win-a11y-shell Core Entrypoint
Accessible Windows-like Desktop Shell for Debian Linux
"""

import sys
import os
from speech import SpeechEngine
from systray import SystemTray

def main():
    print("==================================================")
    print("  win-a11y-shell - Windows Accessibility Shell")
    print("==================================================")
    
    speech = SpeechEngine()
    systray = SystemTray(speech)

    print("\n[Simulação de Navegação - Bandeja do Sistema (Win+B)]")
    print("-> Simulando pressionar Win+B (Foco na Bandeja)...")
    systray.focus()

    print("-> Simulando Seta para Direita (Navegação)...")
    systray.navigate_right()

    print("-> Simulando Seta para Direita...")
    systray.navigate_right()

    print("-> Simulando Enter no primeiro ícone (Mostrar Ícones Ocultos)...")
    systray.current_index = 0
    systray.activate()

    print("-> Simulando Seta para Direita nos Ícones Ocultos...")
    systray.navigate_right()
    systray.navigate_right()

if __name__ == "__main__":
    main()
