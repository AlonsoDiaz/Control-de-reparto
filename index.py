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
        c for c in unicodedata.normalize('NFD', (texto or "").lower())
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
        self.root.geometry("980x620")
        self.root.configure(bg="#f9fafb")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e8ecf0")
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)

        self.data = cargar_datos()

        frame = tk.Frame(root, padx=12, pady=12, bg="#f9fafb")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="📋 Control de Reparto", font=("Segoe UI", 16, "bold"), bg="#f9fafb", fg="#333").grid(row=0, column=0, columnspan=6, pady=(0, 8))

        botones = [
            ("➕ Agregar cliente", self.ventana_agregar_cliente),
            ("✏️ Editar", self.ventana_editar),
            ("🥚 Nuevo pedido", self.ventana_nuevo_pedido),
            ("📊 Ver resumen", self.ventana_resumen),
            ("📦 Generar reparto", self.generar_reparto),
            ("🚪 Salir", root.quit)
        ]
        for i, (text, cmd) in enumerate(botones):
            ttk.Button(frame, text=text, width=18, command=cmd).grid(row=1, column=i, padx=4, pady=6)

        self.tree = ttk.Treeview(
            frame,
            columns=("Nombre", "RUT", "Dirección", "Comuna", "Pendiente a entrega", "Total histórico"),
            show="headings",
            height=16
        )

        for col in ("Nombre", "RUT", "Dirección", "Comuna", "Pendiente a entrega", "Total histórico"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.grid(row=2, column=0, columnspan=6, pady=12)

        self.label_total = tk.Label(frame, text="", bg="#f9fafb", fg="#444", font=("Segoe UI", 11, "bold"))
        self.label_total.grid(row=3, column=0, columnspan=6, pady=(4, 0))

        tk.Label(frame, text="Versión 1.2.0", fg="#888", font=("Segoe UI", 9, "italic"), bg="#f9fafb").grid(row=4, column=0, columnspan=6, pady=(6, 0))

        self.ver_clientes()

    # ------------------ Mostrar clientes ------------------

    def ver_clientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        clientes_ordenados = sorted(self.data, key=lambda c: c.get("cajas_de_huevos", 0), reverse=True)
        total_pendiente = 0

        for c in clientes_ordenados:
            total_pendiente += c.get("cajas_de_huevos", 0)
            self.tree.insert("", "end", values=(
                c.get("nombre_completo", ""),
                c.get("rut", ""),
                c.get("direccion", ""),
                c.get("comuna", ""),
                c.get("cajas_de_huevos", 0),
                c.get("cajas_de_huevos_total", 0)
            ))

        self.label_total.config(text=f"🥚 Total de cajas pendientes a entrega: {total_pendiente}")

    # ------------------ Agregar cliente (placeholders) ------------------

    def ventana_agregar_cliente(self):
        win = tk.Toplevel(self.root)
        win.title("Agregar Cliente")
        win.geometry("340x360")
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
            tk.Label(win, text=label_text, bg="#f7f9fb").pack(pady=(8, 0))
            entry = tk.Entry(win, width=36, fg="#777")
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

                # Validación: comprobar que no queden placeholders
                if any(nombre == p or direccion == p or comuna == p for _, p in entries[:4]):
                    messagebox.showerror("Error", "Complete todos los campos obligatorios.")
                    return

                self.data.append({
                    "rut": "" if rut == entries[1][1] else rut,
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

        ttk.Button(win, text="Guardar", command=agregar).pack(pady=14)

    # ------------------ Nuevo pedido (placeholders + coincidencias) ------------------

    def ventana_nuevo_pedido(self):
        win = tk.Toplevel(self.root)
        win.title("Nuevo Pedido")
        win.geometry("420x380")
        win.resizable(False, False)
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text="Buscar cliente (nombre o RUT):", bg="#f7f9fb").pack(pady=(10, 0))
        entry_buscar = tk.Entry(win, width=44, fg="#777")
        entry_buscar.insert(0, "Ej: María González o 12.345.678-9")

        def on_focus_in(e):
            if entry_buscar.get().startswith("Ej"):
                entry_buscar.delete(0, "end")
                entry_buscar.config(fg="#000")

        def on_focus_out(e):
            if not entry_buscar.get():
                entry_buscar.insert(0, "Ej: María González o 12.345.678-9")
                entry_buscar.config(fg="#777")

        entry_buscar.bind("<FocusIn>", on_focus_in)
        entry_buscar.bind("<FocusOut>", on_focus_out)
        entry_buscar.pack(pady=6)

        listbox = tk.Listbox(win, height=8, width=60)
        listbox.pack(pady=6)
        resultados = []

        def buscar(event=None):
            listbox.delete(0, tk.END)
            texto = normalizar(entry_buscar.get().strip())
            resultados.clear()
            if not texto or texto.startswith("ej:"):
                return
            for c in self.data:
                if texto in normalizar(c.get("nombre_completo", "")) or texto in normalizar(c.get("rut", "")):
                    resultados.append(c)
                    listbox.insert(tk.END, f"{c.get('nombre_completo','')} ({c.get('rut','')}) - {c.get('comuna','')}")

        entry_buscar.bind("<KeyRelease>", buscar)

        tk.Label(win, text="Cantidad de cajas a agregar:", bg="#f7f9fb").pack(pady=(10, 0))
        entry_cantidad = tk.Entry(win, width=18, fg="#777")
        entry_cantidad.insert(0, "Ej: 10")
        entry_cantidad.bind("<FocusIn>", lambda e: entry_cantidad.delete(0, "end") if entry_cantidad.get().startswith("Ej") else None)
        entry_cantidad.bind("<FocusOut>", lambda e: entry_cantidad.insert(0, "Ej: 10") if not entry_cantidad.get() else None)
        entry_cantidad.pack(pady=6)

        def agregar_pedido():
            try:
                sel = listbox.curselection()
                if not sel:
                    messagebox.showerror("Error", "Seleccione un cliente.")
                    return
                cliente = resultados[sel[0]]
                cantidad = int(entry_cantidad.get().strip())
                if cantidad <= 0:
                    messagebox.showerror("Error", "Ingrese una cantidad mayor que 0.")
                    return
                cliente["cajas_de_huevos"] = cliente.get("cajas_de_huevos", 0) + cantidad
                cliente["cajas_de_huevos_total"] = cliente.get("cajas_de_huevos_total", 0) + cantidad
                guardar_datos(self.data)
                self.ver_clientes()
                messagebox.showinfo("Éxito", f"Se agregaron {cantidad} cajas a {cliente.get('nombre_completo','')}.")
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese una cantidad válida.")

        ttk.Button(win, text="Agregar pedido", command=agregar_pedido).pack(pady=10)

    # ------------------ Editar (búsqueda + opciones claras) ------------------

    def ventana_editar(self):
        win = tk.Toplevel(self.root)
        win.title("Editar Cliente o Pedido")
        win.geometry("460x420")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text="Buscar cliente (nombre o RUT):", bg="#f7f9fb").pack(pady=(10, 0))
        entry_buscar = tk.Entry(win, width=46, fg="#777")
        entry_buscar.insert(0, "Ej: Juan Pérez o 12.345.678-9")

        def on_focus_in(e):
            if entry_buscar.get().startswith("Ej"):
                entry_buscar.delete(0, "end")
                entry_buscar.config(fg="#000")

        def on_focus_out(e):
            if not entry_buscar.get():
                entry_buscar.insert(0, "Ej: Juan Pérez o 12.345.678-9")
                entry_buscar.config(fg="#777")

        entry_buscar.bind("<FocusIn>", on_focus_in)
        entry_buscar.bind("<FocusOut>", on_focus_out)
        entry_buscar.pack(pady=6)

        listbox = tk.Listbox(win, height=10, width=70)
        listbox.pack(pady=6)
        resultados = []

        def buscar(event=None):
            listbox.delete(0, tk.END)
            texto = normalizar(entry_buscar.get().strip())
            resultados.clear()
            if not texto or texto.startswith("ej:"):
                return
            for c in self.data:
                if texto in normalizar(c.get("nombre_completo", "")) or texto in normalizar(c.get("rut", "")):
                    resultados.append(c)
                    listbox.insert(tk.END, f"{c.get('nombre_completo','')} ({c.get('rut','')}) - {c.get('comuna','')} — Pendiente: {c.get('cajas_de_huevos',0)}")

        entry_buscar.bind("<KeyRelease>", buscar)

        def seleccionar():
            sel = listbox.curselection()
            if not sel:
                messagebox.showerror("Error", "Seleccione un cliente.")
                return
            cliente = resultados[sel[0]]

            # Ventana de opciones clara (Editar datos, Editar pedido, Eliminar)
            win_op = tk.Toplevel(self.root)
            win_op.title("¿Qué deseas hacer?")
            win_op.geometry("360x160")
            win_op.configure(bg="#f7f9fb")
            self.centrar_ventana(win_op)

            tk.Label(win_op, text=f"{cliente.get('nombre_completo','')}", bg="#f7f9fb", font=("Segoe UI", 11, "bold")).pack(pady=(10, 6))
            tk.Label(win_op, text=f"Pendiente: {cliente.get('cajas_de_huevos',0)} cajas — Comuna: {cliente.get('comuna','')}", bg="#f7f9fb").pack(pady=(0,8))

            def editar_datos():
                win_op.destroy()
                win.destroy()
                self.editar_datos_cliente(cliente)

            def editar_pedido():
                win_op.destroy()
                win.destroy()
                self.editar_pedido_cliente(cliente)

            def eliminar_cliente():
                if messagebox.askyesno("Confirmar eliminación", f"¿Eliminar a {cliente.get('nombre_completo','')}? Esta acción no se puede deshacer."):
                    try:
                        self.data.remove(cliente)
                        guardar_datos(self.data)
                        self.ver_clientes()
                        win_op.destroy()
                        win.destroy()
                        messagebox.showinfo("Eliminado", "Cliente eliminado correctamente.")
                    except Exception as e:
                        messagebox.showerror("Error", str(e))

            btn_frame = tk.Frame(win_op, bg="#f7f9fb")
            btn_frame.pack(pady=6)
            ttk.Button(btn_frame, text="Editar datos", width=12, command=editar_datos).grid(row=0, column=0, padx=6, pady=6)
            ttk.Button(btn_frame, text="Editar pedido", width=12, command=editar_pedido).grid(row=0, column=1, padx=6, pady=6)
            ttk.Button(btn_frame, text="Eliminar", width=12, command=eliminar_cliente).grid(row=1, column=0, columnspan=2, pady=6)
            ttk.Button(win_op, text="Cancelar", command=win_op.destroy).pack(pady=(4,6))

        ttk.Button(win, text="Seleccionar", command=seleccionar).pack(pady=8)

    # ------------------ Subventanas de edición ------------------

    def editar_datos_cliente(self, cliente):
        win = tk.Toplevel(self.root)
        win.title(f"Editar datos: {cliente.get('nombre_completo','')}")
        win.geometry("360x340")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        campos = [
            ("Nombre completo", "nombre_completo", cliente.get("nombre_completo", "")),
            ("RUT (opcional)", "rut", cliente.get("rut", "")),
            ("Dirección", "direccion", cliente.get("direccion", "")),
            ("Comuna", "comuna", cliente.get("comuna", "")),
        ]

        entries = {}
        for label_text, key, valor in campos:
            tk.Label(win, text=label_text, bg="#f7f9fb").pack(pady=(8, 0))
            e = tk.Entry(win, width=42)
            e.insert(0, valor)
            e.pack()
            entries[key] = e

        def guardar():
            nombre = entries["nombre_completo"].get().strip()
            direccion = entries["direccion"].get().strip()
            comuna = entries["comuna"].get().strip()
            if not nombre or not direccion or not comuna:
                messagebox.showerror("Error", "Complete los campos obligatorios.")
                return
            cliente["nombre_completo"] = nombre
            cliente["rut"] = entries["rut"].get().strip()
            cliente["direccion"] = direccion
            cliente["comuna"] = comuna
            guardar_datos(self.data)
            self.ver_clientes()
            win.destroy()
            messagebox.showinfo("Éxito", "Datos del cliente actualizados.")

        ttk.Button(win, text="Guardar cambios", command=guardar).pack(pady=12)

    def editar_pedido_cliente(self, cliente):
        win = tk.Toplevel(self.root)
        win.title(f"Editar pedido: {cliente.get('nombre_completo','')}")
        win.geometry("340x240")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text=f"Pendiente actual: {cliente.get('cajas_de_huevos',0)} cajas", bg="#f7f9fb").pack(pady=(10, 6))
        

        def reemplazar():
            def guardar_reemplazo():
                try:
                    nuevo = int(entry_reemplazar.get().strip())
                    if nuevo < 0:
                        messagebox.showerror("Error", "La cantidad no puede ser negativa.")
                        return
                    cliente["cajas_de_huevos"] = nuevo
                    # Ajustar histórico si es menor que total actual
                    cliente["cajas_de_huevos_total"] = max(cliente.get("cajas_de_huevos_total", 0), nuevo)
                    guardar_datos(self.data)
                    self.ver_clientes()
                    win_replace.destroy()
                    win.destroy()
                    messagebox.showinfo("Éxito", "Pedido reemplazado correctamente.")
                except ValueError:
                    messagebox.showerror("Error", "Ingrese un número válido.")
            win_replace = tk.Toplevel(self.root)
            win_replace.title("Reemplazar cantidad pendiente")
            win_replace.geometry("300x140")
            win_replace.configure(bg="#f7f9fb")
            self.centrar_ventana(win_replace)
            tk.Label(win_replace, text="Nueva cantidad pendiente:", bg="#f7f9fb").pack(pady=(10,4))
            entry_reemplazar = tk.Entry(win_replace, width=12)
            entry_reemplazar.insert(0, str(cliente.get("cajas_de_huevos",0)))
            entry_reemplazar.pack(pady=6)
            ttk.Button(win_replace, text="Guardar", command=guardar_reemplazo).pack(pady=6)

        

        btn_frame = tk.Frame(win, bg="#f7f9fb")
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Editar cantidad", width=18, command=reemplazar).grid(row=0, column=0, padx=6, pady=6)
        ttk.Button(win, text="Cancelar", command=win.destroy).pack(pady=(6,8))

    # ------------------ Resumen / Estadísticas ------------------

    def ventana_resumen(self):
        if not self.data:
            messagebox.showinfo("Sin datos", "No hay clientes registrados.")
            return

        win = tk.Toplevel(self.root)
        win.title("📊 Resumen de Pedidos")
        win.geometry("540x540")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        total_pendiente = sum(c.get("cajas_de_huevos", 0) for c in self.data)
        clientes_con_pedido = [c for c in self.data if c.get("cajas_de_huevos", 0) > 0]
        total_clientes_pendientes = len(clientes_con_pedido)

        # Agrupar por comuna
        resumen_comunas = {}
        for c in clientes_con_pedido:
            comuna = c.get("comuna", "Sin comuna")
            resumen_comunas[comuna] = resumen_comunas.get(comuna, 0) + c.get("cajas_de_huevos", 0)

        resumen_ordenado = sorted(resumen_comunas.items(), key=lambda x: x[1], reverse=True)

        tk.Label(win, text=f"🥚 Total de cajas pendientes: {total_pendiente}", bg="#f7f9fb", font=("Segoe UI", 12, "bold")).pack(pady=(12, 6))
        tk.Label(win, text=f"👥 Clientes con pedidos activos: {total_clientes_pendientes}", bg="#f7f9fb", font=("Segoe UI", 10)).pack(pady=(0, 8))

        # Mostrar porcentaje por comuna
        if total_pendiente > 0:
            tk.Label(win, text="Porcentaje por comuna:", bg="#f7f9fb", font=("Segoe UI", 10, "underline")).pack(pady=(6,4))
            for comuna, total in resumen_ordenado:
                pct = (total / total_pendiente) * 100
                tk.Label(win, text=f"{comuna}: {total} cajas — {pct:.1f}%", bg="#f7f9fb").pack(anchor="w", padx=20)

        # Tabla con detalle por comuna
        tk.Label(win, text="Detalle por comuna:", bg="#f7f9fb", font=("Segoe UI", 10, "underline")).pack(pady=(10,4))
        tree = ttk.Treeview(win, columns=("Comuna", "Cajas pendientes", "Clientes con pedido"), show="headings", height=10)
        tree.heading("Comuna", text="Comuna")
        tree.heading("Cajas pendientes", text="Cajas pendientes")
        tree.heading("Clientes con pedido", text="Clientes con pedido")
        tree.column("Comuna", anchor="center", width=200)
        tree.column("Cajas pendientes", anchor="center", width=120)
        tree.column("Clientes con pedido", anchor="center", width=140)

        # calcular clientes por comuna
        clientes_por_comuna = {}
        for c in clientes_con_pedido:
            clientes_por_comuna[c.get("comuna", "Sin comuna")] = clientes_por_comuna.get(c.get("comuna","Sin comuna"), 0) + 1

        for comuna, total in resumen_ordenado:
            tree.insert("", "end", values=(comuna, total, clientes_por_comuna.get(comuna, 0)))

        tree.pack(pady=8)

        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=10)

    # ------------------ Generar reparto ------------------

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
            clientes_filtrados = [c for c in self.data if normalizar(c.get("comuna", "")) == normalizar(comuna)]
            if not clientes_filtrados:
                messagebox.showinfo("Sin resultados", f"No hay clientes en la comuna '{comuna}'.")
                return

        clientes_con_pedidos = [c for c in clientes_filtrados if c.get("cajas_de_huevos", 0) > 0]
        if not clientes_con_pedidos:
            messagebox.showinfo("Sin pedidos", "No hay pedidos pendientes para generar reparto.")
            return

        fecha_actual = datetime.now().strftime("%d-%m-%Y")
        nombre_archivo = f"reparto_huevos_{comuna or 'general'}_{fecha_actual}.xlsx".replace(" ", "_")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reparto Huevos"

        encabezados = ["Nombre completo", "RUT", "Dirección", "Comuna", "Cajas de huevos", "Metodo de pago", "Pagado SI/NO"]
        ws.append(encabezados)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        total_cajas = 0  # 🔹 Nuevo: contador de total de cajas

        for cliente in clientes_con_pedidos:
            cajas = cliente.get("cajas_de_huevos", 0)
            ws.append([
                cliente.get("nombre_completo", ""),
                cliente.get("rut", ""),
                cliente.get("direccion", ""),
                cliente.get("comuna", ""),
                cajas
            ])
            total_cajas += cajas  # 🔹 Sumar al total

        # 🔹 Nueva fila al final con el total
        ws.append([])
        ws.append(["", "", "", "TOTAL CAJAS", total_cajas])
        total_row = ws.max_row
        ws[f"D{total_row}"].font = Font(bold=True, color="FF0000")
        ws[f"E{total_row}"].font = Font(bold=True, color="FF0000")
        ws[f"D{total_row}"].alignment = Alignment(horizontal="right")
        ws[f"E{total_row}"].alignment = Alignment(horizontal="center")

        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = max(len(str(cell.value)) if cell.value else 0 for cell in column)
            ws.column_dimensions[column[0].column_letter].width = max_length + 2

        wb.save(nombre_archivo)

        # Confirmar si marcar como entregados
        if messagebox.askyesno("Marcar entregados", "¿Deseas marcar los pedidos generados como entregados (poner 0)?"):
            for cliente in clientes_con_pedidos:
                cliente["cajas_de_huevos"] = 0
            guardar_datos(self.data)
            self.ver_clientes()

        messagebox.showinfo("Éxito", f"Archivo '{nombre_archivo}' generado correctamente con total de {total_cajas} cajas.")

    # ------------------ Centrar ventana ------------------

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
