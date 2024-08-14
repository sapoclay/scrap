import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk, ImageSequence
import subprocess
import threading
import webbrowser

# Inicializar la variable global 'process'
process = None

def list_py_files():
    """Lista todos los archivos .py en el directorio 'webs' sin la extensión."""
    directory = "webs"
    if os.path.exists(directory):
        return [f[:-3] for f in os.listdir(directory) if f.endswith('.py')]  # Remover la extensión .py
    return []

def list_html_files():
    """Lista todos los archivos .html en el directorio 'webs'."""
    directory = "webs"
    if os.path.exists(directory):
        return [f for f in os.listdir(directory) if f.endswith('.html')]
    return []

def run_selected_file():
    """Ejecuta el archivo .py seleccionado y muestra una ventana de progreso."""
    global process  # Asegurar que 'process' sea la variable global

    selected_file = selected_file_var.get()
    if selected_file:
        file_path = os.path.join('webs', f"{selected_file}.py")  # Añadir de nuevo la extensión .py

        # Crear una ventana de progreso
        progress_window = tk.Toplevel()
        progress_window.title("Progreso")
        progress_window.geometry("300x150")
        progress_window.resizable(False, False)  # Evitar redimensionamiento

        # Cargar el GIF animado
        gif_path = 'loading.gif'  # Ruta al archivo GIF animado
        gif_image = Image.open(gif_path)
        gif_frames = []

        # Redimensionar cada frame del GIF
        width, height = 30, 30  # Nuevas dimensiones
        for frame in ImageSequence.Iterator(gif_image):
            resized_frame = frame.copy()
            resized_frame.thumbnail((width, height))
            gif_frames.append(ImageTk.PhotoImage(resized_frame))

        # Crear una etiqueta para mostrar el GIF animado
        gif_label = tk.Label(progress_window)
        gif_label.pack(pady=10)

        # Función para actualizar el GIF animado
        def update_gif(frame_index=0):
            if gif_label.winfo_exists():  # Verifica si el widget aún existe
                gif_label.config(image=gif_frames[frame_index])
                progress_window.after(100, update_gif, (frame_index + 1) % len(gif_frames))  # Actualizar cada 100 ms

        update_gif()

        tk.Label(progress_window, text="Ejecutando, por favor espera... \n¡Esto puede tardar un poco!").pack(pady=10)
        progress_window.grab_set()  # Bloquea la ventana principal mientras se muestra la ventana de progreso

        html_file_path = file_path.replace('.py', '.html')

        # Función para ejecutar el archivo .py
        def run_file():
            global process  # Asegurar que 'process' sea la variable global
            try:
                process = subprocess.Popen(['python3', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate()  # Esperar a que el proceso termine
                if process.returncode == 0 and os.path.exists(html_file_path):
                    messagebox.showinfo("Ejecución Exitosa", f"El archivo {selected_file} se ejecutó correctamente.")
                    
                    # Preguntar al usuario si desea abrir el archivo .html generado
                    open_html = messagebox.askyesno("Abrir archivo HTML", "¿Quieres abrir el registro de URL generado en el navegador?")
                    if open_html:
                        webbrowser.open(f'file://{os.path.abspath(html_file_path)}')
                else:
                    messagebox.showinfo("Archivo HTML no encontrado", "El archivo HTML generado no se encontró.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error de Ejecución", f"Hubo un error al ejecutar {selected_file}: {e}")
            finally:
                progress_window.destroy()  # Cierra la ventana de progreso cuando termine

        # Función para manejar el cierre de la ventana de progreso
        def on_closing():
            if process:
                process.terminate()  # Terminar el proceso si está en ejecución
                process.wait()  # Esperar a que el proceso termine correctamente
            progress_window.destroy()

        # Asociar la función on_closing con el evento de cierre de la ventana
        progress_window.protocol("WM_DELETE_WINDOW", on_closing)

        # Iniciar el hilo
        threading.Thread(target=run_file).start()
    else:
        messagebox.showwarning("Selección Vacía", "Por favor, selecciona un archivo para ejecutar.")

def exit_program():
    """Pregunta al usuario si realmente desea salir y cierra el programa."""
    global process  # Asegurar que 'process' sea la variable global
    if messagebox.askokcancel("Salir", "¿Realmente deseas salir del programa?"):
        if process:
            process.terminate()  # Terminar cualquier proceso en ejecución
            process.wait()
        root.destroy()

def show_html_files():
    """Muestra una ventana con la lista de archivos .html y la opción de abrirlos en el navegador."""
    html_files = list_html_files()

    if not html_files:
        messagebox.showinfo("No hay archivos HTML", "No se encontraron archivos HTML en el directorio 'webs'.")
        return

    # Crear una nueva ventana
    list_window = tk.Toplevel()
    list_window.title("Listados de Archivos HTML")
    list_window.geometry("400x300")
    list_window.resizable(False, False)  # Evitar redimensionamiento

    # Lista de archivos HTML
    listbox = tk.Listbox(list_window, selectmode=tk.SINGLE)
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for html_file in html_files:
        listbox.insert(tk.END, html_file)

    def open_selected_html():
        """Abre el archivo HTML seleccionado en el navegador predeterminado."""
        selected_html = listbox.get(tk.ACTIVE)
        if selected_html:
            webbrowser.open(f'file://{os.path.abspath(os.path.join("webs", selected_html))}')
        else:
            messagebox.showwarning("Selección Vacía", "Por favor, selecciona un archivo HTML para abrir.")

    # Botón para abrir el archivo HTML seleccionado
    open_button = tk.Button(list_window, text="Abrir en navegador", command=open_selected_html)
    open_button.pack(pady=10)

def main():
    global root
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Scrapear Webs")
    root.geometry("400x200")
    root.resizable(False, False)  # Evitar redimensionamiento

    # Crear la barra de menú
    menubar = tk.Menu(root)

    # Menú Archivo
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Salir", command=exit_program)
    menubar.add_cascade(label="Archivo", menu=file_menu)

    # Menú Opciones
    options_menu = tk.Menu(menubar, tearoff=0)
    options_menu.add_command(label="Listados", command=show_html_files)
    menubar.add_cascade(label="Opciones", menu=options_menu)

    # Configurar la barra de menú
    root.config(menu=menubar)

    # Listar los archivos .py en el directorio 'webs'
    py_files = list_py_files()

    # Variable para almacenar la selección del usuario
    global selected_file_var
    selected_file_var = tk.StringVar(root)
    selected_file_var.set(py_files[0] if py_files else "No hay archivos .py")

    # Crear el menú desplegable (OptionMenu)
    label = tk.Label(root, text="Selecciona un archivo de alguna Web para comenzar:")
    label.pack(pady=10)

    option_menu = tk.OptionMenu(root, selected_file_var, *py_files)
    option_menu.pack(pady=10)

    # Crear el botón para ejecutar el archivo seleccionado
    execute_button = tk.Button(root, text="Ejecutar", command=run_selected_file)
    execute_button.pack(pady=20)

    # Ejecutar la aplicación
    root.mainloop()

if __name__ == "__main__":
    main()