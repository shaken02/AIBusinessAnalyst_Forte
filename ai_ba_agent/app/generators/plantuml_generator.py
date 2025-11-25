"""PlantUML generator."""

from __future__ import annotations

import re

from app.core.llm_engine import LLMEngine
from app.utils.logger import logger


def generate_plantuml(context: str, engine: LLMEngine) -> str:
    diagram = engine.generate_plantuml(context)
    logger.debug("Raw PlantUML from LLM (first 500 chars): %s", diagram[:500])
    
    # Clean PlantUML code from LLM output
    diagram = diagram.strip()
    
    # Remove markdown code blocks if present
    if '```' in diagram:
        lines = diagram.split('\n')
        diagram = '\n'.join([line for line in lines if not line.strip().startswith('```')])
        diagram = diagram.strip()
    
    # Extract only PlantUML code between @startuml and @enduml
    if '@startuml' in diagram:
        start_idx = diagram.find('@startuml')
        diagram = diagram[start_idx:]
    
    # Исправляем опечатку @endum -> @enduml
    diagram = diagram.replace('@endum', '@enduml')
    
    if '@enduml' in diagram:
        end_idx = diagram.find('@enduml') + len('@enduml')
        diagram = diagram[:end_idx]
    
    # Guarantee @startuml/@enduml are present
    if "@startuml" not in diagram:
        diagram = f"@startuml\n{diagram.strip()}\n@enduml"
    if not diagram.endswith('@enduml'):
        diagram = f"{diagram}\n@enduml"
    
    # Remove any text after @enduml
    if '@enduml' in diagram:
        diagram = diagram[:diagram.rfind('@enduml') + len('@enduml')]
    
    diagram = diagram.strip()
    
    # КРИТИЧЕСКИ ВАЖНО: Удаляем markdown-элементы из PlantUML кода
    # LLM иногда генерирует markdown-заголовки (##, ###) и списки (-) вместо PlantUML
    lines = diagram.split('\n')
    cleaned_lines = []
    inside_plantuml = False
    
    for line in lines:
        stripped = line.strip()
        
        # Отслеживаем начало PlantUML
        if stripped.startswith('@startuml'):
            inside_plantuml = True
            cleaned_lines.append(line)
            continue
        
        if stripped.startswith('@enduml'):
            cleaned_lines.append(line)
            inside_plantuml = False
            continue
        
        # Если мы внутри PlantUML блока, фильтруем markdown
        if inside_plantuml:
            # Удаляем только явные markdown-заголовки (##, ###, #)
            if stripped.startswith('##') or stripped.startswith('###') or (stripped.startswith('# ') and not stripped.startswith('#@')):
                continue
            # Удаляем только markdown-списки, которые явно являются markdown (начинаются с "- " или "* ")
            # НЕ удаляем строки, которые могут быть PlantUML синтаксисом
            if (stripped.startswith('- ') or stripped.startswith('* ')) and not any(kw in stripped for kw in [':', 'start', 'stop', 'if', 'else', 'endif', 'fork', 'endfork', 'note']):
                continue
        
        # Сохраняем все остальное - лучше сохранить лишнее, чем удалить нужное
        cleaned_lines.append(line)
    
    diagram = '\n'.join(cleaned_lines)
    
    # Try to fix common syntax errors with proper structure validation
    lines = diagram.split('\n')
    fixed_lines = []
    
    # Track structure for validation
    structure_stack = []  # Stack of (type, line_idx) where type is 'if' or 'fork'
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Пропускаем пустые строки, но добавляем их в финальную версию для читаемости
        if not stripped:
            fixed_lines.append('')
            i += 1
            continue
        
        # Комментарии и note сохраняем
        if stripped.startswith('//') or stripped.startswith('note'):
            fixed_lines.append(line)
            i += 1
            continue
        
        # КРИТИЧЕСКИ ВАЖНО: Исправляем неправильный синтаксис с ->
        if '->' in stripped or '- >' in stripped:
            # Если это действие с условием внутри, исправляем
            if stripped.startswith(':') and ('Если' in stripped or 'если' in stripped):
                # Пример: ":Если 80% вопросов верны - :Выдает сертификат;"
                match = re.search(r':(?:Если|если)\s+(.+?)\s*[-=]>\s*:?(.+)', stripped)
                if match:
                    condition = match.group(1).strip().rstrip(';')
                    action = match.group(2).strip().rstrip(';')
                    # Создаем правильную структуру
                    fixed_lines.append(f"if ({condition}?) then (Да)")
                    structure_stack.append(('if', len(fixed_lines) - 1))
                    fixed_lines.append(f"  :{action};")
                    fixed_lines.append("else (Нет)")
                    fixed_lines.append("  :Действие не выполнено;")
                    fixed_lines.append("endif")
                    if structure_stack:
                        structure_stack.pop()
                    i += 1
                    continue
            # Разбиваем действия с ->
            if stripped.startswith(':'):
                parts = re.split(r'\s*[-=]>\s*', stripped)
                for part in parts:
                    part = part.strip()
                    if part and not part.lower().startswith('stop'):
                        if not part.startswith(':'):
                            part = ':' + part
                        part = part.rstrip(';').rstrip(',')
                        if not part.endswith(';'):
                            part += ';'
                        fixed_lines.append(part)
                i += 1
                continue
            else:
                # Просто убираем ->
                line = re.sub(r'\s*[-=]>\s*', ' ', line)
                stripped = line.strip()
        
        # Обработка if/else/endif структуры
        if stripped.startswith('if '):
            fixed_lines.append(line)
            structure_stack.append(('if', len(fixed_lines) - 1))
            i += 1
            continue
        elif stripped.startswith('else'):
            # Проверяем, есть ли незакрытые fork перед else
            # Если есть fork в стеке, сначала закрываем их
            while structure_stack and structure_stack[-1][0] == 'fork':
                fixed_lines.append('endfork')
                structure_stack.pop()
            # Теперь добавляем else для if
            if structure_stack and structure_stack[-1][0] == 'if':
                fixed_lines.append(line)
            else:
                # Если нет соответствующего if, пропускаем или создаем новый if
                fixed_lines.append(f"if (Условие?) then (Да)")
                fixed_lines.append("  :Действие;")
                fixed_lines.append(line)
                structure_stack.append(('if', len(fixed_lines) - 3))
            i += 1
            continue
        elif stripped.startswith('endif'):
            # Закрываем все fork перед endif
            while structure_stack and structure_stack[-1][0] == 'fork':
                fixed_lines.append('endfork')
                structure_stack.pop()
            # Теперь закрываем if
            if structure_stack and structure_stack[-1][0] == 'if':
                fixed_lines.append(line)
                structure_stack.pop()
            i += 1
            continue
        
        # Обработка fork/endfork структуры
        if stripped.startswith('fork'):
            fixed_lines.append(line)
            structure_stack.append(('fork', len(fixed_lines) - 1))
            i += 1
            continue
        elif stripped.startswith('endfork'):
            if structure_stack and structure_stack[-1][0] == 'fork':
                fixed_lines.append(line)
                structure_stack.pop()
            i += 1
            continue
        
        # КРИТИЧЕСКИ ВАЖНО: Добавляем точку с запятой в конце действий
        if stripped.startswith(':') and not stripped.endswith(';'):
            if not any(kw in stripped for kw in ['@startuml', '@enduml', 'start', 'stop']):
                if stripped.endswith(','):
                    line = line.rstrip(',') + ';'
                else:
                    line = line.rstrip() + ';'
        
        # Исправляем ":Действие -> stop"
        if stripped.startswith(':') and 'stop' in stripped.lower():
            action_part = stripped.split('stop')[0].strip().rstrip(';').rstrip(',').rstrip('->').rstrip('- >')
            if action_part.startswith(':'):
                if not action_part.endswith(';'):
                    action_part += ';'
                fixed_lines.append(action_part)
            fixed_lines.append('stop')
            i += 1
            continue
        
        # Удаляем sequence diagram синтаксис (только явные sequence команды)
        if any(kw in stripped.lower() for kw in ['participant ', 'activate ', 'deactivate ', 'note right of', '->>']):
            i += 1
            continue
        
        # Сохраняем все остальное - лучше сохранить лишнее
        fixed_lines.append(line)
        i += 1
    
    # Закрываем все незакрытые блоки перед stop/enduml
    while structure_stack:
        block_type, _ = structure_stack.pop()
        if block_type == 'fork':
            fixed_lines.append('endfork')
        elif block_type == 'if':
            fixed_lines.append('endif')
    
    diagram = '\n'.join(fixed_lines)
    
    # Ensure we have valid activity diagram structure
    if 'start' not in diagram:
        # Try to add start if missing
        if '@startuml' in diagram:
            diagram = diagram.replace('@startuml', '@startuml\nstart', 1)
    
    if 'stop' not in diagram and '@enduml' in diagram:
        # Try to add stop before @enduml
        diagram = diagram.replace('@enduml', 'stop\n@enduml', 1)
    
    # Логируем финальный результат для отладки
    logger.debug("Final PlantUML diagram (first 1000 chars):\n%s", diagram[:1000])
    
    # Проверяем, что диаграмма не пустая (только start и stop)
    lines_between = [l.strip() for l in diagram.split('\n') if l.strip() and not l.strip().startswith('@') and l.strip() not in ['start', 'stop']]
    if not lines_between:
        logger.warning("PlantUML diagram appears to be empty - only start/stop found")
    
    return diagram.strip()


__all__ = ["generate_plantuml"]
