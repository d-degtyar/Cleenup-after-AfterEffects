#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
After Effects Sequence Parser Module
Модуль для інтелектуальної обробки секвенцій файлів
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, NamedTuple

class SequenceInfo(NamedTuple):
    """Інформація про секвенцію файлів"""
    name: str
    pattern: str
    folder_path: str
    file_count: int
    auxiliary_count: int
    start_frame: int
    end_frame: int
    extension: str
    full_pattern: str

class FileSequenceParser:
    """Парсер для обробки секвенцій файлів After Effects"""
    
    def __init__(self):
        # Регулярні вирази для різних форматів секвенцій
        self.sequence_patterns = [
            # Формат: Sequence "name_[00000-00447].ext" at path with X files and Y auxiliary files
            r'Sequence\s+"([^"]+)"\s+at\s+(.+?)\s+with\s+(\d+)\s+files\s+and\s+(\d+)\s+auxiliary\s+files',
            
            # Формат: Sequence "[00-30].png" at path with X files and Y auxiliary files  
            r'Sequence\s+"([^"]+)"\s+at\s+(.+?)\s+with\s+(\d+)\s+files\s+and\s+(\d+)\s+auxiliary\s+files',
            
            # Загальний формат для секвенцій
            r'Sequence\s+"?([^"]+)"?\s+at\s+(.+?)\s+with\s+(\d+)\s+files\s+and\s+(\d+)\s+auxiliary\s+files'
        ]
        
        # Шаблони для розпізнавання масок кадрів
        self.frame_patterns = [
            r'\[(\d+)-(\d+)\]',           # [00-30], [000-323]
            r'\[(\d+)-(\d+)\]\.(\w+)',    # [00-30].png
            r'_\[(\d+)-(\d+)\]',          # _[00000-00447]
            r'\[(\d{5})-(\d{5})\]',       # [00000-00447]
            r'\[(\d{3})-(\d{3})\]',       # [000-323]
            r'\[(\d{2})-(\d{2})\]',       # [00-30]
            r'\[(\d{4})-(\d{4})\]',       # [0001-0017]
        ]
    
    def parse_sequence_line(self, line: str) -> Optional[SequenceInfo]:
        """
        Парсинг рядка з інформацією про секвенцію
        
        Args:
            line: Рядок з файлу звіту
            
        Returns:
            SequenceInfo або None якщо рядок не є секвенцією
        """
        line = line.strip()
        
        # Перевіряємо чи це рядок з секвенцією
        if not line.startswith('Sequence'):
            return None
        
        # Пробуємо різні шаблони
        for pattern in self.sequence_patterns:
            match = re.search(pattern, line)
            if match:
                return self._extract_sequence_info(match, line)
        
        return None
    
    def _extract_sequence_info(self, match, original_line: str) -> SequenceInfo:
        """Витягування інформації про секвенцію з regex match"""
        sequence_name = match.group(1)
        folder_path = match.group(2).strip()
        file_count = int(match.group(3))
        auxiliary_count = int(match.group(4))
        
        # Аналіз маски кадрів
        start_frame, end_frame, extension = self._parse_frame_pattern(sequence_name)
        
        # Очищення шляху від зайвих символів
        folder_path = self._clean_folder_path(folder_path)
        
        return SequenceInfo(
            name=sequence_name,
            pattern=self._extract_pattern(sequence_name),
            folder_path=folder_path,
            file_count=file_count,
            auxiliary_count=auxiliary_count,
            start_frame=start_frame,
            end_frame=end_frame,
            extension=extension,
            full_pattern=sequence_name
        )
    
    def _parse_frame_pattern(self, sequence_name: str) -> Tuple[int, int, str]:
        """Парсинг маски кадрів для визначення діапазону та розширення"""
        start_frame = 0
        end_frame = 0
        extension = ""
        
        # Витягування розширення
        ext_match = re.search(r'\.(\w+)$', sequence_name)
        if ext_match:
            extension = ext_match.group(1)
        
        # Пошук діапазону кадрів
        for pattern in self.frame_patterns:
            match = re.search(pattern, sequence_name)
            if match:
                start_frame = int(match.group(1))
                end_frame = int(match.group(2))
                break
        
        return start_frame, end_frame, extension
    
    def _extract_pattern(self, sequence_name: str) -> str:
        """Витягування базового шаблону без діапазону кадрів"""
        # Замінюємо маску кадрів на загальний шаблон
        pattern = sequence_name
        for frame_pattern in self.frame_patterns:
            pattern = re.sub(frame_pattern, '[####]', pattern)
        return pattern
    
    def _clean_folder_path(self, folder_path: str) -> str:
        """Очищення шляху папки від зайвих символів"""
        # Видаляємо зайві символи та пробіли
        cleaned = folder_path.strip()
        
        # Видаляємо можливі артефакти з кінця шляху
        if cleaned.endswith('$$Footage)'):
            cleaned = cleaned.replace('$$Footage)', '')
        
        return cleaned
    
    def get_sequence_files(self, sequence_info: SequenceInfo) -> List[str]:
        """
        Отримання списку всіх файлів секвенції
        
        Args:
            sequence_info: Інформація про секвенцію
            
        Returns:
            Список шляхів до файлів секвенції
        """
        files = []
        folder_path = Path(sequence_info.folder_path)
        
        if not folder_path.exists():
            return files
        
        # Генерація імен файлів на основі маски
        if sequence_info.start_frame is not None and sequence_info.end_frame is not None:
            base_name = self._get_base_filename(sequence_info.name)
            
            for frame_num in range(sequence_info.start_frame, sequence_info.end_frame + 1):
                # Визначення формату номера кадру
                frame_format = self._get_frame_format(sequence_info.name, frame_num)
                filename = base_name.replace('[####]', frame_format)
                
                file_path = folder_path / filename
                if file_path.exists():
                    files.append(str(file_path))
        
        return files
    
    def _get_base_filename(self, sequence_name: str) -> str:
        """Отримання базового імені файлу з маскою"""
        # Замінюємо конкретний діапазон на загальну маску
        base_name = sequence_name
        for pattern in self.frame_patterns:
            base_name = re.sub(pattern, '[####]', base_name)
        return base_name
    
    def _get_frame_format(self, sequence_name: str, frame_num: int) -> str:
        """Визначення формату номера кадру"""
        # Аналізуємо оригінальний формат номерування
        for pattern in self.frame_patterns:
            match = re.search(pattern, sequence_name)
            if match:
                start_str = match.group(1)
                # Визначаємо кількість цифр для форматування
                padding = len(start_str)
                return str(frame_num).zfill(padding)
        
        return str(frame_num)
    
    def get_auxiliary_files(self, sequence_info: SequenceInfo) -> List[str]:
        """
        Отримання списку допоміжних файлів секвенції
        
        Args:
            sequence_info: Інформація про секвенцію
            
        Returns:
            Список шляхів до допоміжних файлів
        """
        auxiliary_files = []
        folder_path = Path(sequence_info.folder_path)
        
        if not folder_path.exists():
            return auxiliary_files
        
        # Типові допоміжні файли та папки
        auxiliary_patterns = [
            '@eaDir',
            '.DS_Store',
            'Thumbs.db',
            'desktop.ini',
            '.metadata',
            '.cache',
            '*.tmp',
            '*.temp'
        ]
        
        for item in folder_path.iterdir():
            for pattern in auxiliary_patterns:
                if pattern.startswith('.') and item.name == pattern:
                    auxiliary_files.append(str(item))
                elif pattern.startswith('@') and item.name.startswith(pattern):
                    auxiliary_files.append(str(item))
                elif '*' in pattern:
                    import fnmatch
                    if fnmatch.fnmatch(item.name, pattern):
                        auxiliary_files.append(str(item))
        
        return auxiliary_files
    
    def validate_sequence(self, sequence_info: SequenceInfo) -> Dict[str, any]:
        """
        Валідація секвенції файлів
        
        Args:
            sequence_info: Інформація про секвенцію
            
        Returns:
            Словник з результатами валідації
        """
        result = {
            'valid': True,
            'folder_exists': False,
            'files_found': 0,
            'files_missing': 0,
            'auxiliary_found': 0,
            'total_size': 0,
            'errors': []
        }
        
        folder_path = Path(sequence_info.folder_path)
        
        # Перевірка існування папки
        if not folder_path.exists():
            result['valid'] = False
            result['errors'].append(f"Папка не існує: {folder_path}")
            return result
        
        result['folder_exists'] = True
        
        # Перевірка файлів секвенції
        sequence_files = self.get_sequence_files(sequence_info)
        result['files_found'] = len(sequence_files)
        
        expected_files = sequence_info.end_frame - sequence_info.start_frame + 1
        result['files_missing'] = max(0, expected_files - result['files_found'])
        
        # Підрахунок розміру
        total_size = 0
        for file_path in sequence_files:
            try:
                total_size += os.path.getsize(file_path)
            except OSError:
                result['errors'].append(f"Не вдалося отримати розмір файлу: {file_path}")
        
        result['total_size'] = total_size
        
        # Перевірка допоміжних файлів
        auxiliary_files = self.get_auxiliary_files(sequence_info)
        result['auxiliary_found'] = len(auxiliary_files)
        
        # Валідація відповідності кількості файлів
        if result['files_found'] != sequence_info.file_count:
            result['errors'].append(
                f"Невідповідність кількості файлів: знайдено {result['files_found']}, "
                f"очікувалося {sequence_info.file_count}"
            )
        
        if result['auxiliary_found'] != sequence_info.auxiliary_count:
            result['errors'].append(
                f"Невідповідність кількості допоміжних файлів: знайдено {result['auxiliary_found']}, "
                f"очікувалося {sequence_info.auxiliary_count}"
            )
        
        return result
    
    def get_sequence_summary(self, sequence_info: SequenceInfo) -> str:
        """Отримання короткого опису секвенції"""
        validation = self.validate_sequence(sequence_info)
        
        size_mb = validation['total_size'] / (1024 * 1024) if validation['total_size'] > 0 else 0
        
        summary = f"""
Секвенція: {sequence_info.name}
Папка: {sequence_info.folder_path}
Кадри: {sequence_info.start_frame}-{sequence_info.end_frame} ({sequence_info.file_count} файлів)
Розмір: {size_mb:.2f} MB
Статус: {'✓ Валідна' if validation['valid'] else '✗ Помилки'}
"""
        
        if validation['errors']:
            summary += f"Помилки: {'; '.join(validation['errors'])}"
        
        return summary.strip()

# Тестування модуля
if __name__ == "__main__":
    parser = FileSequenceParser()
    
    # Тестові рядки
    test_lines = [
        'Sequence "Final Comp Full HD_couldown_[00000-00447].png" at C:\\Users\\HOME_Diomas\\Downloads\\2025-08_Personal_Хто Ми Є (Lyric Video) folder\\Final Comp Full HD_couldown with 448 files and 0 auxiliary files',
        'Sequence "[00-30].png" at E:\\2025\\Work2025\\AMM\\КвіткаVideo_upd folder\\(Footage)\\Footage\\png\\Cards_03updJ2K with 31 files and 0 auxiliary files',
        'Sequence "frame_[00001-00053].png" at E:\\2025\\Work2025\\AMM\\КвіткаVideo_upd folder\\(Footage)\\Footage\\png\\Cruch with 53 files and 0 auxiliary files'
    ]
    
    for line in test_lines:
        sequence = parser.parse_sequence_line(line)
        if sequence:
            print(f"Знайдено секвенцію: {sequence.name}")
            print(f"Папка: {sequence.folder_path}")
            print(f"Кадри: {sequence.start_frame}-{sequence.end_frame}")
            print(f"Розширення: {sequence.extension}")
            print("-" * 50)