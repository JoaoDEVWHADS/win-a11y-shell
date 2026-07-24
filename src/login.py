import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from speech import SpeechEngine

class AccessibleLoginWindow(Gtk.Window):
    """
    Accessible Login Screen Window.
    Includes Username entry, Password entry, and Login button with full screen reader speech.
    """
    def __init__(self, speech: SpeechEngine, on_success_callback=None):
        super().__init__(title="Tela de Login")
        self.speech = speech
        self.on_success_callback = on_success_callback

        self.set_default_size(500, 350)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.box.set_margin_top(25)
        self.box.set_margin_bottom(25)
        self.box.set_margin_start(25)
        self.box.set_margin_end(25)
        self.add(self.box)

        # Header
        self.header = Gtk.Label(label="Entrar no Debian")
        self.header.set_xalign(0)
        self.box.pack_start(self.header, False, False, 0)

        # Username Field
        self.lbl_user = Gtk.Label(label="Nome de Usuário")
        self.lbl_user.set_xalign(0)
        self.box.pack_start(self.lbl_user, False, False, 0)
        
        self.txt_user = Gtk.Entry()
        self.txt_user.set_placeholder_text("Digite seu nome de usuário")
        self.box.pack_start(self.txt_user, False, False, 0)

        # Password Field
        self.lbl_pass = Gtk.Label(label="Senha")
        self.lbl_pass.set_xalign(0)
        self.box.pack_start(self.lbl_pass, False, False, 0)
        
        self.txt_pass = Gtk.Entry()
        self.txt_pass.set_visibility(False)
        self.txt_pass.set_placeholder_text("Digite sua senha")
        self.box.pack_start(self.txt_pass, False, False, 0)

        # Login Button
        self.btn_login = Gtk.Button(label="Entrar")
        self.box.pack_start(self.btn_login, False, False, 10)

        # Events
        self.txt_user.connect("focus-in-event", lambda w, e: self.speech.speak("Caixa de edição  Nome de usuário  em branco"))
        self.txt_pass.connect("focus-in-event", lambda w, e: self.speech.speak("Caixa de edição  Senha  protegida"))
        self.btn_login.connect("focus-in-event", lambda w, e: self.speech.speak("Entrar  botão"))
        self.btn_login.connect("clicked", self.do_login)

        self.connect("key-press-event", self.on_key_press)

    def do_login(self, button=None):
        username = self.txt_user.get_text().strip()
        password = self.txt_pass.get_text().strip()

        if not username:
            self.speech.speak("Por favor, digite o nome de usuário.")
            self.txt_user.grab_focus()
            return

        self.speech.speak(f"Bem vindo {username}. Autenticado com sucesso.")
        self.hide()
        if self.on_success_callback:
            self.on_success_callback()

    def on_key_press(self, widget, event):
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.do_login()
            return True
        elif event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def open_login(self):
        self.show_all()
        self.present()
        self.txt_user.grab_focus()
        self.speech.speak("Tela de login  Caixa de edição  Nome de usuário  em branco")
