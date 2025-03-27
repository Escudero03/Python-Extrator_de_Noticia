# Importando bibliotecas necessárias
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser
import threading
import warnings

# Ignorar avisos SSL
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class ExtratorNoticias:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator de Notícias")
        self.root.geometry("700x500")
        
        # Lista de notícias
        self.noticias = []
        
        # Sites pré-configurados
        self.sites = {
            "G1": {
                "url": "https://g1.globo.com/", 
                "seletor": ".feed-post-link, .bastian-feed-item-titulo",
                "seletor_conteudo": ".content-text__container"
            },
            "UOL": {
                "url": "https://www.uol.com.br/", 
                "seletor": ".headlineMain__title, .manchete-texto span",
                "seletor_conteudo": ".text"
            },
            "Terra": {
                "url": "https://www.terra.com.br/", 
                "seletor": ".card-news__text",
                "seletor_conteudo": ".content"
            }
        }
        
        # Criar interface
        self.criar_interface()
    
    def criar_interface(self):
        # Frame superior
        frame_top = ttk.Frame(self.root, padding=10)
        frame_top.pack(fill=tk.X)
        
        # Seleção de site
        ttk.Label(frame_top, text="Site de notícias:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.site_var = tk.StringVar(value="G1")
        site_combo = ttk.Combobox(frame_top, textvariable=self.site_var, values=list(self.sites.keys()), width=15, state="readonly")
        site_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        site_combo.bind("<<ComboboxSelected>>", self.atualizar_campos)
        
        # URL
        ttk.Label(frame_top, text="URL:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_var = tk.StringVar(value=self.sites["G1"]["url"])
        url_entry = ttk.Entry(frame_top, textvariable=self.url_var, width=50)
        url_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Seletor CSS (títulos)
        ttk.Label(frame_top, text="Seletor CSS (títulos):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.seletor_titulo_var = tk.StringVar(value=self.sites["G1"]["seletor"])
        seletor_titulo_entry = ttk.Entry(frame_top, textvariable=self.seletor_titulo_var, width=50)
        seletor_titulo_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Limite de notícias
        ttk.Label(frame_top, text="Limite de notícias:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.qtd_var = tk.StringVar(value="5")
        qtd_spin = ttk.Spinbox(frame_top, from_=1, to=30, textvariable=self.qtd_var, width=5)
        qtd_spin.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Botões
        self.btn_extrair = ttk.Button(frame_top, text="Extrair Notícias", command=self.iniciar_extracao)
        self.btn_extrair.grid(row=3, column=2, padx=5, pady=5)
        
        self.btn_salvar = ttk.Button(frame_top, text="Salvar Resultados", state="disabled")
        self.btn_salvar.grid(row=3, column=3, padx=5, pady=5)
        
        # Frame para as notícias extraídas
        frame_noticias = ttk.LabelFrame(self.root, text="Notícias Extraídas", padding=10)
        frame_noticias.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview para mostrar as notícias
        colunas = ("#", "titulo", "link")
        self.tree = ttk.Treeview(frame_noticias, columns=colunas, show="headings", selectmode="browse")
        self.tree.heading("#", text="#")
        self.tree.heading("titulo", text="Título")
        self.tree.heading("link", text="Link")
        
        # Configurar larguras das colunas
        self.tree.column("#", width=30, anchor="center")
        self.tree.column("titulo", width=500)
        self.tree.column("link", width=120)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(frame_noticias, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        
        # Layout
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        
        # Vincular evento de duplo clique
        self.tree.bind("<Double-1>", self.mostrar_noticia)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto para extrair notícias.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
        
        # Barra de progresso
        self.progresso = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progresso.pack(side="bottom", fill="x", padx=10)
    
    def atualizar_campos(self, event=None):
        """Atualiza os campos com base no site selecionado"""
        site = self.site_var.get()
        if site in self.sites:
            self.url_var.set(self.sites[site]["url"])
            self.seletor_titulo_var.set(self.sites[site]["seletor"])
    
    def extrair_noticias(self, url, seletor, limite):
        """Extrai notícias de um site usando BeautifulSoup"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            # Fazer requisição HTTP
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                # Analisar HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Encontrar elementos de notícia
                elementos = soup.select(seletor)
                
                # Limitar quantidade
                elementos = elementos[:limite]
                
                # Extrair dados
                noticias = []
                for elem in elementos:
                    titulo = elem.text.strip()
                    
                    # Tentar extrair link
                    link = None
                    if elem.name == 'a' and elem.has_attr('href'):
                        link = elem['href']
                    elif elem.find('a') and elem.find('a').has_attr('href'):
                        link = elem.find('a')['href']
                    
                    # Corrigir links relativos
                    if link and not (link.startswith('http://') or link.startswith('https://')):
                        if link.startswith('/'):
                            base_url = url.split('//')
                            dominio = base_url[0] + '//' + base_url[1].split('/')[0]
                            link = dominio + link
                        else:
                            link = url + '/' + link
                    
                    # Adicionar à lista
                    noticias.append({"titulo": titulo, "link": link, "conteudo": None})
                
                return noticias
            else:
                raise Exception(f"Erro na requisição: {response.status_code}")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao extrair notícias: {str(e)}")
            return []
    
    def iniciar_extracao(self):
        """Inicia o processo de extração em uma thread separada"""
        # Limpar árvore atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.noticias = []
        
        # Obter configurações
        site = self.site_var.get()
        url = self.url_var.get()
        seletor = self.seletor_titulo_var.get()
        
        try:
            limite = int(self.qtd_var.get())
        except:
            limite = 5
        
        # Validar URL
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            messagebox.showerror("Erro", "URL inválida. Deve começar com http:// ou https://")
            return
        
        # Validar seletor
        if not seletor:
            messagebox.showerror("Erro", "Seletor CSS é obrigatório")
            return
        
        # Atualizar status
        self.status_var.set(f"Extraindo notícias de {url}...")
        self.btn_extrair.config(state="disabled")
        self.progresso["value"] = 0
        
        # Iniciar thread
        thread = threading.Thread(
            target=self._executar_extracao,
            args=(site, url, seletor, limite)
        )
        thread.daemon = True
        thread.start()
    
    def _executar_extracao(self, site, url, seletor, limite):
        """Função executada em thread separada"""
        try:
            # Extrair notícias
            self.noticias = self.extrair_noticias(url, seletor, limite)
            
            # Atualizar interface na thread principal
            self.root.after(0, self._atualizar_lista)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na extração: {str(e)}"))
            self.root.after(0, self._finalizar_extracao)
    
    def _atualizar_lista(self):
        """Atualiza a treeview com as notícias extraídas"""
        if not self.noticias:
            messagebox.showinfo("Informação", "Nenhuma notícia encontrada")
        else:
            # Adicionar notícias à árvore
            for i, noticia in enumerate(self.noticias, 1):
                link_status = "Disponível" if noticia["link"] else "Não solicitado"
                self.tree.insert("", "end", values=(i, noticia["titulo"], link_status))
        
        self._finalizar_extracao()
    
    def _finalizar_extracao(self):
        """Atualiza a interface após a extração"""
        self.status_var.set(f"Foram extraídas {len(self.noticias)} notícias.")
        self.btn_extrair.config(state="normal")
        self.progresso["value"] = 100
    
    def extrair_conteudo(self, url, site):
        """Extrai o conteúdo de uma notícia específica"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Usar seletor adequado para o site
                seletor_conteudo = self.sites.get(site, {}).get("seletor_conteudo", "p")
                
                # Tentar diferentes estratégias para encontrar o conteúdo
                conteudo_elementos = soup.select(seletor_conteudo)
                
                if conteudo_elementos:
                    # Extrair texto de cada elemento de conteúdo
                    conteudo = "\n\n".join([elem.text.strip() for elem in conteudo_elementos])
                    return conteudo
                else:
                    # Estratégia alternativa: pegar os primeiros parágrafos
                    paragrafos = soup.find_all('p', limit=5)
                    if paragrafos:
                        conteudo = "\n\n".join([p.text.strip() for p in paragrafos])
                        return conteudo
            
            return "Não foi possível extrair o conteúdo da notícia."
        
        except Exception as e:
            return f"Erro ao acessar a notícia: {str(e)}"
    
    def mostrar_noticia(self, event):
        """Mostra janela com detalhes da notícia selecionada"""
        # Obter item selecionado
        item = self.tree.selection()
        if not item:
            return
        
        # Obter valores
        valores = self.tree.item(item, "values")
        if not valores:
            return
        
        # Obter índice (ajustado para base 0)
        indice = int(valores[0]) - 1
        
        # Verificar se índice é válido
        if indice < 0 or indice >= len(self.noticias):
            return
        
        # Obter notícia
        noticia = self.noticias[indice]
        titulo = noticia["titulo"]
        link = noticia["link"]
        
        # Criar janela
        janela = tk.Toplevel(self.root)
        janela.title("Visualizar Notícia")
        janela.geometry("600x500")
        janela.grab_set()  # Fazer modal
        
        # Frame principal
        frame = ttk.Frame(janela, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo_lbl = ttk.Label(frame, text=titulo, font=("Helvetica", 12, "bold"), wraplength=580)
        titulo_lbl.pack(pady=(0, 10), anchor="w")
        
        # Frame para conteúdo
        frame_conteudo = ttk.LabelFrame(frame, text="Trecho da Notícia")
        frame_conteudo.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Área de texto para o conteúdo
        conteudo_text = scrolledtext.ScrolledText(frame_conteudo, wrap=tk.WORD, font=("Helvetica", 10))
        conteudo_text.pack(fill=tk.BOTH, expand=True)
        
        # Inicialmente, mostrar mensagem de carregamento
        conteudo_text.insert(tk.END, "Carregando conteúdo da notícia...\n\nPor favor, aguarde.")
        conteudo_text.config(state="disabled")
        
        # Se tiver link, adicionar seção de link
        if link:
            # Frame para link
            link_frame = ttk.Frame(frame, padding=5)
            link_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(link_frame, text="Link:").pack(side=tk.LEFT)
            
            # Entry com o link
            link_var = tk.StringVar(value=link)
            link_entry = ttk.Entry(link_frame, textvariable=link_var, width=50)
            link_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Botão para abrir no navegador
            abrir_btn = ttk.Button(
                link_frame, 
                text="Abrir no Navegador", 
                command=lambda: webbrowser.open(link)
            )
            abrir_btn.pack(side=tk.RIGHT)
            
            # Carregar conteúdo em thread separada
            def carregar_conteudo():
                site = self.site_var.get()
                conteudo = self.extrair_conteudo(link, site)
                
                # Atualizar texto na thread principal
                janela.after(0, lambda: atualizar_conteudo_text(conteudo))
            
            def atualizar_conteudo_text(conteudo):
                conteudo_text.config(state="normal")
                conteudo_text.delete(1.0, tk.END)
                conteudo_text.insert(tk.END, conteudo)
                conteudo_text.config(state="disabled")
            
            # Iniciar thread
            thread = threading.Thread(target=carregar_conteudo)
            thread.daemon = True
            thread.start()
        else:
            conteudo_text.config(state="normal")
            conteudo_text.delete(1.0, tk.END)
            conteudo_text.insert(tk.END, "Link não disponível para esta notícia.")
            conteudo_text.config(state="disabled")
        
        # Botão fechar
        fechar_btn = ttk.Button(frame, text="Fechar", command=janela.destroy)
        fechar_btn.pack(pady=10)

# Função principal
def main():
    root = tk.Tk()
    app = ExtratorNoticias(root)
    root.mainloop()

# Executar o programa
if __name__ == "__main__":
    main()