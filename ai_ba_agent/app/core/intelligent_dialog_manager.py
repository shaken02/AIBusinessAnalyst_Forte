"""Intelligent dialog manager that uses LLM to understand context and extract information."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List

from app.core.llm_engine import LLMEngine
from app.utils.logger import logger
from app.utils.state import (
    ConversationState,
    FIELD_METADATA,
    FIELD_SEQUENCE,
    field_label,
)


@dataclass
class DialogAnalysis:
    """Result of analyzing user message."""
    extracted_info: Dict[str, str]
    missing_fields: List[str]
    next_question: str
    confidence: float
    interpretation_options: Dict[str, List[str]]  # Field -> list of 3 interpretation options


CONTEXT_UNDERSTANDING_PROMPT = """Ты — опытный бизнес-аналитик, который собирает требования через диалог.

Твоя задача — анализировать сообщения пользователя и извлекать информацию для Business Requirements Document (BRD).

Доступные поля для заполнения:
{field_descriptions}

Текущее состояние заполнения:
{current_state}

История диалога (последние сообщения):
{conversation_history}
{last_question_context}

Новое сообщение пользователя:
{user_message}

Проанализируй сообщение и выполни следующие задачи:

1. Определи, какую информацию пользователь предоставил
2. Извлеки эту информацию и сопоставь с соответствующими полями из списка выше
3. Для ПЕРВОГО (самого приоритетного) извлеченного поля предложи 3 варианта УТОЧНЕНИЯ/РАСШИРЕНИЯ мысли пользователя - как можно логически развить и дополнить то, что он сказал. ВАЖНО: предлагай варианты ТОЛЬКО для ОДНОГО поля за раз, не для всех сразу!
4. Определи, какие поля еще не заполнены
5. Сформулируй естественный, дружелюбный вопрос о следующем незаполненном поле

КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА ИЗВЛЕЧЕНИЯ ИНФОРМАЦИИ:
1. **КОНТЕКСТ ПОСЛЕДНЕГО ВОПРОСА**: Если в истории диалога последнее сообщение от аналитика содержит вопрос про конкретное поле (например, "Какова ключевая цель инициативы?"), то ответ пользователя относится ТОЛЬКО к этому полю. НЕ пытайся извлечь информацию для других полей!

2. **ПРИОРИТЕТ КОНТЕКСТА**: 
   - Если бот задал вопрос про поле "goal" (Цель), а пользователь ответил - заполняй ТОЛЬКО поле "goal", даже если в ответе есть слова, которые можно отнести к другим полям
   - НЕ дроби ответ пользователя на части и не записывай их в разные поля
   - Если пользователь явно упомянул несколько полей в одном сообщении - тогда извлеки все
   - Если пользователь отвечает на конкретный вопрос - извлекай ТОЛЬКО для этого поля

3. **ПРАВИЛО ОДНОГО ПОЛЯ**: Когда пользователь отвечает на конкретный вопрос бота, его ответ относится к ОДНОМУ полю. Не пытайся "умно" разделить ответ на части для разных полей - это ошибка!

4. **ОБЩИЕ ПРАВИЛА**:
   - Если пользователь уточняет ранее предоставленную информацию — обнови соответствующее поле
   - Если пользователь спрашивает о состоянии заполнения (например: "какие поля не заполнены?", "что еще нужно?", "что осталось?") — ответь естественно, перечисли незаполненные поля, а затем мягко спроси о следующем
   - Будь естественным в общении, не используй формальные фразы
   - Если все поля заполнены, поздрави пользователя и предложи сформировать документы
   - ВАЖНО: В missing_fields включай ТОЛЬКО поля, которые реально не заполнены (проверь current_state - там указано "не заполнено" для незаполненных полей)

