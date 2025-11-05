import json
import os
import pandas as pd
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

ARCHIVO = "db.json"

# ------------------ Funciones base ------------------

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

# ------------------ Funciones de negocio ------------------

def agregar_cliente(data, nombre, direccion, comuna, rut="", cajas=0):
    nuevo_cliente = {
        "rut": rut,
        "nombre_completo": nombre,
        "direccion": direccion,
        "comuna": comuna,
        "cajas_de_huevos_total": cajas,
        "cajas_de_huevos": cajas
    }
    data.append(nuevo_cliente)
    guardar_datos(data)
    return True

def nuevo_pedido(data, nombre, cantidad):
    for c in data:
        if nombre.lower() == c["nombre_completo"].lower():
            c["cajas_de_huevos"] += cantidad
            c["cajas_de_huevos_total"] += cantidad
            guardar_datos(data)
            return True
    return False

def generar_reparto(data):
    if not data:
        messagebox.showwarning("Sin clientes", "No hay clientes registrados.")
        return

    # Preguntar si desea filtrar por comuna
    filtrar = messagebox.askyesno("Filtro", "¿Desea filtrar el reparto por comuna?")
    clientes_filtrados = data
    comuna = None

    if filtrar:
        comuna = simpledialog.askstring("Filtrar por comuna", "Ingrese el nombre de la comuna:")
        if not comuna:
            messagebox.showwarning("Advertencia", "Debe ingresar una comuna válida.")
            return
        clientes_filtrados = [c for c in data if c["comuna"].lower() == comuna.lower()]
        if not clientes_filtrados:
            messagebox.showinfo("Sin resultados", f"No hay clientes en la comuna '{comuna}'.")
            return

    clientes_con_pedidos = [c for c in clientes_filtrados if c["cajas_de_huevos"] > 0]

    if not clientes_con_pedidos:
        messagebox.showinfo("Sin pedidos", "No hay pedidos pendientes para generar reparto.")
        return

    # Crear nombre de archivo con fecha y comuna (si aplica)
    fecha_actual = datetime.now().strftime("%d-%m-%Y")
    if comuna:
        nombre_archivo = f"reparto_huevos_{comuna}_{fecha_actual}.xlsx"
    else:
        nombre_archivo = f"reparto_huevos_{fecha_actual}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reparto Huevos"

    encabezados = ["Nombre completo", "RUT", "Dirección", "Comuna", "Cajas de huevos", "Metodo de pago", "Pagado si/no"]
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

    # Ajustar ancho de columnas
    for column in ws.columns:
        max_length = 0
        column = list(column)
        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column[0].column_letter].width = adjusted_width

    try:
        wb.save(nombre_archivo)
    except PermissionError:
        messagebox.showerror("Error", f"No se pudo guardar el archivo '{nombre_archivo}'.\nCiérralo si está abierto e inténtalo de nuevo.")
        return

    # Restablecer pedidos solo después de guardar con éxito
    for cliente in clientes_con_pedidos:
        cliente["cajas_de_huevos"] = 0

    guardar_datos(data)
    messagebox.showinfo("Éxito", f"Archivo '{nombre_archivo}' generado y pedidos restablecidos.")

# ------------------ Interfaz gráfica ------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Control de Reparto de Huevos")
        self.data = cargar_datos()

        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack()

        tk.Button(frame, text="➕ Agregar cliente", width=20, command=self.ventana_agregar_cliente).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(frame, text="🥚 Nuevo pedido", width=20, command=self.ventana_nuevo_pedido).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame, text="📋 Ver clientes", width=20, command=self.ver_clientes).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(frame, text="📦 Generar reparto", width=20, command=lambda: generar_reparto(self.data)).grid(row=0, column=3, padx=5, pady=5)
        tk.Button(frame, text="🚪 Salir", width=20, command=root.quit).grid(row=0, column=4, padx=5, pady=5)

        self.tree = ttk.Treeview(
            frame,
            columns=("Nombre", "RUT", "Dirección", "Comuna", "Pendiente a entrega", "Total histórico"),
            show="headings",
            height=15
        )

        
        for col in ("Nombre", "RUT", "Dirección", "Comuna", "Pendiente a entrega", "Total histórico"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.grid(row=1, column=0, columnspan=5, pady=10)
        self.ver_clientes()

        tk.Label(frame, text="Versión 1.0.0", fg="gray", font=("Arial", 9, "italic")).grid(row=2, column=0, columnspan=5, pady=(5, 0))


    def ver_clientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for c in self.data:
            self.tree.insert("", "end", values=(
                c["nombre_completo"],
                c.get("rut", ""),
                c["direccion"],
                c["comuna"],
                c["cajas_de_huevos"],
                c["cajas_de_huevos_total"]
            ))

    def ventana_agregar_cliente(self):
        win = tk.Toplevel(self.root)
        win.title("Agregar Cliente")
        win.geometry("300x300")

        labels = ["Nombre completo", "RUT (opcional)", "Dirección", "Comuna", "Cajas iniciales"]
        entries = []
        for text in labels:
            tk.Label(win, text=text).pack()
            entry = tk.Entry(win)
            entry.pack()
            entries.append(entry)

        def agregar():
            try:
                nombre = entries[0].get().strip()
                rut = entries[1].get().strip()
                direccion = entries[2].get().strip()
                comuna = entries[3].get().strip()
                cajas = int(entries[4].get().strip() or 0)
                if not nombre or not direccion or not comuna:
                    messagebox.showerror("Error", "Complete todos los campos obligatorios.")
                    return
                agregar_cliente(self.data, nombre, direccion, comuna, rut, cajas)
                self.ver_clientes()
                win.destroy()
                messagebox.showinfo("Éxito", "Cliente agregado con éxito.")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido para cajas.")

        tk.Button(win, text="Guardar", command=agregar).pack(pady=10)

    def ventana_nuevo_pedido(self):
        win = tk.Toplevel(self.root)
        win.title("Nuevo Pedido")
        win.geometry("300x200")

        tk.Label(win, text="Nombre del cliente:").pack()
        entry_nombre = tk.Entry(win)
        entry_nombre.pack()

        tk.Label(win, text="Cantidad de cajas a agregar:").pack()
        entry_cantidad = tk.Entry(win)
        entry_cantidad.pack()

        def agregar_pedido():
            nombre = entry_nombre.get().strip()
            try:
                cantidad = int(entry_cantidad.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido.")
                return

            if nuevo_pedido(self.data, nombre, cantidad):
                self.ver_clientes()
                messagebox.showinfo("Éxito", f"Pedido agregado a {nombre}.")
                win.destroy()
            else:
                messagebox.showerror("Error", f"No se encontró el cliente '{nombre}'.")

        tk.Button(win, text="Agregar", command=agregar_pedido).pack(pady=10)

# ------------------ Ejecución ------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
