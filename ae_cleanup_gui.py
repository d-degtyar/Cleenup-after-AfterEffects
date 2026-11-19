#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
After Effects Cleanup GUI
Графічний інтерфейс для очистки проектів After Effects
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import shutil
import threading
import logging
from datetime import datetime
from pathlib import Path

# Імпорт наших модулів
from ae_cleanup_core import AECleanupCore, is_after_effects_running
from ae_report_generator import AEReportGenerator

class AECleanupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("After Effects Cleanup Tool - Enhanced")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Змінні для налаштувань
        self.operation_mode = tk.StringVar(value="delete")
        self.target_folder = tk.StringVar()
        self.dry_run_mode = tk.BooleanVar(value=True)
        self.preserve_aep = tk.BooleanVar(value=True)
        self.process_sequences = tk.BooleanVar(value=True)
        self.create_backup_list = tk.BooleanVar(value=True)
        self.min_file_size = tk.IntVar(value=0)
        self.max_file_size = tk.IntVar(value=0)
        
        # Списки файлів та секвенцій
        self.files_to_process = []
        self.sequences_to_process = []
        self.excluded_extensions = set()
        
        # Налаштування логування
        self.setup_logging()
        
        # Ініціалізація основних модулів
        self.cleanup_core = AECleanupCore(self.logger)
        self.report_generator = AEReportGenerator()
        
        # Створення інтерфейсу
        self.create_widgets()
        
        # Завантаження налаштувань
        self.load_settings()
    
    def setup_logging(self):
        """Налаштування системи логування"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_filename = f"ae_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path = log_dir / log_filename
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.log_file_path = log_path
    
    def create_widgets(self):
        """Створення елементів інтерфейсу"""
        # Головний контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Налаштування розтягування
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="After Effects Project Cleanup Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Секція вибору файлу звіту
        self.create_file_selection_section(main_frame, row=1)
        
        # Секція налаштувань операції
        self.create_operation_settings_section(main_frame, row=2)
        
        # Секція фільтрів
        self.create_filters_section(main_frame, row=3)
        
        # Секція безпеки
        self.create_safety_section(main_frame, row=4)
        
        # Кнопки управління
        self.create_control_buttons(main_frame, row=5)
        
        # Область логів та результатів
        self.create_results_section(main_frame, row=6)
        
        # Статус бар
        self.create_status_bar(main_frame, row=7)
        
        # Автоматичний пошук файлу звіту (після створення всіх віджетів)
        self.auto_find_report()
    
    def create_file_selection_section(self, parent, row):
        """Секція вибору файлу звіту"""
        frame = ttk.LabelFrame(parent, text="Файл звіту After Effects", padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(1, weight=1)
        
        ttk.Label(frame, text="Report.txt:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.report_file_var = tk.StringVar()
        self.report_entry = ttk.Entry(frame, textvariable=self.report_file_var, width=50)
        self.report_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(frame, text="Обрати файл", 
                  command=self.select_report_file).grid(row=0, column=2)
    
    def create_operation_settings_section(self, parent, row):
        """Секція налаштувань операції"""
        frame = ttk.LabelFrame(parent, text="Налаштування операції", padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(1, weight=1)
        
        # Режим операції
        ttk.Label(frame, text="Операція:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        operation_frame = ttk.Frame(frame)
        operation_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(operation_frame, text="Видалити файли", 
                       variable=self.operation_mode, value="delete").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(operation_frame, text="Перемістити файли", 
                       variable=self.operation_mode, value="move").pack(side=tk.LEFT)
        
        # Цільова папка для переміщення
        ttk.Label(frame, text="Папка призначення:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        target_frame = ttk.Frame(frame)
        target_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 0))
        target_frame.columnconfigure(0, weight=1)
        
        self.target_entry = ttk.Entry(target_frame, textvariable=self.target_folder)
        self.target_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(target_frame, text="Обрати папку", 
                  command=self.select_target_folder).grid(row=0, column=1)
    
    def create_filters_section(self, parent, row):
        """Секція фільтрів"""
        frame = ttk.LabelFrame(parent, text="Фільтри файлів", padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(1, weight=1)
        
        # Розмір файлів
        size_frame = ttk.Frame(frame)
        size_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(size_frame, text="Мін. розмір (MB):").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(size_frame, textvariable=self.min_file_size, width=10).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(size_frame, text="Макс. розмір (MB):").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(size_frame, textvariable=self.max_file_size, width=10).pack(side=tk.LEFT)
        
        # Виключені розширення
        ttk.Label(frame, text="Виключити типи файлів:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        
        self.extensions_var = tk.StringVar(value=".aep,.aet,.aepx")
        ttk.Entry(frame, textvariable=self.extensions_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E))
    
    def create_safety_section(self, parent, row):
        """Секція безпеки"""
        frame = ttk.LabelFrame(parent, text="Налаштування безпеки", padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        safety_options = ttk.Frame(frame)
        safety_options.pack(fill=tk.X)
        
        ttk.Checkbutton(safety_options, text="Режим попереднього перегляду (Dry Run)", 
                       variable=self.dry_run_mode).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(safety_options, text="Зберігати файли проектів (.aep)", 
                       variable=self.preserve_aep).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(safety_options, text="Обробляти секвенції файлів", 
                       variable=self.process_sequences).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(safety_options, text="Створювати резервний список файлів", 
                       variable=self.create_backup_list).pack(anchor=tk.W, pady=2)
    
    def create_control_buttons(self, parent, row):
        """Кнопки управління"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Аналізувати звіт", 
                  command=self.analyze_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Виконати операцію", 
                  command=self.execute_operation).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Зберегти налаштування", 
                  command=self.save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Очистити лог", 
                  command=self.clear_log).pack(side=tk.LEFT)
    
    def create_results_section(self, parent, row):
        """Область результатів та логів"""
        frame = ttk.LabelFrame(parent, text="Результати та логи", padding="10")
        frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Текстова область з прокруткою
        self.log_text = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Прогрес бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_status_bar(self, parent, row):
        """Статус бар"""
        self.status_var = tk.StringVar(value="Готовий до роботи")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E))
    
    def auto_find_report(self):
        """Автоматичний пошук файлу Report.txt"""
        current_dir = Path.cwd()
        report_files = list(current_dir.glob("*Report*.txt"))
        
        if report_files:
            self.report_file_var.set(str(report_files[0]))
            self.log_message(f"Знайдено файл звіту: {report_files[0]}")
    
    def select_report_file(self):
        """Вибір файлу звіту"""
        filename = filedialog.askopenfilename(
            title="Оберіть файл звіту After Effects",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.report_file_var.set(filename)
    
    def select_target_folder(self):
        """Вибір цільової папки"""
        folder = filedialog.askdirectory(title="Оберіть папку для переміщення файлів")
        if folder:
            self.target_folder.set(folder)
    
    def log_message(self, message):
        """Додавання повідомлення до логу"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
        # Також записуємо в файл логу
        self.logger.info(message)
    
    def clear_log(self):
        """Очищення логу"""
        self.log_text.delete(1.0, tk.END)
    
    def update_status(self, message):
        """Оновлення статус бару"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        """Оновлення прогрес бару"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def save_settings(self):
        """Збереження налаштувань"""
        settings = {
            'operation_mode': self.operation_mode.get(),
            'target_folder': self.target_folder.get(),
            'dry_run_mode': self.dry_run_mode.get(),
            'preserve_aep': self.preserve_aep.get(),
            'process_sequences': self.process_sequences.get(),
            'create_backup_list': self.create_backup_list.get(),
            'min_file_size': self.min_file_size.get(),
            'max_file_size': self.max_file_size.get(),
            'excluded_extensions': self.extensions_var.get()
        }
        
        try:
            with open('ae_cleanup_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self.log_message("Налаштування збережено")
        except Exception as e:
            self.log_message(f"Помилка збереження налаштувань: {e}")
    
    def load_settings(self):
        """Завантаження налаштувань"""
        try:
            if os.path.exists('ae_cleanup_settings.json'):
                with open('ae_cleanup_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.operation_mode.set(settings.get('operation_mode', 'delete'))
                self.target_folder.set(settings.get('target_folder', ''))
                self.dry_run_mode.set(settings.get('dry_run_mode', True))
                self.preserve_aep.set(settings.get('preserve_aep', True))
                self.process_sequences.set(settings.get('process_sequences', True))
                self.create_backup_list.set(settings.get('create_backup_list', True))
                self.min_file_size.set(settings.get('min_file_size', 0))
                self.max_file_size.set(settings.get('max_file_size', 0))
                self.extensions_var.set(settings.get('excluded_extensions', '.aep,.aet,.aepx'))
                
                self.log_message("Налаштування завантажено")
        except Exception as e:
            self.log_message(f"Помилка завантаження налаштувань: {e}")
    
    def analyze_report(self):
        """Аналіз файлу звіту"""
        if not self.report_file_var.get():
            messagebox.showerror("Помилка", "Оберіть файл звіту")
            return
        
        if not os.path.exists(self.report_file_var.get()):
            messagebox.showerror("Помилка", "Файл звіту не знайдено")
            return
        
        # Запуск аналізу в окремому потоці
        threading.Thread(target=self._analyze_report_thread, daemon=True).start()
    
    def _analyze_report_thread(self):
        """Аналіз звіту в окремому потоці"""
        try:
            self.update_status("Аналіз звіту...")
            self.update_progress(0)
            self.log_message("Початок аналізу звіту")
            
            # Очищення попередніх результатів в GUI
            self.files_to_process = []
            self.sequences_to_process = []
            
            # Використовуємо self.cleanup_core для правильного парсингу
            # Це важливо, щоб execute_operation мала доступ до розпарсених файлів
            
            # Парсинг файлу звіту
            success = self.cleanup_core.parse_report_file(
                self.report_file_var.get(), 
                progress_callback=self.update_progress
            )
            
            if success:
                # Застосування фільтрів через Core
                self.update_progress(75)
                self.log_message("Застосування фільтрів...")
                
                filters = {
                    'excluded_extensions': self.extensions_var.get(),
                    'min_file_size': self.min_file_size.get(),
                    'max_file_size': self.max_file_size.get(),
                    'process_sequences': self.process_sequences.get()
                }
                
                self.cleanup_core.apply_filters(filters)
                
                # Конвертуємо результати в формат GUI для відображення
                self.files_to_process = []
                for file_info in self.cleanup_core.files_to_process:
                    self.files_to_process.append({
                        'path': file_info.path,
                        'status': 'exists' if file_info.exists else 'missing',
                        'size': file_info.size / (1024 * 1024) if file_info.size > 0 else 0  # MB
                    })
                
                # Конвертуємо секвенції
                self.sequences_to_process = []
                for seq_info in self.cleanup_core.sequences_to_process:
                    self.sequences_to_process.append({
                        'name': seq_info.name,
                        'pattern': seq_info.pattern,
                        'folder': seq_info.folder_path,
                        'file_count': seq_info.file_count,
                        'auxiliary_count': seq_info.auxiliary_count,
                        'start_frame': seq_info.start_frame,
                        'end_frame': seq_info.end_frame,
                        'extension': seq_info.extension
                    })
                
                self.log_message(f"Після фільтрації залишилось {len(self.files_to_process)} файлів та {len(self.sequences_to_process)} секвенцій")
                
                # Показ результатів
                self.update_progress(100)
                self._show_analysis_results()
                
                self.update_status("Аналіз завершено")
                self.log_message("Аналіз звіту завершено")
            else:
                self.log_message("Помилка парсингу файлу звіту")
                self.update_status("Помилка парсингу")
            
        except Exception as e:
            self.log_message(f"Помилка під час аналізу: {e}")
            self.update_status("Помилка аналізу")
    
    def _show_analysis_results(self):
        """Показ результатів аналізу"""
        total_files = len(self.files_to_process)
        total_sequences = len(self.sequences_to_process)
        
        total_size = sum(file_info.get('size', 0) for file_info in self.files_to_process)
        
        self.log_message("=== РЕЗУЛЬТАТИ АНАЛІЗУ ===")
        self.log_message(f"Файлів для обробки: {total_files}")
        self.log_message(f"Секвенцій для обробки: {total_sequences}")
        self.log_message(f"Загальний розмір: {total_size:.2f} MB")
        self.log_message("=" * 30)
        
        # Показ секвенцій
        if self.sequences_to_process:
            self.log_message("ЗНАЙДЕНІ СЕКВЕНЦІЇ:")
            for i, seq_info in enumerate(self.sequences_to_process):
                self.log_message(f"  {i+1}. {seq_info['name']}")
                self.log_message(f"      Папка: {seq_info['folder']}")
                self.log_message(f"      Кадри: {seq_info['start_frame']}-{seq_info['end_frame']} ({seq_info['file_count']} файлів)")
                self.log_message(f"      Розширення: {seq_info['extension']}")
                if seq_info['auxiliary_count'] > 0:
                    self.log_message(f"      Допоміжних файлів: {seq_info['auxiliary_count']}")
                self.log_message("")
        
        # Показ файлів (обмежуємо до 20 для читабельності)
        if self.files_to_process:
            self.log_message("ФАЙЛИ ДЛЯ ОБРОБКИ:")
            display_limit = min(20, len(self.files_to_process))
            for i, file_info in enumerate(self.files_to_process[:display_limit]):
                size_info = f" ({file_info['size']:.2f} MB)" if file_info['size'] > 0 else ""
                status_info = f" [{file_info['status']}]" if file_info['status'] != 'exists' else ""
                self.log_message(f"  {i+1}. {file_info['path']}{size_info}{status_info}")
            
            if len(self.files_to_process) > display_limit:
                self.log_message(f"  ... та ще {len(self.files_to_process) - display_limit} файлів")
    
    def execute_operation(self):
        """Виконання операції"""
        if not self.files_to_process and not self.sequences_to_process:
            messagebox.showwarning("Попередження", "Немає файлів для обробки. Спочатку проаналізуйте звіт.")
            return
        
        # Перевірка налаштувань
        operation = self.operation_mode.get()
        if operation == "move" and not self.target_folder.get():
            messagebox.showerror("Помилка", "Для переміщення файлів оберіть цільову папку")
            return
        
        # Підтвердження операції
        if not self.dry_run_mode.get():
            # Відкритий After Effects тримає файли проєкту, і їх не вдасться видалити чи перемістити
            if is_after_effects_running() and not messagebox.askyesno(
                "After Effects відкрито",
                "After Effects зараз запущено. Файли, які використовує відкритий проєкт, "
                "він тримає, тож їх буде пропущено.\n\n"
                "Краще закрити After Effects і запустити ще раз.\n\nПродовжити все одно?",
                icon="warning"
            ):
                return
            operation_text = "видалити" if operation == "delete" else "перемістити"
            result = messagebox.askyesno(
                "Підтвердження",
                f"Ви впевнені, що хочете {operation_text} файлів: {len(self.files_to_process)}, "
                f"секвенцій: {len(self.sequences_to_process)}?\n\n"
                f"Ця операція незворотна!",
                icon="warning"
            )
            if not result:
                return
        
        # Запуск операції в окремому потоці
        threading.Thread(target=self._execute_operation_thread, daemon=True).start()
    
    def _execute_operation_thread(self):
        """Виконання операції в окремому потоці"""
        try:
            self.update_status("Виконання операції...")
            operation = self.operation_mode.get()
            target_folder = self.target_folder.get()
            dry_run = self.dry_run_mode.get()
            
            # Використовуємо AECleanupCore для виконання операції
            def progress_callback(progress):
                self.update_progress(progress)
            
            # Виконуємо операцію через AECleanupCore
            results = self.cleanup_core.execute_operation(
                operation=operation,
                target_folder=target_folder,
                dry_run=dry_run,
                progress_callback=progress_callback
            )
            
            # Показ результатів
            self.log_message("=== РЕЗУЛЬТАТИ ОПЕРАЦІЇ ===")
            self.log_message(f"Оброблено файлів: {results['processed_files']}")
            self.log_message(f"Оброблено секвенцій: {results['processed_sequences']}")
            self.log_message(f"Помилок: {len(results['errors'])}")
            self.log_message(f"Пропущено: {len(results['skipped'])}")
            self.log_message(f"Загальний розмір: {results['total_size_processed'] / (1024 * 1024):.2f} MB")
            
            if results['backup_list_path']:
                self.log_message(f"Резервний список збережено: {results['backup_list_path']}")
            
            if results['errors']:
                self.log_message("Помилки:")
                for error in results['errors'][:5]:  # Показуємо перші 5 помилок
                    self.log_message(f"  {error}")
                if len(results['errors']) > 5:
                    self.log_message(f"  ... та ще {len(results['errors']) - 5} помилок")
            
            if results['skipped']:
                self.log_message("Пропущені файли (причина після «->»):")
                for skipped in results['skipped'][:5]:  # Показуємо перші 5 пропущених
                    self.log_message(f"  {skipped}")
                if len(results['skipped']) > 5:
                    self.log_message(f"  ... та ще {len(results['skipped']) - 5} файлів")
            
            mode_text = "Тестовий режим" if dry_run else "Операція"
            self.update_status(f"{mode_text} завершено")
            self.update_progress(100)
            
        except Exception as e:
            self.log_message(f"Критична помилка: {e}")
            self.update_status("Помилка виконання операції")

def main():
    """Головна функція"""
    root = tk.Tk()
    app = AECleanupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()