import tkinter as tk
from tkinter import ttk, messagebox
import os

from .carro import Carro
from .conexion_serial import ConexionSerial, EstadoConexion, PUERTO_PREDETERMINADO
from .sistema_agua import SistemaAgua


try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


ADMIN_PIN = "123"


# Identidad de Marca - Máquina de Proteína
COMPANY_NAME = "UKUMARI"
COMPANY_SLOGAN = "BEAR AND PROUD  •  Estación Dispensadora de Proteína"
LOGO_PATH = os.path.expanduser("~/logo.png")


# Paleta inspirada en el Logo UKUMARI (Negro Carbón + Verde Lima Neón + Blanco)
BG_MAIN = "#F3F6F4"          # Fondo blanco grisáceo limpio
BG_CARD = "#FFFFFF"          # Tarjetas blancas
HEADER_DARK = "#0D110F"      # Negro carbón del trazo del logo
PRIMARY = "#2E8B1A"          # Verde intenso legible en botones con texto blanco
PRIMARY_DARK = "#174D0B"     # Verde oscuro para textos y bordes activos
NEON_GREEN = "#68E01B"       # Verde lima vibrante exacto al rostro del oso
NEON_SOFT = "#E7F9DC"        # Verde lima muy suave para tarjetas en espera
ACCENT_WATER = "#0284C7"     # Azul agua cristalina (dosificación líquida)
SUCCESS = "#16A34A"          # Verde activo
DANGER = "#DC2626"           # Rojo paro de emergencia
TEXT_DARK = "#111815"        # Texto oscuro de alto contraste
TEXT_MUTED = "#4B5E54"       # Texto secundario
BORDER_COLOR = "#C8D6CE"     # Borde sutil




class BandaDualApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{COMPANY_NAME} - BEAR AND PROUD")
        self.root.geometry("800x480")
        self.root.configure(bg=BG_MAIN)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        self.conexion = ConexionSerial(self.process_line, self.update_connection, self.write_terminal)
        self.carro = Carro(self.conexion.enviar)
        self.agua = SistemaAgua(self.conexion.enviar)
        self.pwm_var = tk.IntVar(value=135)
        self.auto_return_var = tk.BooleanVar(value=True)
        self.pending_speed_job = None
        self.current_view = "USER"
        self.logo_img = None

        self.load_company_logo()

        self.container = tk.Frame(self.root, bg=BG_MAIN)
        self.container.pack(fill="both", expand=True)

        self.user_frame = tk.Frame(self.container, bg=BG_MAIN)
        self.admin_frame = tk.Frame(self.container, bg=BG_MAIN)

        self.build_user_ui()
        self.build_admin_ui()

        self.show_user_view()
        self.refresh_ports()
        self.update_connection(EstadoConexion.DESCONECTADO, "")
        self.poll_job = self.root.after(50, self.poll_connection)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_company_logo(self):
        if not os.path.exists(LOGO_PATH):
            return
        try:
            if PIL_AVAILABLE:
                img = Image.open(LOGO_PATH)
                # Logo más grande (64px de alto) para que destaque claramente
                target_h = 64
                ratio = target_h / float(img.height)
                target_w = max(1, int(float(img.width) * ratio))
                img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
            else:
                raw_img = tk.PhotoImage(file=LOGO_PATH)
                if raw_img.height() > 68:
                    factor = max(1, raw_img.height() // 64)
                    raw_img = raw_img.subsample(factor, factor)
                self.logo_img = raw_img
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")
            self.logo_img = None

    # ==================================================
    # NAVEGACIÓN ENTRE VISTAS Y TECLADO PIN
    # ==================================================
    def show_user_view(self):
        self.admin_frame.pack_forget()
        self.user_frame.pack(fill="both", expand=True)
        self.current_view = "USER"

    def show_admin_view(self):
        self.user_frame.pack_forget()
        self.admin_frame.pack(fill="both", expand=True)
        self.current_view = "ADMIN"

    def open_pin_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Acceso Administrador")
        dialog.geometry("320x400")
        dialog.configure(bg=BG_CARD)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 160
        y = (self.root.winfo_screenheight() // 2) - 200
        dialog.geometry(f"+{x}+{y}")

        tk.Label(
            dialog, text=f"{COMPANY_NAME} — PIN Admin",
            font=("Arial", 12, "bold"), bg=BG_CARD, fg=HEADER_DARK
        ).pack(pady=(15, 5))

        pin_var = tk.StringVar(value="")
        display_var = tk.StringVar(value="○ ○ ○")

        lbl_display = tk.Label(
            dialog, textvariable=display_var,
            font=("Arial", 20, "bold"), bg=NEON_SOFT, fg=PRIMARY_DARK,
            width=12, pady=8, relief="flat"
        )
        lbl_display.pack(pady=10)

        lbl_error = tk.Label(dialog, text="", font=("Arial", 9, "bold"), bg=BG_CARD, fg=DANGER)
        lbl_error.pack()

        def update_display():
            entered = pin_var.get()
            dots = " ".join(["●"] * len(entered) + ["○"] * max(0, 3 - len(entered)))
            display_var.set(dots)

        def press_digit(d):
            if len(pin_var.get()) < 6:
                pin_var.set(pin_var.get() + str(d))
                lbl_error.config(text="")
                update_display()

        def clear_pin():
            pin_var.set("")
            lbl_error.config(text="")
            update_display()

        def verify_pin():
            if pin_var.get() == ADMIN_PIN:
                dialog.destroy()
                self.show_admin_view()
            else:
                lbl_error.config(text="PIN incorrecto. Intente de nuevo.")
                pin_var.set("")
                update_display()

        update_display()

        pad = tk.Frame(dialog, bg=BG_CARD)
        pad.pack(pady=10)

        buttons = [
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("Borrar", 3, 0), ("0", 3, 1), ("Entrar", 3, 2)
        ]

        for text, r, c in buttons:
            if text == "Borrar":
                cmd = clear_pin
                bg_btn, fg_btn = "#E2E8F0", TEXT_DARK
            elif text == "Entrar":
                cmd = verify_pin
                bg_btn, fg_btn = PRIMARY, "white"
            else:
                cmd = lambda d=text: press_digit(d)
                bg_btn, fg_btn = NEON_SOFT, PRIMARY_DARK

            tk.Button(
                pad, text=text, command=cmd,
                font=("Arial", 12, "bold"), width=6, height=2,
                bg=bg_btn, fg=fg_btn, relief="flat", cursor="hand2"
            ).grid(row=r, column=c, padx=5, pady=5)

        tk.Button(
            dialog, text="Cancelar", command=dialog.destroy,
            font=("Arial", 10), bg=BG_CARD, fg=TEXT_MUTED, relief="flat"
        ).pack(pady=5)

    # ==================================================
    # 1. INTERFAZ DE USUARIO (MÁQUINA DE PROTEÍNA UKUMARI)
    # ==================================================
    def build_user_ui(self):
        # Barra superior amplia en Negro Carbón con acento Verde Neón
        header = tk.Frame(self.user_frame, bg=HEADER_DARK, height=82)
        header.pack(fill="x")
        header.pack_propagate(False)

        neon_bar = tk.Frame(self.user_frame, bg=NEON_GREEN, height=4)
        neon_bar.pack(fill="x")

        brand_frame = tk.Frame(header, bg=HEADER_DARK)
        brand_frame.pack(side="left", padx=16, pady=6)

        if self.logo_img:
            logo_box = tk.Label(
                brand_frame, image=self.logo_img,
                bg="white", padx=4, pady=2
            )
            logo_box.pack(side="left", padx=(0, 14))

        title_stack = tk.Frame(brand_frame, bg=HEADER_DARK)
        title_stack.pack(side="left")

        tk.Label(
            title_stack, text=COMPANY_NAME,
            font=("Arial", 20, "bold"), bg=HEADER_DARK, fg="white"
        ).pack(anchor="w")

        tk.Label(
            title_stack, text=COMPANY_SLOGAN,
            font=("Arial", 10, "bold"), bg=HEADER_DARK, fg=NEON_GREEN
        ).pack(anchor="w")

        tk.Button(
            header, text="Admin", command=self.open_pin_dialog,
            font=("Arial", 10, "bold"), bg="white", fg=HEADER_DARK,
            padx=14, pady=6, relief="flat", cursor="hand2"
        ).pack(side="right", padx=15)

        self.user_conn_badge = tk.Label(
            header, text="● Conectando...",
            font=("Arial", 9, "bold"), bg=PRIMARY, fg="white", padx=12, pady=5
        )
        self.user_conn_badge.pack(side="right", padx=8)

        # Tarjeta de estado principal y dosificación líquida
        status_card = tk.Frame(
            self.user_frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1
        )
        status_card.pack(fill="x", padx=20, pady=(10, 6))

        self.user_status_lbl = tk.Label(
            status_card, text="COLOQUE SU SHAKER EN INICIO (ESTACIÓN 5)",
            font=("Arial", 13, "bold"), bg=BG_CARD, fg=HEADER_DARK, pady=10
        )
        self.user_status_lbl.pack(side="left", padx=18, expand=True, fill="x")

        self.user_pump_badge = tk.Label(
            status_card, text="[AGUA] BASE AGUA: LISTA",
            font=("Arial", 10, "bold"), bg=NEON_SOFT, fg=PRIMARY_DARK,
            padx=16, pady=9
        )
        self.user_pump_badge.pack(side="right", padx=14, pady=6)

        # Indicador visual de etapas de preparación
        steps_card = tk.Frame(
            self.user_frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1
        )
        steps_card.pack(fill="x", padx=20, pady=5)

        tk.Label(
            steps_card, text="ETAPAS DE PREPARACIÓN DEL BATIDO",
            font=("Arial", 9, "bold"), bg=BG_CARD, fg=TEXT_MUTED
        ).pack(anchor="w", padx=15, pady=(6, 3))

        steps_row = tk.Frame(steps_card, bg=BG_CARD)
        steps_row.pack(fill="x", padx=15, pady=(0, 9))

        self.step_labels = {}
        steps_def = [
            ("STEP_5", "1. Base Líquida\nEst. 5 (Agua 6s)"),
            ("STEP_WORK", "2. Dosificación\nProteína Elegida"),
            ("STEP_1", "3. Entrega Final\nEstación 1"),
            ("STEP_RET", "4. Retorno\na Inicio (Est. 5)")
        ]

        for key, label_text in steps_def:
            lbl = tk.Label(
                steps_row, text=label_text,
                font=("Arial", 9, "bold"), bg=NEON_SOFT, fg=PRIMARY_DARK,
                width=16, pady=8
            )
            lbl.pack(side="left", expand=True, fill="x", padx=4)
            self.step_labels[key] = lbl

        # Panel central de selección de proteína / estación
        action_card = tk.Frame(
            self.user_frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1
        )
        action_card.pack(fill="both", expand=True, padx=20, pady=5)

        tk.Label(
            action_card, text="SELECCIONE SU DOSIS DE PROTEÍNA PARA INICIAR",
            font=("Arial", 11, "bold"), bg=BG_CARD, fg=TEXT_DARK
        ).pack(pady=(8, 4))

        stations_btn_row = tk.Frame(action_card, bg=BG_CARD)
        stations_btn_row.pack(expand=True, fill="x", padx=20)

        station_titles = {
            4: ("ESTACIÓN 4", "Proteína 1  •  ▶ Preparar"),
            3: ("ESTACIÓN 3", "Proteína 2  •  ▶ Preparar"),
            2: ("ESTACIÓN 2", "Proteína 3  •  ▶ Preparar")
        }

        for st in [4, 3, 2]:
            main_t, sub_t = station_titles[st]
            btn = tk.Button(
                stations_btn_row,
                text=f"{main_t}\n{sub_t}",
                font=("Arial", 13, "bold"),
                bg=PRIMARY, fg="white",
                activebackground=HEADER_DARK, activeforeground=NEON_GREEN,
                height=3, relief="flat", cursor="hand2",
                command=lambda n=st: self.carro.iniciar_pedido(n)
            )
            btn.pack(side="left", expand=True, fill="x", padx=10)

        # Barra inferior de seguridad y retorno a inicio
        bottom_bar = tk.Frame(self.user_frame, bg=BG_MAIN)
        bottom_bar.pack(fill="x", padx=20, pady=(5, 12))

        tk.Button(
            bottom_bar, text="LLEVAR SHAKER A INICIO (EST. 5)",
            font=("Arial", 11, "bold"), bg="white", fg=HEADER_DARK,
            highlightbackground=PRIMARY, highlightthickness=2,
            padx=20, pady=10, relief="flat", cursor="hand2",
            command=self.carro.llevar_a_inicio
        ).pack(side="left", expand=True, fill="x", padx=(0, 10))

        tk.Button(
            bottom_bar, text="[STOP] PARO DE EMERGENCIA",
            font=("Arial", 11, "bold"), bg=DANGER, fg="white",
            activebackground="#991B1B", activeforeground="white",
            padx=25, pady=10, relief="flat", cursor="hand2",
            command=self.carro.detener
        ).pack(side="right", expand=True, fill="x", padx=(10, 0))

    def highlight_step(self, active_key):
        for key, lbl in self.step_labels.items():
            if key == active_key:
                lbl.config(bg=NEON_GREEN, fg=HEADER_DARK)
            else:
                lbl.config(bg=NEON_SOFT, fg=PRIMARY_DARK)

    # ==================================================
    # 2. INTERFAZ DE ADMINISTRADOR (MANTENIMIENTO)
    # ==================================================
    def build_admin_ui(self):
        header = tk.Frame(self.admin_frame, bg=HEADER_DARK, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text=f"{COMPANY_NAME} • BEAR AND PROUD — PANEL TÉCNICO",
            font=("Arial", 11, "bold"), bg=HEADER_DARK, fg=NEON_GREEN
        ).pack(side="left", padx=15)

        tk.Button(
            header, text="← Volver a Vista Operador",
            command=self.show_user_view,
            font=("Arial", 10, "bold"), bg="white", fg=HEADER_DARK,
            padx=12, pady=4, relief="flat", cursor="hand2"
        ).pack(side="right", padx=15)

        conn = tk.LabelFrame(
            self.admin_frame, text="Conexión Hardware (ESC sale de pantalla completa)",
            bg=BG_CARD, fg=PRIMARY_DARK, font=("Arial", 9, "bold")
        )
        conn.pack(fill="x", padx=15, pady=5)

        tk.Label(conn, text="Puerto:", bg=BG_CARD, fg=TEXT_DARK).grid(row=0, column=0, padx=6, pady=6)
        self.port_box = ttk.Combobox(conn, state="readonly", width=18)
        self.port_box.grid(row=0, column=1, padx=6, pady=6)

        tk.Button(
            conn, text="Actualizar", command=self.refresh_ports,
            bg=NEON_SOFT, fg=PRIMARY_DARK, relief="flat", padx=10
        ).grid(row=0, column=2, padx=5)

        self.connect_btn = tk.Button(
            conn, text="Conectar", command=self.toggle_connection,
            bg=PRIMARY, fg="white", relief="flat", padx=12
        )
        self.connect_btn.grid(row=0, column=3, padx=5)

        self.connection_status = tk.Label(conn, text="Desconectado", bg=BG_CARD, fg=TEXT_MUTED, font=("Arial", 9, "bold"))
        self.connection_status.grid(row=0, column=4, padx=10)

        diag_frame = tk.LabelFrame(
            self.admin_frame, text="Sensores IR en Vivo (Orden físico: 5 → 4 → 3 → 2 → 1)",
            bg=BG_CARD, fg=PRIMARY_DARK, font=("Arial", 9, "bold")
        )
        diag_frame.pack(fill="x", padx=15, pady=5)

        diag_grid = tk.Frame(diag_frame, bg=BG_CARD)
        diag_grid.pack(pady=6)

        self.sensor_widgets = {}
        stations_info = [
            (5, "Est. 5 (AGUA)"),
            (4, "Estación 4"),
            (3, "Estación 3"),
            (2, "Estación 2"),
            (1, "Est. 1 (ENTREGA)")
        ]

        for col, (st_num, title) in enumerate(stations_info):
            lbl = tk.Label(
                diag_grid, text=f"{title}\n---", width=15,
                bg="#E2E8F0", fg=TEXT_DARK, font=("Arial", 9, "bold"), pady=6
            )
            lbl.grid(row=0, column=col, padx=5)
            self.sensor_widgets[st_num] = (lbl, title)

        ctrl_frame = tk.LabelFrame(
            self.admin_frame, text="Calibración de Banda y Pruebas Manuales",
            bg=BG_CARD, fg=PRIMARY_DARK, font=("Arial", 9, "bold")
        )
        ctrl_frame.pack(fill="x", padx=15, pady=5)

        speed_row = tk.Frame(ctrl_frame, bg=BG_CARD)
        speed_row.pack(fill="x", padx=10, pady=2)

        tk.Label(speed_row, text="Velocidad PWM:", bg=BG_CARD, fg=TEXT_DARK, font=("Arial", 9, "bold")).pack(side="left")
        self.speed_scale = tk.Scale(
            speed_row, from_=0, to=255, orient="horizontal",
            variable=self.pwm_var, length=380, bg=BG_CARD,
            highlightthickness=0, command=self.on_slider_change
        )
        self.speed_scale.pack(side="left", padx=10)

        ttk.Checkbutton(
            speed_row, text="Retorno auto a Est. 5",
            variable=self.auto_return_var, command=self.toggle_auto_return
        ).pack(side="right", padx=5)

        manual_row = tk.Frame(ctrl_frame, bg=BG_CARD)
        manual_row.pack(pady=6)

        btns_admin = [
            ("Avanzar (→ 1)", self.carro.avanzar, NEON_SOFT, PRIMARY_DARK),
            ("STOP", self.carro.detener, DANGER, "white"),
            ("Regresar (→ 5)", self.carro.regresar, NEON_SOFT, PRIMARY_DARK),
            (f"[AGUA] Probar Agua ({self.agua.DURACION_S}s)", self.agua.probar, ACCENT_WATER, "white"),
            ("Invertir Giro", self.carro.invertir, HEADER_DARK, NEON_GREEN),
        ]

        for txt, accion, bg_c, fg_c in btns_admin:
            tk.Button(
                manual_row, text=txt, bg=bg_c, fg=fg_c,
                font=("Arial", 9, "bold"), padx=10, pady=5, relief="flat",
                command=accion
            ).pack(side="left", padx=5)

        monitor = tk.LabelFrame(
            self.admin_frame, text="Consola de Eventos Arduino",
            bg=BG_CARD, fg=PRIMARY_DARK, font=("Arial", 9, "bold")
        )
        monitor.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        self.terminal = tk.Text(monitor, height=6, state="disabled", bg="#F8FAFC", fg=TEXT_DARK, font=("Consolas", 9))
        self.terminal.pack(fill="both", expand=True, padx=6, pady=6)

    def refresh_ports(self):
        seleccionado = self.port_box.get()
        ports = self.conexion.listar_puertos()
        self.port_box["values"] = ports
        if seleccionado in ports:
            self.port_box.set(seleccionado)
        elif PUERTO_PREDETERMINADO in ports:
            self.port_box.set(PUERTO_PREDETERMINADO)
        else:
            self.port_box.set(ports[0] if ports else "")

    def toggle_connection(self):
        if self.conexion.estado in (
            EstadoConexion.CONECTADO, EstadoConexion.CONECTANDO,
            EstadoConexion.RECONECTANDO,
        ):
            self.conexion.desconectar()
        else:
            self.conexion.conectar(self.port_box.get())

    def update_connection(self, estado, detalle):
        conectado = estado is EstadoConexion.CONECTADO
        transitorio = estado in (EstadoConexion.CONECTANDO, EstadoConexion.RECONECTANDO)
        color = SUCCESS if conectado else "#D97706" if transitorio else DANGER
        etiqueta = f"{estado.value} ({detalle})" if conectado or transitorio else estado.value
        self.connection_status.config(text=etiqueta, fg=color)
        self.connect_btn.config(
            text="Desconectar" if conectado or transitorio else "Conectar",
            bg=DANGER if conectado or transitorio else PRIMARY,
        )
        self.port_box.config(state="disabled" if conectado or transitorio else "readonly")
        self.user_conn_badge.config(
            text="● Sistema Conectado" if conectado else f"● {estado.value}",
            bg=PRIMARY if conectado else color,
        )
        if not conectado:
            self.cancel_speed_job()
            self.carro.sensores_ir.clear()
            for lbl, title in self.sensor_widgets.values():
                lbl.config(text=f"{title}\n---", bg="#E2E8F0", fg=TEXT_DARK)
        if estado is EstadoConexion.ERROR:
            messagebox.showerror("Error de Conexión", detalle, parent=self.root)

    def poll_connection(self):
        self.conexion.sondear()
        self.poll_job = self.root.after(50, self.poll_connection)

    def toggle_auto_return(self):
        self.carro.fijar_retorno(self.auto_return_var.get())

    def cancel_speed_job(self):
        if self.pending_speed_job is not None:
            self.root.after_cancel(self.pending_speed_job)
            self.pending_speed_job = None

    def on_slider_change(self, _=None):
        self.cancel_speed_job()
        if self.conexion.estado is EstadoConexion.CONECTADO:
            self.pending_speed_job = self.root.after(100, self.apply_speed)

    def apply_speed(self):
        self.pending_speed_job = None
        self.carro.fijar_velocidad(self.pwm_var.get())

    def process_line(self, line):
        if self.carro.actualizar_sensores(line):
            for estacion, detectado in self.carro.sensores_ir.items():
                lbl, title = self.sensor_widgets[estacion]
                estado = "DETECTADO" if detectado else "LIBRE"
                lbl.config(text=f"{title}\n{estado}", bg=DANGER if detectado else SUCCESS, fg="white")
            return

        self.write_terminal(line)

        bomba_encendida = self.agua.estado_bomba(line)
        if bomba_encendida:
            self.user_pump_badge.config(text="[AGUA] SIRVIENDO AGUA...", bg=ACCENT_WATER, fg="white")
            self.user_status_lbl.config(text=f"SIRVIENDO BASE DE AGUA EN ESTACIÓN 5 ({self.agua.DURACION_S}s)...", fg=ACCENT_WATER)
            self.highlight_step("STEP_5")
            return

        if bomba_encendida is False:
            self.user_pump_badge.config(text="[AGUA] BASE AGUA: LISTA", bg=NEON_SOFT, fg=PRIMARY_DARK)

        if "Avanzando de 5" in line or "LLEGADO A ESTACION 4" in line or "LLEGADO A ESTACION 3" in line or "LLEGADO A ESTACION 2" in line:
            self.highlight_step("STEP_WORK")
            self.user_status_lbl.config(text=line.upper(), fg=PRIMARY)
        elif "Continuando hacia Estacion 1" in line or "LLEGADO A ESTACION 1" in line:
            self.highlight_step("STEP_1")
            self.user_status_lbl.config(text=line.upper(), fg=PRIMARY)
        elif "Regresando a Estacion 5" in line or "Buscando inicio" in line or "Moviendo primero" in line:
            self.highlight_step("STEP_RET")
            self.user_status_lbl.config(text=line.upper(), fg=PRIMARY)
        elif "CICLO COMPLETADO" in line or "LISTO:" in line or "FINALIZADO" in line:
            self.highlight_step(None)
            self.user_pump_badge.config(text="[AGUA] BASE AGUA: LISTA", bg=NEON_SOFT, fg=PRIMARY_DARK)
            self.user_status_lbl.config(text=f"BATIDO LISTO — {line.upper()}", fg=SUCCESS)
        elif "ERROR:" in line:
            self.highlight_step(None)
            self.user_pump_badge.config(text="[AGUA] BASE AGUA: LISTA", bg=NEON_SOFT, fg=PRIMARY_DARK)
            self.user_status_lbl.config(text=f"ERROR: {line}", fg=DANGER)
        elif "detenido" in line:
            self.highlight_step(None)
            self.user_pump_badge.config(text="[AGUA] BOMBA DETENIDA", bg="#FEE2E2", fg=DANGER)
            self.user_status_lbl.config(text="[STOP] SISTEMA DETENIDO POR EMERGENCIA", fg=DANGER)

    def write_terminal(self, text):
        self.terminal.config(state="normal")
        self.terminal.insert("end", text + "\n")
        self.terminal.see("end")
        self.terminal.config(state="disabled")

    def on_close(self):
        self.root.after_cancel(self.poll_job)
        self.cancel_speed_job()
        self.carro.detener()
        self.conexion.desconectar()
        self.root.destroy()


def main():
    root = tk.Tk()
    BandaDualApp(root)
    root.mainloop()
