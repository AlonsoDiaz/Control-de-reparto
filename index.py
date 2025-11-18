import json
import os
import unicodedata
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

ARCHIVO = "db.json"

PRECIO_CAJA = 1000  # 🔹 Precio inicial de la bandeja de huevos

# ------------------ Funciones base ------------------

def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', (texto or "").lower())
        if unicodedata.category(c) != 'Mn'
    )

def cargar_datos():
    if not os.path.exists(ARCHIVO):
        return {"clientes": [], "precio_caja": PRECIO_CAJA, "precios_por_comuna": {}}
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("El archivo JSON no tiene la estructura esperada.")
            # Asegurarse de que las claves necesarias estén presentes
            data.setdefault("clientes", [])
            data.setdefault("precio_caja", PRECIO_CAJA)
            data.setdefault("precios_por_comuna", {})
            return data
    except (json.JSONDecodeError, ValueError, IOError):
        messagebox.showerror("Error", "El archivo de datos está corrupto o tiene un formato incorrecto. Se restablecerán los valores predeterminados.")
        return {"clientes": [], "precio_caja": PRECIO_CAJA, "precios_por_comuna": {}}

def guardar_datos(data):
    # Cargar los datos existentes para preservar las claves
    datos_existentes = cargar_datos()
    datos_existentes.update(data)  # Actualizar solo las claves proporcionadas
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos_existentes, f, indent=4, ensure_ascii=False)

