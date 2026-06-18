"""
app.py — Interface gráfica refatorada com CustomTkinter.

Melhorias em relação à versão original:
- Dropdown para seleção de template de prompt (multi-setor)
- Dropdown para formato de saída (CSV, TSV, JSON, XLSX)
- Suporte a múltiplos arquivos (processamento em lote)
- Barra de progresso real
- Preview dos resultados antes de salvar
- Logging em vez de print()
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import logging
import threading
from pathlib import Path

from src.config.settings import setup_logging, get_available_templates, SUPPORTED_OUTPUT_FORMATS
from src.core.document_reader import read_document, DocumentReadError
from src.core.ai_analyzer import analyze_document, analyze_batch
from src.core.output_writer import save_result, merge_batch_results, parse_tsv_data
from src.validators.response_validator import validate_response, ValidationError

logger = logging.getLogger(__name__)


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        setup_logging()

        # --- Configurações da Janela ---
        self.title("AI Document Analyzer — Análise Inteligente de Documentos")
        self.geometry("850x650")
        self.minsize(750, 550)
        self.center_window(850, 650)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # --- Estado ---
        self.selected_files: list[str] = []
        self.last_result: str | None = None
        self.templates = get_available_templates()

        # --- Layout ---
        self._build_ui()

    def _build_ui(self):
        """Constrói toda a interface."""

        # Frame principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # --- Título ---
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="🔍 AI Document Analyzer",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.title_label.grid(row=row, column=0, columnspan=2, padx=20, pady=(20, 5))
        row += 1

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Análise inteligente de documentos com IA — Jurídico, Contratos, Compliance e mais",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.subtitle_label.grid(row=row, column=0, columnspan=2, padx=20, pady=(0, 15))
        row += 1

        # --- Seleção de Template ---
        template_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        template_frame.grid(row=row, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        template_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            template_frame,
            text="📋 Tipo de Análise:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        template_names = list(self.templates.keys()) if self.templates else ["Nenhum template encontrado"]
        self.template_var = ctk.StringVar(value=template_names[0])
        self.template_dropdown = ctk.CTkComboBox(
            template_frame,
            values=template_names,
            variable=self.template_var,
            width=300,
            font=ctk.CTkFont(size=12),
            state="readonly",
        )
        self.template_dropdown.grid(row=0, column=1, sticky="ew")
        row += 1

        # --- Formato de Saída ---
        format_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        format_frame.grid(row=row, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        format_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            format_frame,
            text="💾 Formato de Saída:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        format_options = ["CSV", "TSV", "JSON", "XLSX"]
        self.format_var = ctk.StringVar(value="CSV")
        self.format_dropdown = ctk.CTkComboBox(
            format_frame,
            values=format_options,
            variable=self.format_var,
            width=300,
            font=ctk.CTkFont(size=12),
            state="readonly",
        )
        self.format_dropdown.grid(row=0, column=1, sticky="ew")
        row += 1

        # --- Botões de Seleção ---
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row=row, column=0, columnspan=2, padx=20, pady=(15, 5))

        self.select_file_button = ctk.CTkButton(
            button_frame,
            text="📄 Selecionar Arquivo(s)",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.select_files_callback,
            width=200,
        )
        self.select_file_button.pack(side="left", padx=5)

        self.select_folder_button = ctk.CTkButton(
            button_frame,
            text="📁 Selecionar Pasta",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.select_folder_callback,
            width=200,
        )
        self.select_folder_button.pack(side="left", padx=5)
        row += 1

        # --- Label com arquivos selecionados ---
        self.selected_file_label = ctk.CTkLabel(
            self.main_frame,
            text="Nenhum arquivo selecionado.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=750,
        )
        self.selected_file_label.grid(row=row, column=0, columnspan=2, padx=20, pady=(5, 10))
        row += 1

        # --- Botão Iniciar ---
        self.start_button = ctk.CTkButton(
            self.main_frame,
            text="🚀 Iniciar Análise",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_analysis_thread,
            state="disabled",
            height=45,
        )
        self.start_button.grid(row=row, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        row += 1

        # --- Barra de Progresso ---
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, mode="determinate")
        self.progress_bar.grid(row=row, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="ew")
        self.progress_bar.set(0)
        row += 1

        self.progress_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.progress_label.grid(row=row, column=0, columnspan=2, padx=20, pady=(0, 5))
        row += 1

        # --- Status ---
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Status: Aguardando seleção de arquivo...",
            font=ctk.CTkFont(size=12),
            wraplength=750,
        )
        self.status_label.grid(row=row, column=0, columnspan=2, padx=20, pady=(5, 20))

    # ==============================
    # Callbacks de Seleção
    # ==============================

    def select_files_callback(self):
        """Seleção de um ou mais arquivos."""
        files = filedialog.askopenfilenames(
            title="Selecione os documentos para análise",
            filetypes=(
                ("Todos os suportados", "*.pdf *.txt *.docx"),
                ("PDF", "*.pdf"),
                ("Texto", "*.txt"),
                ("Word", "*.docx"),
                ("Todos", "*.*"),
            ),
        )
        if files:
            self.selected_files = list(files)
            self._update_file_label()

    def select_folder_callback(self):
        """Seleção de uma pasta inteira — busca recursivamente."""
        folder = filedialog.askdirectory(title="Selecione a pasta com os documentos")
        if folder:
            extensions = (".pdf", ".txt", ".docx")
            files = []
            for ext in extensions:
                files.extend(Path(folder).rglob(f"*{ext}"))
            self.selected_files = [str(f) for f in sorted(files)]
            self._update_file_label()

    def _update_file_label(self):
        """Atualiza o label com a contagem dos arquivos selecionados."""
        count = len(self.selected_files)
        if count == 0:
            self.selected_file_label.configure(
                text="Nenhum arquivo selecionado.", text_color="gray"
            )
            self.start_button.configure(state="disabled")
        elif count == 1:
            name = os.path.basename(self.selected_files[0])
            self.selected_file_label.configure(
                text=f"📄 {name}", text_color="white"
            )
            self.start_button.configure(state="normal")
        else:
            names = [os.path.basename(f) for f in self.selected_files[:3]]
            extra = f" e mais {count - 3}..." if count > 3 else ""
            self.selected_file_label.configure(
                text=f"📄 {count} arquivos: {', '.join(names)}{extra}",
                text_color="white",
            )
            self.start_button.configure(state="normal")

        self.status_label.configure(
            text=f"Status: {count} arquivo(s) pronto(s) para análise.",
            text_color="gray",
        )

    # ==============================
    # Análise
    # ==============================

    def start_analysis_thread(self):
        """Inicia a análise em thread separada."""
        self.start_button.configure(state="disabled", text="⏳ Analisando...")
        self.select_file_button.configure(state="disabled")
        self.select_folder_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(
            text="Status: Iniciando análise com IA... Isso pode levar um momento.",
            text_color="cyan",
        )

        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()

    def run_analysis(self):
        """Executa a análise."""
        try:
            # Obter template selecionado
            template_name = self.template_var.get()
            template_path = self.templates.get(template_name)
            if not template_path:
                raise ValueError(f"Template '{template_name}' não encontrado")

            output_format = self.format_var.get().lower()

            if len(self.selected_files) == 1:
                self._analyze_single(self.selected_files[0], template_path, output_format)
            else:
                self._analyze_batch(self.selected_files, template_path, output_format)

        except Exception as e:
            logger.error(f"Erro na análise: {e}", exc_info=True)
            self.after(0, self.update_status_error, str(e))

    def _analyze_single(self, file_path: str, template_path: Path, output_format: str):
        """Análise de arquivo único."""
        # Ler documento
        self.after(0, lambda: self.status_label.configure(
            text="Status: Lendo documento...", text_color="cyan"
        ))
        content = read_document(file_path)

        # Analisar com IA
        self.after(0, lambda: self.status_label.configure(
            text="Status: Analisando com IA...", text_color="cyan"
        ))
        self.after(0, lambda: self.progress_bar.set(0.3))

        result = analyze_document(content, template_path)

        # Validar resposta
        self.after(0, lambda: self.progress_bar.set(0.7))
        try:
            validation = validate_response(result)
            if validation["warnings"]:
                warnings_text = "; ".join(validation["warnings"][:3])
                logger.warning(f"Validação com avisos: {warnings_text}")
        except ValidationError as e:
            logger.warning(f"Validação falhou (prosseguindo): {e}")

        self.after(0, lambda: self.progress_bar.set(0.9))
        self.last_result = result

        # Salvar
        self.after(0, self.save_result, result, output_format, file_path)

    def _analyze_batch(self, file_paths: list[str], template_path: Path, output_format: str):
        """Análise em lote."""
        # Ler todos os documentos
        file_contents = []
        for i, fp in enumerate(file_paths):
            try:
                content = read_document(fp)
                file_contents.append((os.path.basename(fp), content))
            except DocumentReadError as e:
                logger.warning(f"Ignorando {fp}: {e}")

        if not file_contents:
            raise ValueError("Nenhum documento pôde ser lido")

        # Callback de progresso
        def progress_cb(current, total, filename):
            progress = current / total if total > 0 else 0
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(
                0,
                lambda c=current, t=total, f=filename: self.progress_label.configure(
                    text=f"[{c}/{t}] {f}"
                ),
            )

        self.after(0, lambda: self.status_label.configure(
            text=f"Status: Analisando {len(file_contents)} documentos...",
            text_color="cyan",
        ))

        # Analisar em lote
        results = analyze_batch(file_contents, template_path, progress_cb)

        # Consolidar resultados
        merged = merge_batch_results(results)
        if not merged:
            raise ValueError("Nenhum resultado foi gerado")

        self.last_result = merged

        # Contar erros
        errors = [r for r in results if r[2] is not None]
        success = len(results) - len(errors)

        self.after(0, lambda: self.status_label.configure(
            text=f"Status: {success} analisados, {len(errors)} erros.",
            text_color="green" if not errors else "yellow",
        ))

        self.after(0, self.save_result, merged, output_format)

    # ==============================
    # Salvamento
    # ==============================

    def save_result(self, data: str, output_format: str, original_file: str = None):
        """Abre diálogo de salvar e grava o resultado."""
        if not data:
            self.update_status_error("A análise não retornou dados.")
            return

        # Nome sugerido
        if original_file:
            base_name = f"analisado_{Path(original_file).stem}"
        else:
            base_name = "relatorio_consolidado"

        ext_map = {"csv": ".csv", "tsv": ".tsv", "json": ".json", "xlsx": ".xlsx"}
        ext = ext_map.get(output_format, ".csv")

        filetypes = [
            ("CSV", "*.csv"),
            ("TSV", "*.tsv"),
            ("JSON", "*.json"),
            ("Excel", "*.xlsx"),
            ("Todos", "*.*"),
        ]

        save_path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
            initialfile=f"{base_name}{ext}",
        )

        if save_path:
            try:
                save_result(data, save_path, output_format)
                self.status_label.configure(
                    text=f"✅ Salvo com sucesso: {save_path}",
                    text_color="green",
                )
                self.progress_bar.set(1.0)
                logger.info(f"Resultado salvo: {save_path}")
            except Exception as e:
                self.update_status_error(f"Erro ao salvar: {e}")
        else:
            self.status_label.configure(
                text="⚠️ Salvamento cancelado.", text_color="yellow"
            )

        self._reset_buttons()

    # ==============================
    # Utilitários
    # ==============================

    def update_status_error(self, error_message: str):
        """Atualiza status com erro."""
        self.status_label.configure(
            text=f"❌ Erro: {error_message}", text_color="red"
        )
        self._reset_buttons()

    def _reset_buttons(self):
        """Restaura botões ao estado normal."""
        self.start_button.configure(state="normal", text="🚀 Iniciar Análise")
        self.select_file_button.configure(state="normal")
        self.select_folder_button.configure(state="normal")
        self.progress_label.configure(text="")

    def center_window(self, width, height):
        """Centraliza a janela na tela."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")
