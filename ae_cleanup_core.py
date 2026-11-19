#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
After Effects Cleanup Core Module
Основний модуль з логікою обробки файлів
"""

import os
import re
import shutil
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

from ae_sequence_parser import FileSequenceParser, SequenceInfo

# Службові файли, через які папка не вважається "непорожньою"
JUNK_FILE_NAMES = {'thumbs.db', '.ds_store', 'desktop.ini'}

LOCKED_HINT = ("файл зайнятий іншою програмою (After Effects, Premiere, Провідник). "
               "Закрийте її та запустіть ще раз")


def is_locked_error(error: Exception) -> bool:
    """Чи означає помилка, що файл тримає інша програма"""
    text = str(error)
    return (isinstance(error, PermissionError) or "[WinError 32]" in text
            or "being used by another process" in text.lower())


def is_after_effects_running() -> bool:
    """Чи запущено After Effects: файли відкритого проєкту він тримає і їх не можна видалити"""
    try:
        if sys.platform.startswith("win"):
            output = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq AfterFX.exe", "/NH"],
                capture_output=True, text=True, timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).stdout
            return "afterfx.exe" in output.lower()
        result = subprocess.run(["pgrep", "-f", "After Effects"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

class FileInfo:
    """Інформація про файл для обробки"""
    def __init__(self, path: str, size: int = 0, is_sequence: bool = False):
        self.path = path
        self.size = size
        self.is_sequence = is_sequence
        self.exists = os.path.exists(path)
        self.extension = Path(path).suffix.lower()
        self.name = Path(path).name

class AECleanupCore:
    """Основний клас для обробки очистки After Effects проектів"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.sequence_parser = FileSequenceParser()
        # Причина, з якої останній файл чи секвенцію пропущено (для звіту)
        self._last_skip_reason = ""
        
        # Списки для обробки
        self.files_to_process: List[FileInfo] = []
        self.sequences_to_process: List[SequenceInfo] = []
        self.missing_files: List[str] = []
        
        # Статистика
        self.stats = {
            'total_files': 0,
            'total_sequences': 0,
            'total_size': 0,
            'processed_files': 0,
            'processed_sequences': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def parse_report_file(self, report_path: str, progress_callback=None) -> bool:
        """
        Парсинг файлу звіту After Effects
        
        Args:
            report_path: Шлях до файлу звіту
            progress_callback: Функція для оновлення прогресу
            
        Returns:
            True якщо парсинг успішний
        """
        try:
            if not os.path.exists(report_path):
                self.logger.error(f"Файл звіту не знайдено: {report_path}")
                return False
            
            self.logger.info(f"Початок парсингу файлу: {report_path}")
            
            # Очищення попередніх результатів
            self.files_to_process.clear()
            self.sequences_to_process.clear()
            self.missing_files.clear()
            
            with open(report_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            processed_lines = 0
            
            for line in lines:
                line = line.strip()
                
                # Видаляємо табуляцію
                line = re.sub(r'\t+', '', line)
                
                if not line:
                    continue
                
                # Перевіряємо чи це секвенція
                sequence_info = self.sequence_parser.parse_sequence_line(line)
                if sequence_info:
                    self.sequences_to_process.append(sequence_info)
                    self.logger.debug(f"Знайдено секвенцію: {sequence_info.name}")
                else:
                    # Перевіряємо чи це файл
                    if self._is_file_path(line):
                        file_info = self._create_file_info(line)
                        if file_info:
                            if file_info.exists:
                                self.files_to_process.append(file_info)
                            else:
                                self.missing_files.append(line)
                
                processed_lines += 1
                if progress_callback and processed_lines % 10 == 0:
                    progress = (processed_lines / total_lines) * 100
                    progress_callback(progress)
            
            # Оновлення статистики
            self._update_stats()
            
            self.logger.info(f"Парсинг завершено. Файлів: {len(self.files_to_process)}, "
                           f"Секвенцій: {len(self.sequences_to_process)}, "
                           f"Відсутніх: {len(self.missing_files)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Помилка парсингу файлу звіту: {e}")
            return False
    
    def _is_file_path(self, line: str) -> bool:
        """Перевірка чи є рядок шляхом до файлу"""
        line = line.strip()
        
        # Перевіряємо базові критерії шляху
        if len(line) < 3:
            return False
        
        # Windows шляхи: C:\, D:\, \\server\
        if (len(line) > 2 and line[1] == ':' and line[2] == '\\') or \
           (line.startswith('\\\\') and '\\' in line[2:]):
            return True
        
        # Unix шляхи: /path/to/file
        if line.startswith('/') and '/' in line[1:]:
            return True
        
        return False
    
    def _create_file_info(self, file_path: str) -> Optional[FileInfo]:
        """Створення об'єкта FileInfo"""
        try:
            size = 0
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
            
            return FileInfo(file_path, size)
        except Exception as e:
            self.logger.warning(f"Помилка створення FileInfo для {file_path}: {e}")
            return None
    
    def _update_stats(self):
        """Оновлення статистики"""
        self.stats['total_files'] = len(self.files_to_process)
        self.stats['total_sequences'] = len(self.sequences_to_process)
        
        total_size = sum(f.size for f in self.files_to_process)
        
        # Додаємо розмір секвенцій
        for sequence in self.sequences_to_process:
            validation = self.sequence_parser.validate_sequence(sequence)
            total_size += validation.get('total_size', 0)
        
        self.stats['total_size'] = total_size
    
    def apply_filters(self, filters: Dict) -> None:
        """
        Застосування фільтрів до списку файлів
        
        Args:
            filters: Словник з параметрами фільтрації
        """
        self.logger.info("Застосування фільтрів")
        
        # Фільтр за розширеннями
        excluded_extensions = set()
        if 'excluded_extensions' in filters:
            ext_string = filters['excluded_extensions']
            excluded_extensions = {ext.strip().lower() for ext in ext_string.split(',')}
        
        # Фільтр за розміром
        min_size = filters.get('min_file_size', 0) * 1024 * 1024  # MB to bytes
        max_size = filters.get('max_file_size', 0) * 1024 * 1024
        
        # Фільтрація файлів
        filtered_files = []
        for file_info in self.files_to_process:
            # Перевірка розширення
            if file_info.extension in excluded_extensions:
                self.logger.debug(f"Виключено за розширенням: {file_info.path}")
                continue
            
            # Перевірка розміру
            if min_size > 0 and file_info.size < min_size:
                self.logger.debug(f"Виключено за мінімальним розміром: {file_info.path}")
                continue
            
            if max_size > 0 and file_info.size > max_size:
                self.logger.debug(f"Виключено за максимальним розміром: {file_info.path}")
                continue
            
            filtered_files.append(file_info)
        
        # Фільтрація секвенцій
        filtered_sequences = []
        if filters.get('process_sequences', True):
            for sequence in self.sequences_to_process:
                # Перевірка розширення секвенції
                if sequence.extension.lower() in excluded_extensions:
                    self.logger.debug(f"Виключено секвенцію за розширенням: {sequence.name}")
                    continue
                
                filtered_sequences.append(sequence)
        
        # Оновлення списків
        removed_files = len(self.files_to_process) - len(filtered_files)
        removed_sequences = len(self.sequences_to_process) - len(filtered_sequences)
        
        self.files_to_process = filtered_files
        self.sequences_to_process = filtered_sequences
        
        self.logger.info(f"Фільтрація завершена. Виключено файлів: {removed_files}, "
                        f"секвенцій: {removed_sequences}")
        
        # Оновлення статистики
        self._update_stats()
    
    def execute_operation(self, operation: str, target_folder: str = "", 
                         dry_run: bool = True, progress_callback=None) -> Dict:
        """
        Виконання операції над файлами
        
        Args:
            operation: Тип операції ('delete' або 'move')
            target_folder: Цільова папка для переміщення
            dry_run: Режим попереднього перегляду
            progress_callback: Функція для оновлення прогресу
            
        Returns:
            Словник з результатами операції
        """
        results = {
            'success': True,
            'processed_files': 0,
            'processed_sequences': 0,
            'errors': [],
            'skipped': [],
            'total_size_processed': 0,
            'backup_list_path': None
        }
        
        try:
            self.logger.info(f"Початок операції: {operation} (dry_run: {dry_run})")
            
            # Створення резервного списку
            if not dry_run:
                backup_path = self._create_backup_list()
                results['backup_list_path'] = backup_path
            
            # Підготовка цільової папки для переміщення
            if operation == 'move' and target_folder and not dry_run:
                os.makedirs(target_folder, exist_ok=True)
            
            total_items = len(self.files_to_process) + len(self.sequences_to_process)
            processed_items = 0
            
            # Обробка окремих файлів
            for file_info in self.files_to_process:
                try:
                    if operation == 'delete':
                        success = self._delete_file(file_info, dry_run)
                    elif operation == 'move':
                        success = self._move_file(file_info, target_folder, dry_run)
                    else:
                        raise ValueError(f"Невідома операція: {operation}")
                    
                    if success:
                        results['processed_files'] += 1
                        results['total_size_processed'] += file_info.size
                    else:
                        results['skipped'].append(self._last_skip_reason or file_info.path)
                
                except Exception as e:
                    error_msg = f"Помилка обробки файлу {file_info.path}: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
                
                processed_items += 1
                if progress_callback:
                    progress = (processed_items / total_items) * 100
                    progress_callback(progress)
            
            # Обробка секвенцій
            for sequence in self.sequences_to_process:
                try:
                    # Розмір рахуємо ДО операції, поки кадри ще на місці
                    size = self.sequence_size(sequence)
                    if operation == 'delete':
                        success = self._delete_sequence(sequence, dry_run)
                    elif operation == 'move':
                        success = self._move_sequence(sequence, target_folder, dry_run)
                    else:
                        raise ValueError(f"Невідома операція: {operation}")
                    
                    if success:
                        results['processed_sequences'] += 1
                        results['total_size_processed'] += size
                    else:
                        results['skipped'].append(self._last_skip_reason or sequence.folder_path)
                
                except Exception as e:
                    error_msg = f"Помилка обробки секвенції {sequence.name}: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
                
                processed_items += 1
                if progress_callback:
                    progress = (processed_items / total_items) * 100
                    progress_callback(progress)
            
            # Оновлення статистики
            self.stats['processed_files'] = results['processed_files']
            self.stats['processed_sequences'] = results['processed_sequences']
            self.stats['errors'] = len(results['errors'])
            self.stats['skipped'] = len(results['skipped'])
            
            self.logger.info(f"Операція завершена. Оброблено файлів: {results['processed_files']}, "
                           f"секвенцій: {results['processed_sequences']}, "
                           f"помилок: {len(results['errors'])}")
            
        except Exception as e:
            self.logger.error(f"Критична помилка під час операції: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    def _create_backup_list(self) -> str:
        """Створення резервного списку файлів"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_list_{timestamp}.json"
        
        backup_data = {
            'timestamp': timestamp,
            'files': [f.path for f in self.files_to_process],
            'sequences': [
                {
                    'name': seq.name,
                    'folder_path': seq.folder_path,
                    'file_count': seq.file_count
                }
                for seq in self.sequences_to_process
            ],
            'stats': self.stats.copy()
        }
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Створено резервний список: {backup_filename}")
        return backup_filename
    
    def _skip(self, path: str, error) -> bool:
        """Запам'ятовує, чому пропущено, і пише в журнал. Повертає False для зручності"""
        reason = LOCKED_HINT if isinstance(error, Exception) and is_locked_error(error) else str(error)
        self._last_skip_reason = f"{path} -> {reason}"
        self.logger.warning(f"Пропущено: {self._last_skip_reason}")
        return False

    def _delete_file(self, file_info: FileInfo, dry_run: bool) -> bool:
        """Видалення файлу"""
        self._last_skip_reason = ""
        if dry_run:
            self.logger.info(f"[DRY RUN] Видалення файлу: {file_info.path}")
            return True
        
        try:
            os.remove(file_info.path)
            self.logger.info(f"Видалено файл: {file_info.path}")
            return True
        except Exception as e:
            return self._skip(file_info.path, e)

    @staticmethod
    def _unique_path(target_path: str) -> str:
        """file.ext -> file_1.ext -> file_2.ext ..., якщо такий файл уже є"""
        if not os.path.exists(target_path):
            return target_path
        base, ext = os.path.splitext(target_path)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        return f"{base}_{counter}{ext}"
    
    def _move_file(self, file_info: FileInfo, target_folder: str, dry_run: bool) -> bool:
        """Переміщення файлу"""
        self._last_skip_reason = ""
        if not target_folder:
            self.logger.error("Не вказано цільову папку для переміщення")
            return self._skip(file_info.path, "не вказано цільову папку")
        
        target_path = os.path.join(target_folder, file_info.name)
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Переміщення файлу: {file_info.path} -> {target_path}")
            return True
        
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            target_path = self._unique_path(target_path)
            shutil.move(file_info.path, target_path)
            self.logger.info(f"Переміщено файл: {file_info.path} -> {target_path}")
            return True
        except Exception as e:
            return self._skip(file_info.path, e)

    def _sequence_members(self, sequence: SequenceInfo) -> List[str]:
        """Кадри секвенції та її допоміжні файли - і нічого більше з тієї папки"""
        frames = self.sequence_parser.get_sequence_files(sequence)
        auxiliary = self.sequence_parser.get_auxiliary_files(sequence)
        return frames + [a for a in auxiliary if a not in frames]

    def sequence_size(self, sequence: SequenceInfo) -> int:
        """Розмір кадрів секвенції в байтах"""
        size = 0
        for path in self.sequence_parser.get_sequence_files(sequence):
            try:
                size += os.path.getsize(path)
            except OSError:
                pass
        return size

    @staticmethod
    def _remove_item(path: str) -> None:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    def _remove_dir_if_empty(self, folder: str) -> bool:
        """Видаляє папку, лише якщо в ній не лишилося нічого, крім службових файлів"""
        try:
            items = os.listdir(folder)
        except OSError:
            return False
        if any(name.lower() not in JUNK_FILE_NAMES for name in items):
            return False
        try:
            for name in items:
                os.remove(os.path.join(folder, name))
            os.rmdir(folder)
            self.logger.info(f"Видалено порожню папку: {folder}")
            return True
        except OSError as e:
            self.logger.warning(f"Не вдалося видалити порожню папку {folder}: {e}")
            return False

    def _delete_sequence(self, sequence: SequenceInfo, dry_run: bool) -> bool:
        """
        Видаляє кадри секвенції та її допоміжні файли.
        Інші файли в папці не чіпаються; сама папка видаляється, лише якщо стала порожньою.
        """
        self._last_skip_reason = ""
        folder_path = Path(sequence.folder_path)
        members = self._sequence_members(sequence)
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Видалення {len(members)} файлів секвенції: {folder_path}")
            return True
        
        if not folder_path.exists():
            return self._skip(str(folder_path), "папка секвенції не існує")
        if not members:
            return self._skip(str(folder_path), "у папці не знайдено кадрів секвенції")

        failed = None
        for path in members:
            try:
                self._remove_item(path)
            except Exception as e:
                failed = failed or e
        self._remove_dir_if_empty(str(folder_path))
        if failed:
            return self._skip(str(folder_path), failed)
        self.logger.info(f"Видалено {len(members)} файлів секвенції: {folder_path}")
        return True
    
    def _move_sequence(self, sequence: SequenceInfo, target_folder: str, dry_run: bool) -> bool:
        """Переміщує кадри секвенції у <цільова папка>/<назва папки секвенції>"""
        self._last_skip_reason = ""
        if not target_folder:
            self.logger.error("Не вказано цільову папку для переміщення")
            return self._skip(sequence.folder_path, "не вказано цільову папку")
        
        source_folder = Path(sequence.folder_path)
        dest_sequence_folder = Path(target_folder) / source_folder.name
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Переміщення секвенції: {source_folder} -> {dest_sequence_folder}")
            return True
        
        if not source_folder.exists():
            return self._skip(str(source_folder), "папка секвенції не існує")
        members = self._sequence_members(sequence)
        if not members:
            return self._skip(str(source_folder), "у папці не знайдено кадрів секвенції")

        failed = None
        try:
            dest_sequence_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return self._skip(str(source_folder), e)
        for path in members:
            try:
                shutil.move(path, self._unique_path(str(dest_sequence_folder / Path(path).name)))
            except Exception as e:
                failed = failed or e
        self._remove_dir_if_empty(str(source_folder))
        if failed:
            return self._skip(str(source_folder), failed)
        self.logger.info(f"Переміщено секвенцію: {source_folder} -> {dest_sequence_folder}")
        return True
    
    def get_summary(self) -> Dict:
        """Отримання підсумкової інформації"""
        total_size_mb = self.stats['total_size'] / (1024 * 1024)
        
        return {
            'total_files': self.stats['total_files'],
            'total_sequences': self.stats['total_sequences'],
            'total_size_mb': round(total_size_mb, 2),
            'missing_files': len(self.missing_files),
            'processed_files': self.stats.get('processed_files', 0),
            'processed_sequences': self.stats.get('processed_sequences', 0),
            'errors': self.stats.get('errors', 0),
            'skipped': self.stats.get('skipped', 0)
        }