# ------------------ Interfaz gráfica ------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Control de Reparto de Huevos")
        self.root.geometry("1024x720")
        self.root.configure(bg="#f0f4f8")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#d1e7ff", foreground="#003366")
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28, background="#ffffff", fieldbackground="#ffffff")
        style.map("Treeview", background=[("selected", "#cce5ff")])

        datos_cargados = cargar_datos()
        self.data = datos_cargados.get("clientes", [])
        self.precios_por_comuna = datos_cargados.get("precios_por_comuna", {})
        global PRECIO_CAJA
        PRECIO_CAJA = datos_cargados.get("precio_caja", PRECIO_CAJA)

        frame = tk.Frame(root, padx=16, pady=16, bg="#f0f4f8")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="📋 Control de Reparto", font=("Segoe UI", 18, "bold"), bg="#f0f4f8", fg="#003366").pack(pady=(0, 12))

        botones_frame = tk.Frame(frame, bg="#f0f4f8")  # 🔹 Contenedor para los botones
        botones_frame.pack(fill="x", pady=8)

        botones = [
            ("➕ Agregar cliente", self.ventana_agregar_cliente),
            ("✏️ Editar", self.ventana_editar),
            ("🥚 Nuevo pedido", self.ventana_nuevo_pedido),
            ("📊 Ver resumen", self.ventana_resumen),
            ("💲 Cambiar precio", self.cambiar_precio_caja),  # 🔹 Nuevo botón para cambiar el precio
            ("📦 Generar reparto", self.generar_reparto),
            ("🚪 Salir", root.quit),
            ("🏘️ Gestionar Precios", self.gestionar_precios_por_comuna)  # 🔹 Botón para gestionar precios por comuna
        ]
        for text, cmd in botones:
            ttk.Button(botones_frame, text=text, command=cmd).pack(side="left", padx=6, pady=6, expand=True)  # 🔹 Botones distribuidos horizontalmente

        self.tree = ttk.Treeview(
            frame,
            columns=("Nombre", "Teléfono", "Dirección", "Comuna", "Día de Reparto", "Pendiente a entrega", "Total histórico", "Total adeudado"),
            show="headings",
            height=16
        )

        for col in ("Nombre", "Teléfono", "Dirección", "Comuna", "Día de Reparto", "Pendiente a entrega", "Total histórico", "Total adeudado"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")

        self.tree.pack(fill="both", expand=True, pady=16)

        self.label_total = tk.Label(frame, text="", bg="#f0f4f8", fg="#003366", font=("Segoe UI", 12, "bold"))
        self.label_total.pack(pady=(8, 0))

        tk.Label(frame, text="Versión 1.2.0", fg="#888", font=("Segoe UI", 10, "italic"), bg="#f0f4f8").pack(pady=(8, 0))

        self.ver_clientes()

    # ------------------ Mostrar clientes ------------------

    def ver_clientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        clientes_ordenados = sorted(self.data, key=lambda c: c.get("cajas_de_huevos", 0), reverse=True)
        total_pendiente = 0

        for c in clientes_ordenados:
            pendiente = c.get("cajas_de_huevos", 0)
            total_pendiente += pendiente

            comuna_valor = (c.get("comuna", "") or "").strip()
            comuna_mostrar = comuna_valor.capitalize() if comuna_valor else ""

            dia_valor = (c.get("dia_reparto", "") or "").strip()
            dia_mostrar = dia_valor.capitalize() if dia_valor else "-"

            precio = PRECIO_CAJA
            for comuna_guardada, valor in self.precios_por_comuna.items():
                if normalizar(comuna_guardada) == normalizar(comuna_valor):
                    precio = valor
                    break

            total_adeudado = pendiente * precio

            self.tree.insert("", "end", values=(
                c.get("nombre_completo", ""),
                c.get("telefono", ""),
                c.get("direccion", ""),
                comuna_mostrar,
                dia_mostrar,
                pendiente,
                c.get("cajas_de_huevos_total", 0),
                f"${total_adeudado:,.0f}".replace(",", ".")
            ))

        # Actualizar la etiqueta con el total de cajas pendientes
        self.label_total.config(text=f"🥚 Total de cajas pendientes a entrega: {total_pendiente}")
        self.label_total.pack(pady=(8, 0))

    # ------------------ Cambiar precio de la caja ------------------

    def cambiar_precio_caja(self):
        def guardar_precio():
            try:
                nuevo_precio = int(entry_precio.get().strip())
                if nuevo_precio <= 0:
                    messagebox.showerror("Error", "El precio debe ser mayor a 0.")
                    return
                global PRECIO_CAJA
                PRECIO_CAJA = nuevo_precio
                # Guardar el nuevo precio en los datos
                guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA})
                self.ver_clientes()  # 🔹 Actualizar la tabla con el nuevo precio
                win.destroy()
                messagebox.showinfo("Éxito", f"El precio de la bandeja se actualizó a ${PRECIO_CAJA}.")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido.")

        win = tk.Toplevel(self.root)
        win.title("Cambiar Precio de la Bandeja")
        win.geometry("300x150")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text="Precio actual: $" + str(PRECIO_CAJA), bg="#f7f9fb", font=("Segoe UI", 11)).pack(pady=(10, 4))
        tk.Label(win, text="Nuevo precio:", bg="#f7f9fb", font=("Segoe UI", 10)).pack(pady=(4, 0))

        entry_precio = tk.Entry(win, width=20, font=("Segoe UI", 10))
        entry_precio.pack(pady=6)

        ttk.Button(win, text="Guardar", command=guardar_precio).pack(pady=10)

    # ------------------ Agregar cliente (placeholders) ------------------

    def ventana_agregar_cliente(self):
        def guardar_cliente():
            nombre = entry_nombre.get().strip()
            telefono = entry_telefono.get().strip()
            direccion = entry_direccion.get().strip()
            comuna = entry_comuna.get().strip()
            dia_reparto = entry_dia_reparto.get().strip()  # Nuevo campo para día de reparto

            if not nombre or not telefono or not direccion or not comuna:
                messagebox.showerror("Error", "Todos los campos excepto el día de reparto son obligatorios.")
                return

            nuevo_cliente = {
                "nombre_completo": nombre,
                "telefono": telefono,
                "direccion": direccion,
                "comuna": comuna,
                "cajas_de_huevos_total": 0,
                "cajas_de_huevos": 0,
                "dia_reparto": dia_reparto or None  # Guardar como None si está vacío
            }

            self.data.append(nuevo_cliente)
            # Cargar los datos existentes para preservar las claves
            datos_existentes = cargar_datos()
            datos_existentes["clientes"] = self.data  # Actualizar solo la lista de clientes
            guardar_datos(datos_existentes)
            self.ver_clientes()
            win.destroy()
            messagebox.showinfo("Éxito", "Cliente agregado correctamente.")

        win = tk.Toplevel(self.root)
        win.title("Agregar Cliente")
        win.geometry("400x400")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text="Agregar Cliente", bg="#f7f9fb", font=("Segoe UI", 14, "bold")).pack(pady=(10, 10))

        tk.Label(win, text="Nombre Completo:", bg="#f7f9fb", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        entry_nombre = tk.Entry(win, width=30, font=("Segoe UI", 10))
        entry_nombre.pack(pady=5)

        tk.Label(win, text="Teléfono:", bg="#f7f9fb", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        entry_telefono = tk.Entry(win, width=30, font=("Segoe UI", 10))
        entry_telefono.pack(pady=5)

        tk.Label(win, text="Dirección:", bg="#f7f9fb", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        entry_direccion = tk.Entry(win, width=30, font=("Segoe UI", 10))
        entry_direccion.pack(pady=5)

        tk.Label(win, text="Comuna:", bg="#f7f9fb", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        entry_comuna = tk.Entry(win, width=30, font=("Segoe UI", 10))
        entry_comuna.pack(pady=5)

        tk.Label(win, text="Día de Reparto (opcional):", bg="#f7f9fb", font=("Segoe UI", 10)).pack(anchor="w", padx=20)  # Etiqueta para el nuevo campo
        entry_dia_reparto = tk.Entry(win, width=30, font=("Segoe UI", 10))
        entry_dia_reparto.pack(pady=5)  # Campo de entrada para el día de reparto

        ttk.Button(win, text="Guardar", command=guardar_cliente).pack(pady=20)

    # ------------------ Nuevo pedido (placeholders + coincidencias) ------------------

    def ventana_nuevo_pedido(self):
        win = tk.Toplevel(self.root)
        win.title("Nuevo Pedido")
        win.geometry("500x450")
        win.resizable(False, False)
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text="Buscar cliente (nombre o telefono):", bg="#f7f9fb").pack(pady=(10, 0))
        # Corregir y asegurar que el campo de búsqueda sea visible y funcional
        entry_buscar = tk.Entry(win, width=44, fg="#000")
        entry_buscar.insert(0, "Ej: María González o 912345678")
        entry_buscar.bind("<FocusIn>", lambda e: entry_buscar.delete(0, "end") if entry_buscar.get().startswith("Ej") else None)
        entry_buscar.bind("<FocusOut>", lambda e: entry_buscar.insert(0, "Ej: María González o 912345678") if not entry_buscar.get() else None)
        entry_buscar.pack(pady=(10, 5))  # Ajustar margen superior e inferior

        tk.Label(win, text="Cantidad de cajas a agregar:", bg="#f7f9fb").pack(pady=(10, 0))
        entry_cantidad = tk.Entry(win, width=18, fg="#000")
        entry_cantidad.pack(pady=6)

        # Crear listbox para mostrar resultados de búsqueda
        listbox = tk.Listbox(win, height=10, width=50)
        listbox.pack(pady=(5, 10))  # Ajustar margen superior e inferior

        resultados = []  # Lista para almacenar los resultados de búsqueda

        # Actualizar resultados en tiempo real mientras se escribe
        def actualizar_resultados(event):
            valor_busqueda = entry_buscar.get().strip()
            if valor_busqueda.startswith("Ej:" ):
                query = ""
            else:
                query = valor_busqueda.lower()
            listbox.delete(0, tk.END)
            resultados.clear()
            for cliente in self.data:
                nombre = cliente.get("nombre_completo", "")
                comuna = (cliente.get("comuna", "") or "").strip()
                if query in nombre.lower() or query in cliente.get("telefono", ""):
                    resultados.append(cliente)
                    listbox.insert(tk.END, f"{nombre} - {comuna.capitalize() if comuna else ''}")
            if not resultados:
                listbox.insert(tk.END, "No se encontraron resultados.")

        # Asociar la actualización de resultados al evento de escritura
        entry_buscar.bind("<KeyRelease>", actualizar_resultados)

        # Cargar lista inicial de clientes
        actualizar_resultados(None)

        def agregar_pedido():
            try:
                sel = listbox.curselection()
                if not sel:
                    messagebox.showerror("Error", "Seleccione un cliente.")
                    return
                if not resultados or sel[0] >= len(resultados):
                    messagebox.showerror("Error", "Seleccione un cliente válido de la lista.")
                    return

                cliente = resultados[sel[0]]

                cantidad_texto = entry_cantidad.get().strip()
                if not cantidad_texto:
                    messagebox.showerror("Error", "El campo de cantidad no puede estar vacío.")
                    return
                if not cantidad_texto.isdigit():
                    messagebox.showerror("Error", "Ingrese un número válido para la cantidad de cajas.")
                    return

                cantidad = int(cantidad_texto)
                if cantidad <= 0:
                    messagebox.showerror("Error", "Ingrese una cantidad mayor que 0.")
                    return
                cliente["cajas_de_huevos"] = cliente.get("cajas_de_huevos", 0) + cantidad
                cliente["cajas_de_huevos_total"] = cliente.get("cajas_de_huevos_total", 0) + cantidad
                datos_existentes = cargar_datos()
                datos_existentes["clientes"] = self.data
                guardar_datos(datos_existentes)
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

        tk.Label(win, text="Buscar cliente (nombre o telefono):", bg="#f7f9fb").pack(pady=(10, 0))
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

        # Ajustar la posición del campo de búsqueda
        entry_buscar.pack(pady=5)
        entry_buscar.bind("<FocusIn>", lambda e: entry_buscar.delete(0, "end") if entry_buscar.get().startswith("Ej") else None)
        entry_buscar.bind("<FocusOut>", lambda e: entry_buscar.insert(0, "Ej: María González o 12.345.678-9") if not entry_buscar.get() else None)
        entry_buscar.pack(pady=6)

        # Crear listbox para mostrar resultados de búsqueda
        listbox = tk.Listbox(win, height=10, width=70)  # 🔹 Definido correctamente
        listbox.pack(pady=6)
        resultados = []  # 🔹 Definido correctamente

        def buscar(event=None):
            listbox.delete(0, tk.END)
            texto = normalizar(entry_buscar.get().strip())
            resultados.clear()
            if not texto or texto.startswith("ej:"):
                return
            for c in self.data:
                if texto in normalizar(c.get("nombre_completo", "")) or texto in normalizar(c.get("telefono", "")):
                    resultados.append(c)
                    listbox.insert(tk.END, f"{c.get('nombre_completo','')} ({c.get('telefono','')}) - {c.get('comuna','')} — Pendiente: {c.get('cajas_de_huevos',0)}")

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
                        guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA, "precios_por_comuna": self.precios_por_comuna})
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
            ("telefono (opcional)", "telefono", cliente.get("telefono", "")),
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
            cliente["telefono"] = entries["telefono"].get().strip()
            cliente["direccion"] = direccion
            cliente["comuna"] = comuna
            guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA, "precios_por_comuna": self.precios_por_comuna})
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

        tk.Label

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
                    guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA, "precios_por_comuna": self.precios_por_comuna})
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
            clientes_por_comuna[c.get("comuna", "Sin comuna")] = clientes_por_comuna.get(c.get("comuna", "Sin comuna"), 0) + 1

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

        # Modificar la lógica de generación de reparto para incluir filtro por día
        filtrar_dia = messagebox.askyesno("Filtro", "¿Desea filtrar el reparto por día de reparto?")
        if filtrar_dia:
            dia_reparto = simpledialog.askstring("Filtrar por día", "Ingrese el día de reparto (por ejemplo, Lunes):")
            if not dia_reparto:
                messagebox.showwarning("Advertencia", "Debe ingresar un día válido.")
                return
            clientes_filtrados = [c for c in clientes_filtrados if normalizar(c.get("dia_reparto", "")) == normalizar(dia_reparto)]
            if not clientes_filtrados:
                messagebox.showinfo("Sin resultados", f"No hay clientes con día de reparto '{dia_reparto}'.")
                return

        clientes_con_pedidos = [c for c in clientes_filtrados if c.get("cajas_de_huevos", 0) > 0]
        if not clientes_con_pedidos:
            messagebox.showinfo("Sin pedidos", "No hay pedidos pendientes para generar reparto.")
            return

        fecha_actual = datetime.now().strftime("%d-%m-%Y")
        nombre_archivo = f"reparto_huevos_{comuna or 'general'}_{fecha_actual}.xlsx"

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reparto Huevos"

        # Definir encabezados y asegurarse de que `ws` esté correctamente utilizado
        encabezados = ["Nombre completo", "Teléfono", "Dirección", "Comuna", "Cajas de huevos", "Monto a pagar"]
        ws.append(encabezados)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        total_cajas = 0  # 🔹 Contador de total de cajas
        total_ganancias = 0  # 🔹 Contador de total a ganar

        for cliente in clientes_con_pedidos:
            cajas = cliente.get("cajas_de_huevos", 0)
            comuna = cliente.get("comuna", "")
            precio = self.precios_por_comuna.get(comuna, PRECIO_CAJA)  # Usar precio por comuna si existe
            monto_a_pagar = cajas * precio
            total_cajas += cajas
            total_ganancias += monto_a_pagar

            ws.append([
                cliente.get("nombre_completo", ""),
                cliente.get("telefono", ""),
                cliente.get("direccion", ""),
                comuna,
                cajas,
                f"${monto_a_pagar:,.0f}".replace(",", ".")  # Formato $000.000.000
            ])

        # 🔹 Nueva fila al final con el total
        ws.append([])
        ws.append(["", "", "", "Total", total_cajas, f"${total_ganancias:,.0f}".replace(",", ".")])

        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = max(len(str(cell.value)) if cell.value else 0 for cell in column)
            ws.column_dimensions[column[0].column_letter].width = max_length + 2

        # Guardar el archivo Excel
        wb.save(nombre_archivo)

        # Confirmar si marcar como entregados
        if messagebox.askyesno("Marcar entregidos", "¿Deseas marcar los pedidos generados como entregidos (poner 0)?"):
            for cliente in clientes_con_pedidos:
                cliente["cajas_de_huevos"] = 0
            # Preservar los precios por comuna al guardar los datos
            guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA, "precios_por_comuna": self.precios_por_comuna})
            self.ver_clientes()

        messagebox.showinfo("Éxito", f"Archivo '{nombre_archivo}' generado correctamente con total de {total_cajas} cajas y ganancias de ${total_ganancias:,.0f}".replace(",", "."))

    # ------------------ Centrar ventana ------------------

    def centrar_ventana(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"+{x}+{y}")

    # Crear una nueva ventana para gestionar precios por comuna
    def gestionar_precios_por_comuna(self):
        win = tk.Toplevel(self.root)
        win.title("Gestionar Precios por Comuna")
        win.geometry("400x400")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text="Precios por Comuna", bg="#f7f9fb", font=("Segoe UI", 12, "bold")).pack(pady=(10, 6))

        frame = tk.Frame(win, bg="#f7f9fb")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(frame, columns=("Comuna", "Precio"), show="headings", height=10)
        tree.heading("Comuna", text="Comuna")
        tree.heading("Precio", text="Precio")
        tree.column("Comuna", anchor="center", width=200)
        tree.column("Precio", anchor="center", width=100)
        tree.pack(fill="both", expand=True, pady=10)

        for comuna, precio in self.precios_por_comuna.items():
            tree.insert("", "end", values=(comuna, f"${precio}"))

        def agregar_precio():
            comuna = simpledialog.askstring("Agregar Comuna", "Ingrese el nombre de la comuna:")
            if not comuna:
                return
            try:
                precio = int(simpledialog.askstring("Agregar Precio", f"Ingrese el precio para {comuna}:").strip())
                if precio <= 0:
                    messagebox.showerror("Error", "El precio debe ser mayor a 0.")
                    return
                self.precios_por_comuna[comuna] = precio
                guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA, "precios_por_comuna": self.precios_por_comuna})
                tree.insert("", "end", values=(comuna, f"${precio}"))
                messagebox.showinfo("Éxito", f"Precio para {comuna} agregado correctamente.")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido.")

        def eliminar_precio():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Error", "Seleccione una comuna para eliminar.")
                return
            comuna = tree.item(sel[0], "values")[0]
            if messagebox.askyesno("Confirmar", f"¿Eliminar el precio para {comuna}?"):
                del self.precios_por_comuna[comuna]
                guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA, "precios_por_comuna": self.precios_por_comuna})
                tree.delete(sel[0])
                messagebox.showinfo("Éxito", f"Precio para {comuna} eliminado correctamente.")

        btn_frame = tk.Frame(win, bg="#f7f9fb")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Agregar", command=agregar_precio).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=eliminar_precio).grid(row=0, column=1, padx=5)
        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=10)

    # ------------------ Agregar día de reparto ------------------

    def agregar_dia_reparto(self):
        def guardar_dia():
            dia = entry_dia.get().strip()
            if dia:
                cliente["dia_reparto"] = dia
                guardar_datos({"clientes": self.data, "precio_caja": PRECIO_CAJA, "precios_por_comuna": self.precios_por_comuna})
                self.ver_clientes()
                win.destroy()
                messagebox.showinfo("Éxito", f"Día de reparto para {cliente['nombre_completo']} actualizado a '{dia}'.")
            else:
                messagebox.showwarning("Advertencia", "No se ingresó ningún día de reparto.")

        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Seleccione un cliente para agregar el día de reparto.")
            return

        cliente = self.data[self.tree.index(sel[0])]

        win = tk.Toplevel(self.root)
        win.title("Agregar Día de Reparto")
        win.geometry("300x150")
        win.configure(bg="#f7f9fb")
        self.centrar_ventana(win)

        tk.Label(win, text=f"Cliente: {cliente['nombre_completo']}", bg="#f7f9fb", font=("Segoe UI", 11)).pack(pady=(10, 4))
        tk.Label(win, text="Día de reparto:", bg="#f7f9fb", font=("Segoe UI", 10)).pack(pady=(4, 0))

        entry_dia = tk.Entry(win, width=20, font=("Segoe UI", 10))
        entry_dia.pack(pady=6)
        entry_dia.insert(0, cliente.get("dia_reparto", ""))

        ttk.Button(win, text="Guardar", command=guardar_dia).pack(pady=10)

# ------------------ Ejecución ------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()  # 🔹 Verificado: formato correcto