Верни ответ ТОЛЬКО в формате JSON (без дополнительного текста):
{{
    "extracted_info": {{
        "goal": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "problem": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "description": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "stakeholders": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "roles": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "scope": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "out_of_scope": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "kpi": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "business_rules": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "constraints": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "risks": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "assumptions": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "nfr": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле",
        "process_description": "извлеченная информация ТОЛЬКО если она есть в сообщении, иначе НЕ ВКЛЮЧАЙ это поле"
    }},
    "interpretation_options": {{
        "goal": ["вариант 1", "вариант 2", "вариант 3"] - ТОЛЬКО если goal в extracted_info,
        "problem": ["вариант 1", "вариант 2", "вариант 3"] - ТОЛЬКО если problem в extracted_info,
        ... (для каждого поля из extracted_info предложи 3 варианта интерпретации)
    }},
    "missing_fields": ["список полей которые еще не заполнены на основе текущего состояния"],
    "next_question": "естественный вопрос для пользователя на русском языке о следующем незаполненном поле",
    "confidence": 0.8
}}

КРИТИЧЕСКИ ВАЖНО:
- Включай поле в extracted_info ТОЛЬКО если пользователь действительно предоставил информацию для этого поля
- НЕ включай поля с пустыми строками, "—", "-", "не указано" или другими placeholder значениями
- НЕ включай поле, если информации для него нет в сообщении пользователя
- В missing_fields укажи поля, которые реально не заполнены (проверь current_state)
- next_question должен быть о следующем незаполненном поле (первое из missing_fields)
- Если все поля заполнены, next_question должен быть поздравлением и предложением сформировать документы
- В interpretation_options для КАЖДОГО поля из extracted_info предложи РОВНО 3 варианта УТОЧНЕНИЯ/РАСШИРЕНИЯ:
  * КРИТИЧЕСКИ ВАЖНО: это НЕ интерпретации, а варианты того, как можно ЛОГИЧЕСКИ РАЗВИТЬ и УТОЧНИТЬ мысль пользователя
  * Представь, что пользователь дал краткий/неполный ответ, и ты предлагаешь 3 разных способа его УТОЧНИТЬ/РАСШИРИТЬ
  * Каждый вариант - это логическое продолжение мысли пользователя, но с РАЗНЫМ акцентом или деталями
  
  ПРАВИЛО: Вместо того чтобы спрашивать "Уточните, пожалуйста...", предложи 3 готовых варианта уточнения:
  
  Вариант 1: Базовое уточнение - минимальное развитие мысли, близко к оригиналу
  Вариант 2: Среднее уточнение - добавление конкретики и деталей
  Вариант 3: Расширенное уточнение - полное развитие с дополнительными аспектами
  
  ПРИМЕР (пользователь сказал: "разработать систему накоплений"):
  ПЛОХО (похожие формулировки):
    1. Разработать систему автоматических накоплений
    2. Создать систему для автоматических накоплений  
    3. Разработать платформу автоматических накоплений
  
  ХОРОШО (логическое развитие мысли):
    1. Разработать систему автоматических накоплений для клиентов банка (базовое уточнение)
    2. Создать систему автоматических накоплений с настройкой целей и умными рекомендациями (среднее уточнение)
    3. Разработать комплексную платформу автоматических накоплений с анализом расходов, финансовыми целями и автоматическими переводами (расширенное уточнение)
  
  * Все 3 варианта должны ЛОГИЧЕСКИ продолжаться от исходного сообщения пользователя
  * Варианты должны отличаться уровнем детализации и полноты
  * Варианты должны быть краткими (до 100 символов каждый) но содержательными
  * Если поле не в extracted_info - НЕ включай его в interpretation_options
