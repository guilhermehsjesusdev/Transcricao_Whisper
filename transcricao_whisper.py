import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import threading
import whisper
import time
import os
import shutil
import tempfile
import subprocess
import sys

# ---------- REDIRECIONADOR DE PRINT PARA TKINTER ----------
class Redirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)

    def flush(self):
        pass

# ---------- ADICIONAR FFMPEG AO PATH ----------
ffmpeg_path = r"C:\ffmpeg"
os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

try:
    subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    messagebox.showwarning("Aviso", f"FFmpeg não encontrado no caminho: {ffmpeg_path}\nVídeos podem não ser processados.")

# ---------- CARREGAR MODELO ----------
print("Carregando modelo Whisper 'base'... isso pode demorar um pouco.")
model = whisper.load_model("base")
print("Modelo carregado!")

# ---------- VARIÁVEL GLOBAL ----------
resultado_global = ""  # Armazena o texto completo da transcrição

# ---------- FUNÇÃO PARA FORMATAR TEMPO ----------
def formatar_tempo(segundo):
    minutos = int(segundo // 60)
    segundos = int(segundo % 60)
    milissegundos = int((segundo - int(segundo)) * 1000)
    return f"{minutos:02d}:{segundos:02d}.{milissegundos:03d}"

# ---------- FUNÇÃO DE TRANSCRIÇÃO ----------
def transcrever_audio(caminho_arquivo):
    global resultado_global
    resultado_global = ""
    saida_texto.insert(tk.END, "Transcrevendo...\n")
    saida_texto.see(tk.END)

    # Barra de progresso animada
    animando = True
    def animar_barra():
        if animando:
            barra_progresso["value"] = (barra_progresso["value"] + 2) % 100
            janela.after(50, animar_barra)
    animar_barra()

    def rodar_transcricao():
        global resultado_global
        nonlocal animando
        try:
            resultado = model.transcribe(caminho_arquivo, verbose=True)
            texto_completo = resultado["text"]

            resultado_global = texto_completo
            saida_texto.insert(tk.END, "\n=== TRANSCRIÇÃO COMPLETA ===\n\n")
            saida_texto.insert(tk.END, resultado_global)
            saida_texto.see(tk.END)

        except Exception as e:
            janela.after(0, lambda: messagebox.showerror("Erro", f"Ocorreu um erro: {e}"))
            animando = False
            return

        # ---------- SALVAR SEMPRE NA PASTA DA ÁREA DE TRABALHO ----------
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        pasta_transcricao = os.path.join(desktop, "Transcricao")

        # Criar pasta se não existir
        if not os.path.exists(pasta_transcricao):
            os.makedirs(pasta_transcricao)

        nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
        arquivo_saida = os.path.join(pasta_transcricao, f"{nome_base}_transcricao.txt")

        try:
            with open(arquivo_saida, "w", encoding="utf-8") as f:
                f.write(resultado_global)
        except Exception as e:
            janela.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível salvar a transcrição:\n{e}"))

        animando = False
        janela.after(0, lambda: barra_progresso.config(value=0))
        janela.after(0, lambda: messagebox.showinfo("Finalizado", f"Transcrição concluída!\nArquivo salvo em:\n{arquivo_saida}"))

    threading.Thread(target=rodar_transcricao, daemon=True).start()

# ---------- FUNÇÃO DE CARREGAR ARQUIVO ----------
def carregar_arquivo():
    caminho = filedialog.askopenfilename(
        title="Selecione o arquivo de vídeo/áudio",
        filetypes=[
            ("Todos os vídeos e áudios", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.mp3 *.wav *.m4a"),
            ("Todos os arquivos", "*.*")
        ]
    )
    if not caminho:
        return

    caminho = os.path.abspath(caminho)

    # Copiar para pasta temporária
    temp_dir = tempfile.gettempdir()
    arquivo_temp = os.path.join(temp_dir, os.path.basename(caminho))
    try:
        shutil.copy2(caminho, arquivo_temp)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível copiar o arquivo:\n{e}")
        return

    saida_texto.delete(1.0, tk.END)
    saida_texto.insert(tk.END, f"Arquivo selecionado:\n{arquivo_temp}\n\n")
    saida_texto.see(tk.END)

    transcrever_audio(arquivo_temp)

# ---------- INTERFACE TKINTER ----------
janela = tk.Tk()
janela.title("Transcrição com Whisper")
janela.geometry("700x500")

frame_topo = tk.Frame(janela)
frame_topo.pack(pady=10)

btn_carregar = tk.Button(frame_topo, text="Carregar Vídeo/Áudio", command=carregar_arquivo)
btn_carregar.pack()

barra_progresso = ttk.Progressbar(janela, orient="horizontal", mode="determinate", length=500)
barra_progresso.pack(pady=10)

saida_texto = scrolledtext.ScrolledText(janela, width=80, height=20)
saida_texto.pack(pady=10)

# Redireciona prints para o ScrolledText
sys.stdout = Redirector(saida_texto)
sys.stderr = Redirector(saida_texto)

janela.mainloop()
