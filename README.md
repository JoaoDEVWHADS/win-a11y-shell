# win-a11y-shell

**Windows-like Accessible Desktop Shell for Debian Linux** tailored specifically for visually impaired users and screen reader users.

## 🎯 Goal
Provide an exact Windows + NVDA keyboard navigation and speech feedback experience natively on Debian Linux, with zero visual clutter, no animations, high contrast/text focus, and instant keybindings response.

## ⌨️ Keybindings (Identical to Windows)
- `Win + M`: Focus Desktop icon list
- `Win + B`: Focus System Tray (Notification area)
- `Super (Win)`: Toggle Start Menu
- `Win + I`: Open Settings
- `Win + E`: Open Accessible File Explorer
- `Alt + Tab`: Cycle through open windows

## 🚀 Quick Install (Debian / Ubuntu)

```bash
git clone https://github.com/JoaoDEVWHADS/win-a11y-shell.git
cd win-a11y-shell
sudo chmod +x install.sh
sudo ./install.sh
```

## 🏗️ Project Architecture
- **Language:** Python 3 + GTK3 / AT-SPI2 (`PyGObject`)
- **Speech Engine:** Native integration with `speech-dispatcher` & `Orca`
- **Focus Manager:** Accessible focus controller for SysTray, Taskbar, Start Menu & Desktop.
