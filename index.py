import json
import os
import unicodedata
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

ARCHIVO = "db.json"

# ------------------ Funciones base ------------------

def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

def cargar_datos():
    if not os.path.exists(ARCHIVO):
        return []
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "clientes" in data:
                return data["clientes"]
            else:
                return []
    except (json.JSONDecodeError, IOError):
        return []

def guardar_datos(data):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ------------------ Interfaz gráfica ------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Control de Reparto de Huevos")
        self.root.geometry("950x600")
        self.root.configure(bg="#f9fafb")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e8ecf0")
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)

        self.data = cargar_datos()

        frame = tk.Frame(root, padx=10, pady=10, bg="#f9fafb")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="📋 Control de Reparto", font=("Segoe UI", 14, "bold"), bg="#f9fafb", fg="#333").grid(row=0, column=0, columnspan=5, pady=(0, 5))

        botones = [
            ("➕ Agregar cliente", self.ventana_agregar_cliente),
            ("🥚 Nuevo pedido", self.ventana_nuevo_pedido),
            ("📦 Generar reparto", self.generar_reparto),
            ("🚪 Salir", root.quit)
        ]
        for i, (text, cmd) in enumerate(botones):
            ttk.Button(frame, text=text, width=20, command=cmd).grid(row=1, column=i, padx=5, pady=5)

        self.tree = ttk.Treeview(
            frame,
            columns=("Nombre", "RUT", "Dirección", "Comuna", "Pendiente a entrega", "Total histórico"),
            show="headings",
            height=15
        )

        for col in ("Nombre", "RUT", "Dirección", "Comuna", "Pendiente a entrega", "Total histórico"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.grid(row=2, column=0, columnspan=5, pady=10)

        self.label_total = tk.Label(frame, text="", bg="#f9fafb", fg="#444", font=("Segoe UI", 10, "bold"))
        self.label_total.grid(row=3, column=0, columnspan=5, pady=(5, 0))

        tk.Label(frame, text="Versión 1.1.0", fg="#888", font=("Segoe UI", 9, "italic"), bg="#f9fafb").grid(row=4, column=0, columnspan=5, pady=(5, 0))

        self.ver_clientes()

    # ------------------ Funciones principales ------------------

    def ver_clientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        clientes_ordenados = sorted(self.data, key=lambda c: c["cajas_de_huevos"], reverse=True)
        total_pendiente = 0

        for c in clientes_ordenados:
            total_pendiente += c["cajas_de_huevos"]
            self.tree.insert("", "end", values=(
                c["nombre_completo"],
                c.get("rut", ""),
                c["direccion"],
                c["comuna"],
                c["cajas_de_huevos"],
                c["cajas_de_huevos_total"]
            ))

        self.label_total.config(text=f"🥚 Total de cajas pendientes a entrega: {total_pendiente}")

    def ventana_agregar_cliente(self):
        win = tk.Toplevel(self.root)
        win.title("Agregar Cliente")
        win.geometry("320x330")
        win.resizable(False, False)
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        labels = [
            ("Nombre completo", "Ej: Juan Pérez González"),
            ("RUT (opcional)", "Ej: 12.345.678-9"),
            ("Dirección", "Ej: Av. Los Leones 345"),
            ("Comuna", "Ej: Las Condes"),
            ("Cajas iniciales", "Ej: 5")
        ]

        entries = []
        for label_text, placeholder in labels:
            tk.Label(win, text=label_text, bg="#f7f9fb").pack(pady=(6, 0))
            entry = tk.Entry(win, width=35, fg="#777")
            entry.insert(0, placeholder)

            def on_focus_in(e, text=placeholder, ent=entry):
                if ent.get() == text:
                    ent.delete(0, "end")
                    ent.config(fg="#000")

            def on_focus_out(e, text=placeholder, ent=entry):
                if not ent.get():
                    ent.insert(0, text)
                    ent.config(fg="#777")

            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)
            entry.pack()
            entries.append((entry, placeholder))

        def agregar():
            try:
                nombre = entries[0][0].get().strip()
                rut = entries[1][0].get().strip()
                direccion = entries[2][0].get().strip()
                comuna = entries[3][0].get().strip()
                cajas_str = entries[4][0].get().strip()
                cajas = int(cajas_str) if cajas_str.isdigit() else 0

                # Validación
                if any(nombre == p or direccion == p or comuna == p for _, p in entries[:4]):
                    messagebox.showerror("Error", "Complete todos los campos obligatorios.")
                    return

                self.data.append({
                    "rut": rut if rut != entries[1][1] else "",
                    "nombre_completo": nombre,
                    "direccion": direccion,
                    "comuna": comuna,
                    "cajas_de_huevos_total": cajas,
                    "cajas_de_huevos": cajas
                })
                guardar_datos(self.data)
                self.ver_clientes()
                win.destroy()
                messagebox.showinfo("Éxito", "Cliente agregado con éxito.")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido para cajas.")

        ttk.Button(win, text="Guardar", command=agregar).pack(pady=15)

    def ventana_nuevo_pedido(self):
        win = tk.Toplevel(self.root)
        win.title("Nuevo Pedido")
        win.geometry("380x360")
        win.resizable(False, False)
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text="Buscar cliente (nombre o RUT):", bg="#f7f9fb").pack(pady=(10, 0))
        entry_buscar = tk.Entry(win, width=40, fg="#777")
        entry_buscar.insert(0, "Ej: María González o 12.345.678-9")

        def on_focus_in(e):
            if entry_buscar.get() == "Ej: María González o 12.345.678-9":
                entry_buscar.delete(0, "end")
                entry_buscar.config(fg="#000")

        def on_focus_out(e):
            if not entry_buscar.get():
                entry_buscar.insert(0, "Ej: María González o 12.345.678-9")
                entry_buscar.config(fg="#777")

        entry_buscar.bind("<FocusIn>", on_focus_in)
        entry_buscar.bind("<FocusOut>", on_focus_out)
        entry_buscar.pack(pady=5)

        listbox = tk.Listbox(win, height=6, width=50)
        listbox.pack(pady=5)
        resultados = []

        def buscar(event=None):
            listbox.delete(0, tk.END)
            texto = normalizar(entry_buscar.get().strip())
            if not texto or texto.startswith("ej:"):
                return
            resultados.clear()
            for c in self.data:
                if texto in normalizar(c["nombre_completo"]) or texto in normalizar(c.get("rut", "")):
                    resultados.append(c)
                    listbox.insert(tk.END, f"{c['nombre_completo']} ({c.get('rut', '')}) - {c['comuna']}")

        entry_buscar.bind("<KeyRelease>", buscar)

        tk.Label(win, text="Cantidad de cajas a agregar:", bg="#f7f9fb").pack(pady=(10, 0))
        entry_cantidad = tk.Entry(win, width=15, fg="#777")
        entry_cantidad.insert(0, "Ej: 10")
        entry_cantidad.bind("<FocusIn>", lambda e: entry_cantidad.delete(0, "end") if entry_cantidad.get() == "Ej: 10" else None)
        entry_cantidad.bind("<FocusOut>", lambda e: entry_cantidad.insert(0, "Ej: 10") if not entry_cantidad.get() else None)
        entry_cantidad.pack()

        def agregar():
            try:
                sel = listbox.curselection()
                if not sel:
                    messagebox.showerror("Error", "Seleccione un cliente.")
                    return
                cliente = resultados[sel[0]]
                cantidad = int(entry_cantidad.get().strip())
                cliente["cajas_de_huevos"] += cantidad
                cliente["cajas_de_huevos_total"] += cantidad
                guardar_datos(self.data)
                self.ver_clientes()
                messagebox.showinfo("Éxito", f"Se agregaron {cantidad} cajas a {cliente['nombre_completo']}.")
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese una cantidad válida.")

        ttk.Button(win, text="Agregar pedido", command=agregar).pack(pady=10)

    def generar_reparto(self):
        if not self.data:
            messagebox.showwarning("Sin clientes", "No hay clientes registrados.")
            return

        filtrar = messagebox.askyesno("Filtro", "¿Desea filtrar el reparto por comuna?")
        clientes_filtrados = self.data
        comuna = None

        if filtrar:
            comuna = simpledialog.askstring("Filtrar por comuna", "Ingrese el nombre de la comuna:")
            if not comuna:
                messagebox.showwarning("Advertencia", "Debe ingresar una comuna válida.")
                return
            clientes_filtrados = [c for c in self.data if normalizar(c["comuna"]) == normalizar(comuna)]
            if not clientes_filtrados:
                messagebox.showinfo("Sin resultados", f"No hay clientes en la comuna '{comuna}'.")
                return

        clientes_con_pedidos = [c for c in clientes_filtrados if c["cajas_de_huevos"] > 0]
        if not clientes_con_pedidos:
            messagebox.showinfo("Sin pedidos", "No hay pedidos pendientes para generar reparto.")
            return

        fecha_actual = datetime.now().strftime("%d-%m-%Y")
        nombre_archivo = f"reparto_huevos_{comuna or 'general'}_{fecha_actual}.xlsx".replace(" ", "_")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reparto Huevos"

        encabezados = ["Nombre completo", "RUT", "Dirección", "Comuna", "Cajas de huevos", "Método de pago", "Pagado (Sí/No)"]
        ws.append(encabezados)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        for cliente in clientes_con_pedidos:
            ws.append([
                cliente["nombre_completo"],
                cliente.get("rut", ""),
                cliente["direccion"],
                cliente["comuna"],
                cliente["cajas_de_huevos"]
            ])

        for column in ws.columns:
            max_length = max(len(str(cell.value)) if cell.value else 0 for cell in column)
            ws.column_dimensions[column[0].column_letter].width = max_length + 2

        wb.save(nombre_archivo)

        # Resetear pedidos
        for cliente in clientes_con_pedidos:
            cliente["cajas_de_huevos"] = 0

        guardar_datos(self.data)
        self.ver_clientes()

        messagebox.showinfo("Éxito", f"Archivo '{nombre_archivo}' generado correctamente.\nPedidos actualizados.")

    def centrar_ventana(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"+{x}+{y}")

# ------------------ Ejecución ------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