"""


class IntelligentDialogManager:
    """Intelligent dialog manager that uses LLM to understand context and extract information."""

    def __init__(self, state: ConversationState, llm_engine: LLMEngine):
        self.state = state
        self.llm_engine = llm_engine
        self.conversation_history: List[Dict[str, str]] = []
        self.pending_options: Dict[str, List[str]] = {}  # Store pending interpretation options

    def process_message(self, user_message: str) -> tuple[str, Dict[str, List[str]]]:
        """
        Process user message, extract information, update state, and generate response.
        Always saves extracted info directly to the most appropriate field.
        
        Returns:
            Tuple of (response message, empty dict - no interpretation options)
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Analyze message through LLM
        try:
            analysis = self._analyze_message(user_message)
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            # Fallback: save message to first missing field
            missing_fields = self.state.get_missing_fields()
            if missing_fields:
                first_field = missing_fields[0]
                if self._is_value_valid(user_message):
                    self.state.update_field(first_field, user_message)
                    next_field = self.state.get_missing_fields()[0] if len(missing_fields) > 1 else None
                    if next_field:
                        response_message = f"Спасибо! {FIELD_METADATA[next_field]['question']}"
                    elif self.state.is_complete():
                        response_message = "Превосходно! Все необходимые данные собраны. Можете сформировать документы."
                    else:
                        response_message = "Спасибо! Что еще вы хотели бы добавить?"
                else:
                    response_message = "Извините, произошла ошибка при анализе сообщения. Попробуйте переформулировать."
            else:
                response_message = "Извините, произошла ошибка при анализе сообщения. Попробуйте переформулировать."
            return (response_message, {})

        # Always save extracted info directly - no interpretation options
        updated_fields = []
        
        # ВАЖНО: Получаем список пустых полей ДО сохранения
        missing_fields_before = self.state.get_missing_fields()
        
        # КРИТИЧЕСКИ ВАЖНО: Определяем, про какое поле был задан последний вопрос
        last_question_field = None
        if self.conversation_history:
            for msg in reversed(self.conversation_history[-3:]):
                if msg["role"] == "assistant":
                    last_question = msg["content"]
                    # Проверяем, про какое поле был вопрос
                    for field in FIELD_SEQUENCE:
                        field_question = FIELD_METADATA[field]["question"]
                        field_label_name = field_label(field)
                        if field_question in last_question or field_label_name in last_question:
                            last_question_field = field
                            logger.info(f"Last question was about field: {field}")
                            break
                    if last_question_field:
                        break
        
        # If we have extracted info, save it to appropriate fields
        if analysis.extracted_info:
            # Если был задан вопрос про конкретное поле, сохраняем ТОЛЬКО в это поле
            if last_question_field and last_question_field in analysis.extracted_info:
                # Сохраняем только в поле, про которое был вопрос
                value = analysis.extracted_info[last_question_field]
                if value and isinstance(value, str):
                    value = value.strip()
                    if self._is_value_valid(value):
                        existing_value = self.state.answers.get(last_question_field, "").strip()
                        if existing_value and self._is_value_valid(existing_value):
                            # Поле уже заполнено - проверяем на дубликат
                            if value.lower() not in existing_value.lower() and existing_value.lower() not in value.lower():
                                self.state.update_field(last_question_field, f"{existing_value}\n\n{value}")
                                updated_fields.append(last_question_field)
                                logger.info(f"Merged to last question field: {last_question_field}")
                        else:
                            self.state.update_field(last_question_field, value)
                            updated_fields.append(last_question_field)
                            logger.info(f"Saved to last question field: {last_question_field}")
                # Игнорируем все остальные поля, даже если LLM их извлек
                logger.info(f"Ignoring other extracted fields because last question was about {last_question_field}")
            else:
                # Нет контекста последнего вопроса - сохраняем все извлеченные поля
                for field, value in analysis.extracted_info.items():
                    if field not in FIELD_SEQUENCE:
                        continue
                    
                    # Clean and validate value
                    if not value:
                        continue
                    
                    value = value.strip()
                    
                    # Validate value before saving
                    if not self._is_value_valid(value):
                        continue
                    
                    # ВАЖНО: Проверяем, заполнено ли поле
                    existing_value = self.state.answers.get(field, "").strip()
                    if existing_value and self._is_value_valid(existing_value):
                        # Поле уже заполнено - проверяем, не является ли новое значение просто дубликатом
                        if value.lower() in existing_value.lower() or existing_value.lower() in value.lower():
                            # Это дубликат или очень похожее - не сохраняем
                            logger.info(f"Skipping duplicate value for field {field}")
                            continue
                        # Если новое значение существенно отличается - объединяем
                        if value not in existing_value and existing_value not in value:
                            self.state.update_field(field, f"{existing_value}\n\n{value}")
                            updated_fields.append(field)
                            logger.info(f"Merged additional info to field {field}")
                    else:
                        # Поле пустое - сохраняем
                        self.state.update_field(field, value)
                        updated_fields.append(field)
                        logger.info(f"Saved new value to field {field}")
        
        # If no extracted info but message is valid, save to first missing field
        if not updated_fields:
            missing_fields = self.state.get_missing_fields()
            if missing_fields and self._is_value_valid(user_message):
                first_field = missing_fields[0]
                self.state.update_field(first_field, user_message)
                updated_fields.append(first_field)
                logger.info(f"Saved message to first missing field: {first_field}")
        
        # Log updates
        if updated_fields:
            logger.info(f"Updated fields: {updated_fields}")

        # КРИТИЧЕСКИ ВАЖНО: Всегда проверяем РЕАЛЬНОЕ состояние полей перед генерацией вопроса
        missing_fields = self.state.get_missing_fields()
        
        # Проверяем, является ли сообщение общим вопросом (не данными)
        user_message_lower = user_message.lower().strip()
        general_questions = [
            "с чего начать", "что делать", "как начать", "помоги", "помощь",
            "какие поля", "что заполнено", "что осталось", "что не заполнено",
            "какие данные", "что нужно", "что осталось заполнить",
            "какие поля не заполнены", "что еще нужно заполнить",
            "что уже есть", "что уже заполнено", "статус", "прогресс"
        ]
        
        is_general_question = any(phrase in user_message_lower for phrase in general_questions)
        
        # Если это общий вопрос, отвечаем на него
        if is_general_question:
            if "с чего начать" in user_message_lower or "как начать" in user_message_lower:
                if missing_fields:
                    next_field = missing_fields[0]
                    response_message = (
                        f"Отлично, давайте начнем! Сначала мне нужно узнать о **{field_label(next_field)}**.\n\n"
                        f"{FIELD_METADATA[next_field]['question']}\n\n"
                        "Вы можете ответить прямо сейчас или задать любой другой вопрос."
                    )
                else:
                    response_message = "Все необходимые данные уже собраны! Можете сформировать документы."
            elif any(phrase in user_message_lower for phrase in ["какие поля", "что заполнено", "что осталось", "статус", "прогресс"]):
                if not missing_fields:
                    response_message = "Отлично! Все необходимые поля заполнены. Можете сформировать документы."
                else:
                    missing_labels = [field_label(field) for field in missing_fields]
                    if len(missing_fields) == 1:
                        response_message = (
                            f"Осталось заполнить только одно поле: **{missing_labels[0]}**.\n\n"
                            f"{FIELD_METADATA[missing_fields[0]]['question']}"
                        )
                    else:
                        fields_text = ", ".join([f"**{label}**" for label in missing_labels[:-1]]) + f" и **{missing_labels[-1]}**"
                        response_message = (
                            f"Осталось заполнить {len(missing_fields)} полей: {fields_text}.\n\n"
                            f"Давайте начнем с **{missing_labels[0]}**: {FIELD_METADATA[missing_fields[0]]['question']}"
                        )
            else:
                # Общий вопрос о помощи
                if missing_fields:
                    next_field = missing_fields[0]
                    response_message = (
                        f"Я помогу вам собрать все необходимые данные для проекта.\n\n"
                        f"Сейчас нужно заполнить поле **{field_label(next_field)}**:\n"
                        f"{FIELD_METADATA[next_field]['question']}\n\n"
                        "Просто опишите ваш проект в свободной форме, и я автоматически заполню нужные поля."
                    )
                else:
                    response_message = "Все данные собраны! Можете сформировать документы."
        else:
            # Обычное сообщение с данными - используем вопрос из анализа, но проверяем реальное состояние
            response_message = analysis.next_question
            
            # ВАЖНО: Перепроверяем, что вопрос соответствует реальному состоянию полей
            if missing_fields:
                # Проверяем, упоминает ли вопрос правильное поле
                next_field = missing_fields[0]
                field_label_lower = field_label(next_field).lower()
                question_lower = response_message.lower()
                
                # Если вопрос не про нужное поле, заменяем его
                if field_label_lower not in question_lower and next_field not in question_lower:
                    response_message = FIELD_METADATA[next_field]['question']
            elif self.state.is_complete():
                # Если все заполнено, но LLM не понял - исправляем
                response_message = "Превосходно! Все необходимые данные собраны. Можете сформировать документы."
            elif not response_message or response_message.strip() == "":
                # Если нет вопроса, генерируем на основе реального состояния
                if missing_fields:
                    next_field = missing_fields[0]
                    response_message = FIELD_METADATA[next_field]['question']
                else:
                    response_message = "Спасибо! Что еще вы хотели бы добавить?"
        
        # Add assistant response to history
        if response_message:
            self.conversation_history.append({
                "role": "assistant", 
                "content": response_message
            })

        # Always return empty interpretation options - no user selection needed
        return (response_message, {})
    
    def select_interpretation(self, field: str, selected_option: str) -> tuple[str, Dict[str, List[str]]]:
        """Save selected interpretation option to field and generate next question."""
        if field not in FIELD_SEQUENCE:
            return ("", {})
        
        # Validate and save
        next_question = ""
        next_options = {}
        
        if selected_option and self._is_value_valid(selected_option):
            existing_value = self.state.answers.get(field, "").strip()
            if existing_value and self._is_value_valid(existing_value):
                # Merge if different
                if selected_option not in existing_value:
                    self.state.update_field(field, f"{existing_value}\n\n{selected_option}")
            else:
                self.state.update_field(field, selected_option)
            
            # Remove from pending options
            self.pending_options.pop(field, None)
            logger.info(f"Selected interpretation for {field}: {selected_option[:50]}...")
            
            # Generate next question automatically
            missing = self.state.get_missing_fields()
            if missing:
                next_field = missing[0]
                next_label = field_label(next_field)
                next_question = f"Отлично! Теперь давайте перейдем к следующему вопросу. {FIELD_METADATA[next_field]['question']}"
            elif self.state.is_complete():
                next_question = "Превосходно! Все необходимые данные собраны. Можете сформировать документы."
            else:
                next_question = "Спасибо! Что еще вы хотели бы добавить?"
        
        return (next_question, next_options)
    
    def process_custom_interpretation(self, field: str, custom_value: str, original_message: str) -> tuple[str, Dict[str, List[str]]]:
        """Process custom user input with context and save to field."""
        if field not in FIELD_SEQUENCE:
            return
        
        if not custom_value or not custom_value.strip():
            return
        
        # Use LLM to combine context and custom input into a well-formed value
        prompt = f"""Ты — опытный бизнес-аналитик, который обрабатывает требования.

Поле: {field_label(field)} ({field})
Вопрос для этого поля: {FIELD_METADATA[field]["question"]}

Исходное сообщение пользователя: {original_message[:200] if original_message else "не указано"}

Пользователь дополнил/уточнил свое сообщение: {custom_value}

Задача: Объедини исходное сообщение и уточнение пользователя в ОДНУ правильную формулировку для поля "{field_label(field)}".

ВАЖНО:
- Склей информацию из исходного сообщения и уточнения естественным образом
- Результат должен быть конкретным и полным
- Длина результата должна быть разумной (100-200 символов, если возможно)
- Результат должен отвечать на вопрос поля
- Верни ТОЛЬКО финальную формулировку, без дополнительных комментариев"""

        try:
            processed_value = self.llm_engine.ask(prompt).strip()
            
            # Clean up - remove quotes if LLM wrapped it
            if processed_value.startswith('"') and processed_value.endswith('"'):
                processed_value = processed_value[1:-1]
            if processed_value.startswith("'") and processed_value.endswith("'"):
                processed_value = processed_value[1:-1]
            
            # Validate and save
            if processed_value and self._is_value_valid(processed_value):
                existing_value = self.state.answers.get(field, "").strip()
                if existing_value and self._is_value_valid(existing_value):
                    # Merge if different
                    if processed_value not in existing_value and existing_value not in processed_value:
                        self.state.update_field(field, f"{existing_value}\n\n{processed_value}")
                    else:
                        # If new value is more complete, replace
                        if len(processed_value) > len(existing_value) * 1.2:
                            self.state.update_field(field, processed_value)
                else:
                    self.state.update_field(field, processed_value)
                
                logger.info(f"Processed custom interpretation for {field}: {processed_value[:50]}...")
            else:
                # Fallback: use custom_value directly if LLM failed
                if self._is_value_valid(custom_value):
                    self.state.update_field(field, custom_value)
                    logger.info(f"Saved custom value directly for {field} (LLM processing failed)")
        except Exception as e:
            logger.error(f"Error processing custom interpretation: {e}")
            # Fallback: save custom_value directly
            if self._is_value_valid(custom_value):
                self.state.update_field(field, custom_value)
        
        # Generate next question automatically
        next_question = ""
        next_options = {}
        missing = self.state.get_missing_fields()
        if missing:
            next_field = missing[0]
            next_label = field_label(next_field)
            next_question = f"Отлично! Теперь давайте перейдем к следующему вопросу. {FIELD_METADATA[next_field]['question']}"
        elif self.state.is_complete():
            next_question = "Превосходно! Все необходимые данные собраны. Можете сформировать документы."
        else:
            next_question = "Спасибо! Что еще вы хотели бы добавить?"
        
        return (next_question, next_options)

    def _analyze_message(self, user_message: str) -> DialogAnalysis:
        """Analyze user message using LLM and extract information."""
        prompt = self._build_analysis_prompt(user_message)
        
        try:
            response = self.llm_engine.ask(prompt)
            # Try to extract JSON from response
            analysis_data = self._extract_json(response)
            
            # Validate and create analysis object
            extracted_info = analysis_data.get("extracted_info", {})
            interpretation_options = analysis_data.get("interpretation_options", {})
            next_question = analysis_data.get("next_question", "Расскажите больше о вашем проекте.")
            confidence = analysis_data.get("confidence", 0.5)
            
            # Clean interpretation_options - ensure it's a dict with lists
            cleaned_options = {}
            for field, options in interpretation_options.items():
                if isinstance(options, list) and len(options) >= 3:
                    cleaned_options[field] = options[:3]  # Take first 3
                elif isinstance(options, list) and len(options) > 0:
                    # If less than 3, pad with first option
                    while len(options) < 3:
                        options.append(options[0])
                    cleaned_options[field] = options[:3]
            
            # КРИТИЧЕСКИ ВАЖНО: Пересчитываем missing_fields на основе РЕАЛЬНОГО состояния state
            # Не доверяем LLM - он может ошибиться
            missing_fields = self.state.get_missing_fields()
            
            # ВАЖНО: Всегда используем реальное состояние полей, не доверяем LLM
            # Проверяем, является ли сообщение общим вопросом
            user_message_lower = user_message.lower().strip()
            general_questions = [
                "с чего начать", "что делать", "как начать", "помоги", "помощь",
                "какие поля", "что заполнено", "что осталось", "что не заполнено",
                "какие данные", "что нужно", "что осталось заполнить",
                "какие поля не заполнены", "что еще нужно заполнить",
                "что уже есть", "что уже заполнено", "статус", "прогресс"
            ]
            
            is_general_question = any(phrase in user_message_lower for phrase in general_questions)
            
            # Если это общий вопрос, генерируем соответствующий ответ
            if is_general_question:
                if not missing_fields:
                    next_question = "Отлично! Все необходимые поля заполнены. Можете сформировать документы."
                else:
                    missing_labels = [field_label(field) for field in missing_fields]
                    if len(missing_fields) == 1:
                        next_question = (
                            f"Осталось заполнить только одно поле: **{missing_labels[0]}**.\n\n"
                            f"{FIELD_METADATA[missing_fields[0]]['question']}"
                        )
                    else:
                        fields_text = ", ".join([f"**{label}**" for label in missing_labels[:-1]]) + f" и **{missing_labels[-1]}**"
                        next_question = (
                            f"Осталось заполнить {len(missing_fields)} полей: {fields_text}.\n\n"
                            f"Давайте начнем с **{missing_labels[0]}**: {FIELD_METADATA[missing_fields[0]]['question']}"
                        )
            elif missing_fields:
                # Обычный режим - задаем вопрос о следующем поле
                first_missing = missing_fields[0]
                # ВАЖНО: Проверяем, что LLM сгенерировал вопрос про правильное поле
                # Если нет - заменяем на правильный
                field_label_lower = field_label(first_missing).lower()
                question_lower = next_question.lower()
                
                if first_missing not in question_lower and field_label_lower not in question_lower:
                    # LLM ошибся - используем правильный вопрос
                    next_question = FIELD_METADATA[first_missing]['question']
            elif self.state.is_complete():
                # Все заполнено
                next_question = "Превосходно! Все необходимые данные собраны. Можете сформировать документы."
            else:
                # Fallback - пересчитываем missing_fields еще раз на всякий случай
                missing = self.state.get_missing_fields()
                if missing:
                    next_question = FIELD_METADATA[missing[0]]['question']
                else:
                    next_question = "Спасибо! Что еще вы хотели бы добавить?"
            
            # Create analysis object
            analysis_obj = DialogAnalysis(
                extracted_info=extracted_info,
                missing_fields=missing_fields,
                next_question=next_question,
                confidence=confidence,
                interpretation_options=cleaned_options
            )
            
            return analysis_obj
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            # Fallback analysis
            missing = self.state.get_missing_fields()
            if missing:
                next_field = missing[0]
                next_question = FIELD_METADATA[next_field]["question"]
            else:
                next_question = "Расскажите больше о вашем проекте."
            
            fallback_analysis = DialogAnalysis(
                extracted_info={},
                missing_fields=missing,
                next_question=next_question,
                confidence=0.3,
                interpretation_options={}
            )
            return fallback_analysis

    def _build_analysis_prompt(self, user_message: str) -> str:
        """Build prompt for LLM analysis."""
        # Format field descriptions
        field_descriptions = []
        for field in FIELD_SEQUENCE:
            label = field_label(field)
            question = FIELD_METADATA[field]["question"]
            field_descriptions.append(f"- {field}: {label} ({question})")
        
        # Format current state
        current_state_lines = []
        for field in FIELD_SEQUENCE:
            label = field_label(field)
            value = self.state.answers.get(field, "").strip()
            if value:
                current_state_lines.append(f"- {label}: {value[:100]}...")
            else:
                current_state_lines.append(f"- {label}: не заполнено")
        
        # Format conversation history (last 5 messages)
        history_lines = []
        for msg in self.conversation_history[-5:]:
            role = "Пользователь" if msg["role"] == "user" else "Аналитик"
            history_lines.append(f"{role}: {msg['content']}")
        
        # Определяем, какой вопрос был задан последним (если есть)
        last_question_context = ""
        if self.conversation_history:
            # Ищем последнее сообщение от аналитика
            for msg in reversed(self.conversation_history[-5:]):
                if msg["role"] == "assistant":
                    last_question = msg["content"]
                    # Проверяем, про какое поле был вопрос
                    for field in FIELD_SEQUENCE:
                        field_question = FIELD_METADATA[field]["question"]
                        field_label_name = field_label(field)
                        if field_question in last_question or field_label_name in last_question:
                            last_question_context = f"\n\nВАЖНО: Последний вопрос бота был про поле '{field_label_name}' ({field}). Ответ пользователя относится ТОЛЬКО к этому полю. НЕ извлекай информацию для других полей!"
                            break
                    break
        
        return CONTEXT_UNDERSTANDING_PROMPT.format(
            field_descriptions="\n".join(field_descriptions),
            current_state="\n".join(current_state_lines),
            conversation_history="\n".join(history_lines) if history_lines else "Диалог только начинается",
            user_message=user_message,
            last_question_context=last_question_context
        )

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response."""
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                # Clean extracted_info - remove empty or placeholder values
                if "extracted_info" in data:
                    cleaned_info = {}
                    for field, value in data["extracted_info"].items():
                        if value and isinstance(value, str):
                            value = value.strip()
                            # Skip placeholder text
                            invalid = ["", "—", "-", "не указано", "не заполнено", 
                                      "извлеченная информация или пустая строка",
                                      "извлеченная информация", "пустая строка"]
                            if value and value.lower() not in [v.lower() for v in invalid] and len(value) >= 5:
                                cleaned_info[field] = value
                    data["extracted_info"] = cleaned_info
                return data
            except json.JSONDecodeError:
                pass
        
        # Try to parse entire response as JSON
        try:
            data = json.loads(text)
            # Clean extracted_info
            if "extracted_info" in data:
                cleaned_info = {}
                for field, value in data["extracted_info"].items():
                    if value and isinstance(value, str):
                        value = value.strip()
                        invalid = ["", "—", "-", "не указано", "не заполнено",
                                  "извлеченная информация или пустая строка",
                                  "извлеченная информация", "пустая строка"]
                        if value and value.lower() not in [v.lower() for v in invalid] and len(value) >= 5:
                            cleaned_info[field] = value
                data["extracted_info"] = cleaned_info
            return data
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from response: {text[:200]}")
            return {
                "extracted_info": {},
                "interpretation_options": {},
                "missing_fields": self.state.get_missing_fields(),
                "next_question": "Расскажите больше о вашем проекте.",
                "confidence": 0.3
            }

    def get_greeting(self) -> str:
        """Get initial greeting message."""
        fields_list = []
        for field in FIELD_SEQUENCE:
            label = field_label(field)
            fields_list.append(f"- **{label}**")
        
        fields_text = "\n".join(fields_list)
        
        return (
            "Привет! Я AI-бизнес-аналитик, созданный для помощи в сборе и структурировании требований к проекту.\n\n"
            "**Моя задача:** помочь вам сформировать структурированный документ (BRD, Use Case, User Stories) на основе ваших требований.\n\n"
            "**Какие данные мне нужны:**\n\n"
            f"{fields_text}\n\n"
            "**Как работать:**\n\n"
            "Вы можете писать всю информацию сразу или частями - я пойму, что вы имеете в виду, и автоматически заполню соответствующие поля.\n\n"
            "Также вы можете задавать любые вопросы, например:\n\n"
            "- С чего начать?\n"
            "- Какие поля уже заполнены?\n"
            "- Что еще нужно указать?\n\n"
            "**Готовы начать?** Расскажите о вашем проекте!"
        )

    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        return self.state.is_complete()

    def _is_value_valid(self, value: str) -> bool:
        """Check if value is valid (not empty, not placeholder)."""
        if not value or not value.strip():
            return False
        
        invalid_values = [
            "", "—", "-", "не указано", "не заполнено",
            "извлеченная информация или пустая строка",
            "извлеченная информация",
            "пустая строка",
        ]
        
        value_lower = value.strip().lower()
        if value_lower in [v.lower() for v in invalid_values]:
            return False
        
        # Skip if too short
        if len(value.strip()) < 5:
            return False
        
        return True


__all__ = ["IntelligentDialogManager", "DialogAnalysis"]
