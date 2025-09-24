#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
After Effects Report Generator
Модуль для генерації звітів про операції очистки
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class AEReportGenerator:
    """Генератор звітів для операцій очистки After Effects"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_operation_report(self, operation_data: Dict, 
                                summary_data: Dict, 
                                operation_type: str,
                                dry_run: bool = False) -> str:
        """
        Генерація звіту про операцію
        
        Args:
            operation_data: Дані про виконану операцію
            summary_data: Підсумкові дані
            operation_type: Тип операції (delete/move)
            dry_run: Чи був це тестовий запуск
            
        Returns:
            Шлях до створеного звіту
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_type = "dry_run" if dry_run else "actual"
        filename = f"ae_cleanup_{operation_type}_{report_type}_{timestamp}.html"
        report_path = os.path.join(self.output_dir, filename)
        
        # Генерація HTML звіту
        html_content = self._generate_html_report(
            operation_data, summary_data, operation_type, dry_run, timestamp
        )
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Також створюємо JSON версію для програмної обробки
        json_filename = filename.replace('.html', '.json')
        json_path = os.path.join(self.output_dir, json_filename)
        
        json_data = {
            'timestamp': timestamp,
            'operation_type': operation_type,
            'dry_run': dry_run,
            'operation_data': operation_data,
            'summary_data': summary_data
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return report_path
    
    def _generate_html_report(self, operation_data: Dict, 
                            summary_data: Dict, 
                            operation_type: str,
                            dry_run: bool, 
                            timestamp: str) -> str:
        """Генерація HTML звіту"""
        
        # Визначення кольорів та іконок
        operation_color = "#e74c3c" if operation_type == "delete" else "#3498db"
        operation_icon = "🗑️" if operation_type == "delete" else "📁"
        operation_text = "Видалення" if operation_type == "delete" else "Переміщення"
        
        status_text = "Тестовий запуск" if dry_run else "Виконано"
        status_color = "#f39c12" if dry_run else "#27ae60"
        
        # Форматування розміру
        def format_size(size_bytes):
            if size_bytes == 0:
                return "0 B"
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        
        html = f"""
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Звіт про очистку After Effects - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, {operation_color}, {operation_color}dd);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header .subtitle {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .status-badge {{
            display: inline-block;
            background: {status_color};
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 15px;
        }}
        .content {{
            padding: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            border-left: 4px solid {operation_color};
            padding: 20px;
            border-radius: 5px;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: {operation_color};
            font-size: 1.1em;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: {operation_color};
            border-bottom: 2px solid {operation_color};
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .file-list {{
            background: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
        }}
        .file-item {{
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .file-item:last-child {{
            border-bottom: none;
        }}
        .error-item {{
            color: #e74c3c;
            background: #fdf2f2;
            padding: 10px;
            border-radius: 3px;
            margin: 5px 0;
        }}
        .success-summary {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .warning-summary {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}
        .progress-bar {{
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            height: 20px;
            margin: 10px 0;
        }}
        .progress-fill {{
            background: {operation_color};
            height: 100%;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{operation_icon} {operation_text} файлів After Effects</h1>
            <div class="subtitle">Звіт створено: {datetime.now().strftime('%d.%m.%Y о %H:%M:%S')}</div>
            <div class="status-badge">{status_text}</div>
        </div>
        
        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📄 Оброблено файлів</h3>
                    <div class="value">{operation_data.get('processed_files', 0)}</div>
                </div>
                <div class="stat-card">
                    <h3>🎬 Оброблено секвенцій</h3>
                    <div class="value">{operation_data.get('processed_sequences', 0)}</div>
                </div>
                <div class="stat-card">
                    <h3>💾 Розмір даних</h3>
                    <div class="value">{format_size(operation_data.get('total_size_processed', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>❌ Помилки</h3>
                    <div class="value">{len(operation_data.get('errors', []))}</div>
                </div>
            </div>
        """
        
        # Додаємо підсумок операції
        total_items = summary_data.get('total_files', 0) + summary_data.get('total_sequences', 0)
        processed_items = operation_data.get('processed_files', 0) + operation_data.get('processed_sequences', 0)
        
        if total_items > 0:
            success_rate = (processed_items / total_items) * 100
            
            if success_rate >= 90:
                summary_class = "success-summary"
                summary_icon = "✅"
                summary_title = "Операція виконана успішно"
            elif success_rate >= 70:
                summary_class = "warning-summary"
                summary_icon = "⚠️"
                summary_title = "Операція виконана з попередженнями"
            else:
                summary_class = "error-item"
                summary_icon = "❌"
                summary_title = "Операція виконана з помилками"
            
            html += f"""
            <div class="{summary_class}">
                <h3>{summary_icon} {summary_title}</h3>
                <p>Успішно оброблено {processed_items} з {total_items} елементів ({success_rate:.1f}%)</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {success_rate}%"></div>
                </div>
            </div>
            """
        
        # Додаємо детальну інформацію про помилки
        if operation_data.get('errors'):
            html += f"""
            <div class="section">
                <h2>❌ Помилки під час виконання</h2>
                <div class="file-list">
            """
            for error in operation_data['errors']:
                html += f'<div class="error-item">{error}</div>'
            html += "</div></div>"
        
        # Додаємо інформацію про пропущені файли
        if operation_data.get('skipped'):
            html += f"""
            <div class="section">
                <h2>⏭️ Пропущені файли</h2>
                <div class="file-list">
            """
            for skipped in operation_data['skipped']:
                html += f'<div class="file-item">{skipped}</div>'
            html += "</div></div>"
        
        # Додаємо загальну статистику
        html += f"""
            <div class="section">
                <h2>📊 Загальна статистика</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>📁 Всього файлів знайдено</h3>
                        <div class="value">{summary_data.get('total_files', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <h3>🎬 Всього секвенцій знайдено</h3>
                        <div class="value">{summary_data.get('total_sequences', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <h3>💾 Загальний розмір</h3>
                        <div class="value">{format_size(summary_data.get('total_size_mb', 0) * 1024 * 1024)}</div>
                    </div>
                    <div class="stat-card">
                        <h3>❓ Відсутні файли</h3>
                        <div class="value">{summary_data.get('missing_files', 0)}</div>
                    </div>
                </div>
            </div>
        """
        
        # Додаємо інформацію про резервну копію
        if operation_data.get('backup_list_path') and not dry_run:
            html += f"""
            <div class="section">
                <h2>💾 Резервна копія</h2>
                <div class="success-summary">
                    <p><strong>Створено резервний список файлів:</strong></p>
                    <p style="font-family: 'Courier New', monospace;">{operation_data['backup_list_path']}</p>
                    <p><small>Цей файл містить список всіх оброблених файлів та може бути використаний для відновлення.</small></p>
                </div>
            </div>
            """
        
        html += """
        </div>
        
        <div class="footer">
            <p>Звіт згенеровано автоматично системою очистки After Effects</p>
            <p><small>Для питань та підтримки зверніться до адміністратора системи</small></p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def generate_disk_usage_report(self, paths: List[str]) -> Dict:
        """
        Генерація звіту про використання дискового простору
        
        Args:
            paths: Список шляхів для аналізу
            
        Returns:
            Словник з інформацією про використання диска
        """
        disk_info = {}
        
        for path in paths:
            try:
                if os.path.exists(path):
                    # Отримуємо інформацію про диск
                    statvfs = os.statvfs(path) if hasattr(os, 'statvfs') else None
                    
                    if statvfs:
                        # Unix/Linux
                        total = statvfs.f_frsize * statvfs.f_blocks
                        free = statvfs.f_frsize * statvfs.f_available
                        used = total - free
                    else:
                        # Windows
                        import shutil
                        total, used, free = shutil.disk_usage(path)
                    
                    disk_info[path] = {
                        'total_gb': round(total / (1024**3), 2),
                        'used_gb': round(used / (1024**3), 2),
                        'free_gb': round(free / (1024**3), 2),
                        'usage_percent': round((used / total) * 100, 1)
                    }
                    
            except Exception as e:
                disk_info[path] = {'error': str(e)}
        
        return disk_info
    
    def list_recent_reports(self, limit: int = 10) -> List[Dict]:
        """
        Отримання списку останніх звітів
        
        Args:
            limit: Максимальна кількість звітів
            
        Returns:
            Список словників з інформацією про звіти
        """
        reports = []
        
        try:
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.json') and 'ae_cleanup_' in filename:
                    filepath = os.path.join(self.output_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        reports.append({
                            'filename': filename,
                            'filepath': filepath,
                            'timestamp': data.get('timestamp', ''),
                            'operation_type': data.get('operation_type', ''),
                            'dry_run': data.get('dry_run', False),
                            'processed_files': data.get('operation_data', {}).get('processed_files', 0),
                            'processed_sequences': data.get('operation_data', {}).get('processed_sequences', 0),
                            'errors': len(data.get('operation_data', {}).get('errors', [])),
                            'file_size': os.path.getsize(filepath)
                        })
                        
                    except Exception:
                        continue
            
            # Сортуємо за часом створення
            reports.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return reports[:limit]
            
        except Exception:
            return []