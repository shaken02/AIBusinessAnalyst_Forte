"""Streamlit UI entrypoint."""

from __future__ import annotations

import time
import streamlit as st

from app.config import settings
from app.core.dialog_manager import DialogManager
from app.core.intelligent_dialog_manager import IntelligentDialogManager
from app.core.llm_engine import create_engine
from app.core.orchestrator import DocumentBundle, Orchestrator
from app.utils.logger import logger
from app.utils.state import ConversationState, FIELD_SEQUENCE, field_label, FIELD_METADATA

PAGE_TITLE = settings.app.name


def init_session_state() -> None:
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = ConversationState()
    if "dialog_mode" not in st.session_state:
        st.session_state.dialog_mode = "intelligent"  # "intelligent" or "structured"
    if "dialog_manager" not in st.session_state:
        _init_dialog_manager()
    if "orchestrator" not in st.session_state:
        selected_model = st.session_state.get("selected_gemini_model", "gemini-2.5-flash")
        st.session_state.orchestrator = Orchestrator(model_name=selected_model)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "documents" not in st.session_state:
        st.session_state.documents: DocumentBundle | None = None
    if "greeting_shown" not in st.session_state:
        st.session_state.greeting_shown = False
    if "pending_interpretations" not in st.session_state:
        st.session_state.pending_interpretations = {}  # Field -> list of options
    if "waiting_for_custom_input" not in st.session_state:
        st.session_state.waiting_for_custom_input = None  # Field name or None
    if "custom_input_context" not in st.session_state:
        st.session_state.custom_input_context = {}  # Field -> original user message for context
    if "analytical_mode" not in st.session_state:
        st.session_state.analytical_mode = False  # Режим анализа после генерации документов
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False  # Начался ли разговор
    if "selected_gemini_model" not in st.session_state:
        st.session_state.selected_gemini_model = "gemini-2.5-flash"  # По умолчанию flash


def _init_dialog_manager() -> None:
    """Initialize dialog manager based on current mode."""
    state = st.session_state.conversation_state
    mode = st.session_state.get("dialog_mode", "intelligent")
    
    if mode == "intelligent":
        # Используем выбранную модель Gemini
        selected_model = st.session_state.get("selected_gemini_model", "gemini-2.5-flash")
        llm_engine = create_engine(model_name=selected_model)
        st.session_state.dialog_manager = IntelligentDialogManager(state, llm_engine)
    else:
        st.session_state.dialog_manager = DialogManager(state)


def reset_dialog() -> None:
    st.session_state.conversation_state = ConversationState()
    st.session_state.chat_history = []
    st.session_state.documents = None
    st.session_state.greeting_shown = False
    st.session_state.pending_interpretations = {}
    st.session_state.waiting_for_custom_input = None
    st.session_state.custom_input_context = {}
    st.session_state.analytical_mode = False  # Сбрасываем аналитический режим
    # Очищаем кэш PDF и PlantUML при сбросе
    if "pdf_data_cache" in st.session_state:
        del st.session_state.pdf_data_cache
    if "pdf_data_cache_id" in st.session_state:
        del st.session_state.pdf_data_cache_id
    # Очищаем кэш PlantUML (все ключи начинающиеся с plantuml_png_)
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("plantuml_png_")]
    for key in keys_to_delete:
        del st.session_state[key]
    _init_dialog_manager()
    
    # Бот пишет сообщение в чат о сбросе (если intelligent режим)
    mode = st.session_state.get("dialog_mode", "intelligent")
    if mode == "intelligent":
        reset_message = "Вижу, что вы сбросили диалог. Давайте начнем сначала! Расскажите о вашем проекте - начните с описания того, что вы хотите создать."
        st.session_state.chat_history.append({"role": "assistant", "content": reset_message})
        st.session_state.conversation_started = True  # Разговор уже начат после сброса


def enqueue_next_question() -> None:
    """Enqueue next question for structured mode only."""
    if st.session_state.get("dialog_mode") != "structured":
        return
    manager = st.session_state.dialog_manager
    if not isinstance(manager, DialogManager):
        return
    question = manager.get_next_question()
    if not question:
        return
    history = st.session_state.chat_history
    if history and history[-1]["role"] == "assistant" and history[-1].get("field") == question.field:
        return
    history.append({"role": "assistant", "content": question.text, "field": question.field})


def render_sidebar(state: ConversationState) -> None:
    st.sidebar.header("Настройки")
    
    # Dialog mode selector
    mode = st.sidebar.radio(
        "Режим диалога",
        ["intelligent", "structured"],
        format_func=lambda x: "Свободный диалог" if x == "intelligent" else "Структурированная форма",
        index=0 if st.session_state.get("dialog_mode", "intelligent") == "intelligent" else 1,
        key="dialog_mode_selector"
    )
    
    # Update manager if mode changed
    if mode != st.session_state.get("dialog_mode"):
        st.session_state.dialog_mode = mode
        _init_dialog_manager()
        st.session_state.greeting_shown = False
        st.rerun()
    
    # Gemini model selector (for both modes if gemini provider)
    if settings.model.provider == "gemini":
        st.sidebar.divider()
        selected_model = st.sidebar.selectbox(
            "Модель Gemini",
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0 if st.session_state.get("selected_gemini_model", "gemini-2.5-flash") == "gemini-2.5-flash" else 1,
            key="gemini_model_selector_sidebar",
            help="Flash - быстрее и дешевле, Pro - более качественные ответы"
        )
        
        # Update manager and orchestrator if model changed
        if selected_model != st.session_state.get("selected_gemini_model"):
            st.session_state.selected_gemini_model = selected_model
            if mode == "intelligent":
                _init_dialog_manager()
            # Пересоздаем orchestrator с новой моделью
            st.session_state.orchestrator = Orchestrator(model_name=selected_model)
            st.rerun()
    
    st.sidebar.divider()
    
    st.sidebar.header("Прогресс")
    st.sidebar.progress(state.progress_ratio())
    st.sidebar.metric("Заполнено полей", f"{len(state.answers)}/{len(FIELD_SEQUENCE)}")
    st.sidebar.header("Поля")
    
    # Определяем текущее поле (первое незаполненное)
    missing_fields = state.get_missing_fields()
    current_field = missing_fields[0] if missing_fields else None
    
    for field in FIELD_SEQUENCE:
        label = field_label(field)
        value = state.answers.get(field)
        indicator = "✓" if value else "—"
        
        # Определяем стиль для поля
        is_filled = bool(value and value.strip())
        is_current = field == current_field and not st.session_state.get("analytical_mode", False)
        
        # Show expandable section for each field
        with st.sidebar.expander(f"{indicator} {label}", expanded=False):
            # Добавляем data-атрибут для подсветки текущего поля через CSS
            if is_current:
                st.markdown(f'<div data-field-current="true" style="display:none;"></div>', unsafe_allow_html=True)
            if value:
                st.text_area(
                    f"Редактировать {label}",
                    value=value,
                    key=f"edit_{field}",
                    height=100,
                    label_visibility="collapsed"
                )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Сохранить", key=f"save_{field}"):
                        new_value = st.session_state.get(f"edit_{field}", value)
                        if new_value and new_value.strip():
                            state.update_field(field, new_value.strip())
                            st.session_state.documents = None
                            # Очищаем кэш PDF и PlantUML при изменении данных
                            if "pdf_data_cache" in st.session_state:
                                del st.session_state.pdf_data_cache
                            if "pdf_data_cache_id" in st.session_state:
                                del st.session_state.pdf_data_cache_id
                            # Очищаем кэш PlantUML
                            keys_to_delete = [key for key in st.session_state.keys() if key.startswith("plantuml_png_")]
                            for key in keys_to_delete:
                                del st.session_state[key]
                            st.rerun()
                with col2:
                    if st.button("Очистить", key=f"clear_{field}"):
                        state.answers.pop(field, None)
                        st.session_state.documents = None
                        # Очищаем кэш PDF и PlantUML при очистке поля
                        if "pdf_data_cache" in st.session_state:
                            del st.session_state.pdf_data_cache
                        if "pdf_data_cache_id" in st.session_state:
                            del st.session_state.pdf_data_cache_id
                        # Очищаем кэш PlantUML
                        keys_to_delete = [key for key in st.session_state.keys() if key.startswith("plantuml_png_")]
                        for key in keys_to_delete:
                            del st.session_state[key]
                        st.rerun()
            else:
                st.info("Поле не заполнено")
    st.sidebar.divider()
    st.sidebar.button("Сбросить диалог", on_click=reset_dialog, type="secondary")


def render_document_tabs(bundle: DocumentBundle) -> None:
    tabs = st.tabs(["BRD", "Use Case", "User Stories", "PlantUML"])
    for tab, (label, content) in zip(tabs, bundle.as_dict().items(), strict=False):
        with tab:
            if label == "PlantUML":
                # Special handling for PlantUML - show only visual diagram (no code)
                st.subheader("PlantUML Диаграмма")
                
                # Кэшируем PNG диаграмму в session_state, чтобы не рендерить при каждом rerun
                # Используем более стабильный ключ на основе bundle ID
                bundle_id = id(bundle) if bundle else 0
                plantuml_cache_key = f"plantuml_png_{bundle_id}_{hash(content)}"
                
                # Используем кэшированное изображение, если оно есть
                png_bytes = st.session_state.get(plantuml_cache_key)
                
                if png_bytes is None:
                    # Рендерим только если кэш пуст
                    from app.utils.plantuml_renderer import render_plantuml_to_png
                    
                    try:
                        with st.spinner("Рендеринг диаграммы..."):
                            png_bytes = render_plantuml_to_png(content)
                        
                        if png_bytes:
                            # Сохраняем в кэш
                            st.session_state[plantuml_cache_key] = png_bytes
                        else:
                            st.session_state[plantuml_cache_key] = False  # Используем False для ошибки
                    except Exception as e:
                        logger.error(f"Ошибка при рендеринге диаграммы: {e}")
                        st.session_state[plantuml_cache_key] = False
                        png_bytes = False
                
                # Отображаем изображение или ошибку
                if png_bytes and png_bytes is not False:
                    st.image(png_bytes, caption="PlantUML диаграмма", use_container_width=True)
                elif png_bytes is False:
                    st.warning("Не удалось сгенерировать диаграмму локально")
                    st.info("Проверьте логи приложения или убедитесь, что установлены Java и plantuml.jar")
            else:
                st.markdown(content)


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    
    # Apply Forte theme CSS
    st.markdown("""
    <style>
        /* Forte Theme - Updated colors */
        :root {
            --forte-primary: #E91E63;
            --forte-primary-dark: #C2185B;
            --forte-secondary: #F06292;
            --forte-dark-bg: #1A0E1A;
            --forte-darker-bg: #2D1B2D;
            --forte-text: #FFFFFF;
            --forte-text-light: #E0E0E0;
            --forte-accent: #EC407A;
            --forte-red: #DC143C;
            --forte-light-red: #FF6B8A;
            --forte-dark-pink: #C2185B;
            --forte-white: #FFFFFF;
        }
        
        /* Main container styling - WHITE background */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            background-color: var(--forte-white) !important;
        }
        
        .main {
            background-color: var(--forte-white) !important;
        }
        
        /* Main content area - white background, dark pink text */
        .element-container, .stMarkdown, h1, h2, h3, p, .stTitle {
            color: var(--forte-dark-pink) !important;
        }
        
        /* Chat messages styling - white background */
        .stChatMessage {
            background-color: var(--forte-white) !important;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .stChatMessage .stMarkdown {
            color: var(--forte-dark-pink) !important;
        }
        
        /* Sidebar styling - DARKER PINK background with GRADIENT */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #8B1045 0%, #6B0C35 50%, #4A0825 100%) !important;
            background-color: #8B1045 !important;
        }
        
        .css-1d391kg, .css-1lcbmhc, [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #8B1045 0%, #6B0C35 50%, #4A0825 100%) !important;
            background-color: #8B1045 !important;
        }
        
        /* Text area in sidebar - DARKER with rounded corners and WHITE THICK BORDER */
        .stSidebar .stTextArea textarea {
            background-color: #5A0A2D !important;
            color: var(--forte-white) !important;
            border: 3px solid var(--forte-white) !important;
            border-radius: 12px !important;
            padding: 12px !important;
        }
        
        /* Text input in sidebar - DARKER with rounded corners and WHITE THICK BORDER */
        .stSidebar .stTextInput input {
            background-color: #5A0A2D !important;
            color: var(--forte-white) !important;
            border: 3px solid var(--forte-white) !important;
            border-radius: 12px !important;
            padding: 12px !important;
        }
        
        /* Selectbox in sidebar - WHITE background with DARK text for visibility */
        .stSidebar .stSelectbox > div > div {
            background-color: var(--forte-white) !important;
            border: 3px solid var(--forte-white) !important;
            border-radius: 12px !important;
        }
        
        .stSidebar .stSelectbox select,
        .stSidebar .stSelectbox > div > div > select,
        .stSidebar [data-baseweb="select"] {
            background-color: var(--forte-white) !important;
            color: var(--forte-dark-pink) !important;
            border: 3px solid var(--forte-white) !important;
            border-radius: 12px !important;
        }
        
        .stSidebar .stSelectbox [data-baseweb="select"] > div {
            background-color: var(--forte-white) !important;
            color: var(--forte-dark-pink) !important;
        }
        
        .stSidebar .stSelectbox [data-baseweb="select"] span,
        .stSidebar .stSelectbox [data-baseweb="select"] div,
        .stSidebar .stSelectbox [data-baseweb="select"] p {
            color: var(--forte-dark-pink) !important;
        }
        
        /* Selectbox value text - все элементы внутри */
        .stSidebar [data-baseweb="select"] * {
            color: var(--forte-dark-pink) !important;
        }
        
        .stSidebar [data-baseweb="select"] [aria-selected="true"],
        .stSidebar [data-baseweb="select"] div[role="option"],
        .stSidebar [data-baseweb="select"] > div > div {
            color: var(--forte-dark-pink) !important;
            background-color: var(--forte-white) !important;
        }
        
        /* Selectbox input field */
        .stSidebar [data-baseweb="select"] input {
            color: var(--forte-dark-pink) !important;
            background-color: var(--forte-white) !important;
        }
        
        /* Input containers in sidebar - WHITE THICK BORDER */
        .stSidebar .stTextInput > div > div,
        .stSidebar .stTextArea > div > div {
            background-color: #5A0A2D !important;
            border-radius: 12px !important;
            border: 3px solid var(--forte-white) !important;
        }
        
        /* Text input wrapper in sidebar */
        .stSidebar .stTextInput > div > div > div > input,
        .stSidebar .stTextArea > div > div > textarea {
            border: 3px solid var(--forte-white) !important;
        }
        
        /* Sidebar text - WHITE */
        .css-1d391kg *, .css-1lcbmhc *, [data-testid="stSidebar"] * {
            color: var(--forte-white) !important;
        }
        
        .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3,
        .css-1lcbmhc h1, .css-1lcbmhc h2, .css-1lcbmhc h3,
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: var(--forte-white) !important;
        }
        
        /* Sidebar labels and text */
        .stSidebar label, .stSidebar p, .stSidebar span, .stSidebar div {
            color: var(--forte-white) !important;
        }
        
        /* Radio buttons in sidebar */
        .stRadio label {
            color: var(--forte-white) !important;
        }
        
        /* Progress bar in sidebar */
        .stProgress > div > div > div {
            background-color: var(--forte-red) !important;
        }
        
        /* Expander elements (field list items) in sidebar - WHITE THICK BORDER */
        .stSidebar .stExpander,
        .stSidebar [data-testid="stExpander"] {
            border: 3px solid var(--forte-white) !important;
            border-radius: 12px !important;
            margin: 6px 0 !important;
            padding: 4px !important;
        }
        
        /* Expander header/label */
        .stSidebar .stExpander > label,
        .stSidebar [data-testid="stExpander"] > label {
            border: none !important;
            border-radius: 8px !important;
        }
        
        /* Expander content area */
        .stSidebar .stExpander [data-testid="stExpanderContent"] {
            border: none !important;
            border-radius: 8px !important;
        }
        
        /* Sidebar field expanders - стили для заполненных и текущих полей */
        .stSidebar .stExpander {
            margin: 4px 0 !important;
        }
        
        /* Заполненные поля - светло-зеленый фон */
        .stSidebar .stExpander:has([data-testid*="✓"]) {
            background-color: #E8F5E9 !important;
            border: 2px solid #4CAF50 !important;
        }
        
        /* Текущее поле (по которому задается вопрос) - тонкая подсветка */
        .stSidebar .stExpander:has([data-field-current="true"]) {
            border: 2px solid #FFC107 !important;
            box-shadow: 0 0 3px rgba(255, 193, 7, 0.2) !important;
        }
        
        /* Buttons styling */
        .stButton > button {
            background-color: var(--forte-primary);
            color: white !important;
            border-radius: 8px;
            border: none;
            font-weight: 500;
        }
        
        .stButton > button * {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        .stButton > button:hover {
            background-color: var(--forte-primary-dark);
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover * {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        /* Download button - same style as generate button */
        .stDownloadButton > button {
            background-color: var(--forte-primary) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 500 !important;
        }
        
        .stDownloadButton > button * {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        .stDownloadButton > button:hover {
            background-color: var(--forte-primary-dark) !important;
            transition: all 0.3s ease !important;
        }
        
        .stDownloadButton > button:hover * {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        /* Input fields - white background, dark pink text */
        .stTextInput > div > div > input {
            background-color: var(--forte-white) !important;
            color: var(--forte-dark-pink) !important;
            border: 1px solid var(--forte-secondary);
        }
        
        /* Text area - white background, dark pink text */
        .stTextArea > div > div > textarea {
            background-color: var(--forte-white) !important;
            color: var(--forte-dark-pink) !important;
            border: 1px solid var(--forte-secondary);
        }
        
        /* Chat input - white text */
        .stChatInputContainer {
            background-color: var(--forte-white) !important;
        }
        
        .stChatInputContainer input,
        .stChatInputContainer textarea {
            background-color: var(--forte-white) !important;
            color: var(--forte-dark-pink) !important;
        }
        
        /* Chat input placeholder and text */
        .stChatInputContainer input::placeholder,
        .stChatInputContainer textarea::placeholder {
            color: #999999 !important;
        }
        
        /* Fix chat input text color - make it dark pink or white */
        div[data-testid="stChatInput"] input,
        div[data-testid="stChatInput"] textarea,
        .stChatInputContainer > div > div > input,
        .stChatInputContainer > div > div > textarea {
            color: var(--forte-dark-pink) !important;
            background-color: var(--forte-white) !important;
        }
        
        /* Chat input container wrapper */
        div[data-baseweb="input"] input {
            color: var(--forte-dark-pink) !important;
        }
        
        /* Title and captions in main area */
        h1, .stTitle {
            color: var(--forte-dark-pink) !important;
        }
        
        .stCaption {
            color: var(--forte-dark-pink) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    state: ConversationState = st.session_state.conversation_state
    manager: DialogManager = st.session_state.dialog_manager
    orchestrator: Orchestrator = st.session_state.orchestrator

    render_sidebar(state)

    st.title(PAGE_TITLE)
    mode = st.session_state.get("dialog_mode", "intelligent")
    mode_label = "Свободный диалог" if mode == "intelligent" else "Структурированная форма"
    st.caption(f"Диалоговый AI-аналитик: собираем требования и генерируем документы. Режим: {mode_label}")

    # Auto-fill toggle in sidebar (only for structured mode)
    if mode == "structured":
        if 'auto_fill_enabled' not in st.session_state:
            st.session_state.auto_fill_enabled = False
        
        auto_fill_enabled = st.sidebar.checkbox(
            "Автозаполнение (Selenium)",
            value=st.session_state.auto_fill_enabled,
            help="Включить автоматическое заполнение формы через Selenium",
            key="auto_fill_checkbox"
        )
        st.session_state.auto_fill_enabled = auto_fill_enabled
        
        # Auto-fill button
        if auto_fill_enabled and not manager.is_complete():
            if st.sidebar.button("▶️ Запустить автозаполнение", key="auto_fill_button"):
                from app.utils.auto_filler import fill_form_directly
                
                try:
                    # Fill form directly (no browser needed)
                    with st.spinner("Заполняю форму автоматически..."):
                        success = fill_form_directly(manager, state)
                        
                    if success:
                        # Rebuild chat history to show all Q&A
                        st.session_state.chat_history = []
                        temp_manager = DialogManager(state)
                        
                        # Build history by simulating the conversation
                        for field_key in FIELD_SEQUENCE:
                            if field_key in state.answers:
                                question = temp_manager.get_next_question()
                                if question:
                                    st.session_state.chat_history.append({
                                        "role": "assistant",
                                        "content": question.text,
                                        "field": question.field
                                    })
                                    st.session_state.chat_history.append({
                                        "role": "user",
                                        "content": state.answers[field_key]
                                    })
                                    try:
                                        temp_manager.accept_answer(state.answers[field_key])
                                    except:
                                        pass
                        
                        st.sidebar.success("Форма заполнена автоматически!")
                        st.rerun()
                    else:
                        st.sidebar.error("Ошибка автозаполнения")
                except Exception as e:
                    logger.error(f"Auto-fill error: {e}")
                    import traceback
                    traceback.print_exc()
                    st.sidebar.error(f"Ошибка: {e}")

    # Handle different dialog modes
    if mode == "intelligent":
        # Intelligent mode - free dialog
        intelligent_manager: IntelligentDialogManager = manager
        
        # Show greeting if first time
        if not st.session_state.greeting_shown and not st.session_state.chat_history:
            greeting = intelligent_manager.get_greeting()
            st.session_state.chat_history.append({"role": "assistant", "content": greeting})
            st.session_state.greeting_shown = True
            st.session_state.conversation_started = False  # Разговор еще не начат
        
        # Если разговор еще не начат, показываем только приветствие и кнопку
        if not st.session_state.conversation_started:
            # Показываем только приветствие
            if st.session_state.chat_history:
                with st.chat_message("assistant"):
                    st.markdown(st.session_state.chat_history[0]["content"])
            
            # Кнопка для начала разговора
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Начать разговор", key="start_conversation", use_container_width=True):
                    st.session_state.conversation_started = True
                    
                    # Задаем вопрос о первом незаполненном поле
                    missing_fields = state.get_missing_fields()
                    if missing_fields:
                        first_field = missing_fields[0]
                        field_label_text = field_label(first_field)
                        field_question = FIELD_METADATA[first_field]["question"]
                        first_question = f"\n\n**{field_label_text}**\n\n{field_question}"
                        st.session_state.chat_history.append({"role": "assistant", "content": first_question})
                    st.rerun()
        else:
            # Разговор начат - показываем весь чат
            # Display chat history
            for i, message in enumerate(st.session_state.chat_history):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
            # Handle user input
            analytical_mode = st.session_state.get("analytical_mode", False)
            chat_placeholder = "Задайте вопрос о проекте..." if analytical_mode else "Напишите о вашем проекте..."
            
            if prompt := st.chat_input(chat_placeholder):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                
                # Если аналитический режим - обрабатываем вопросы на основе данных
                if analytical_mode:
                    # НЕ сбрасываем документы в аналитическом режиме - они должны оставаться видимыми
                    with st.spinner("Анализирую вопрос на основе собранных данных..."):
                        try:
                            # Используем LLM для анализа вопроса на основе собранных данных
                            selected_model = st.session_state.get("selected_gemini_model", "gemini-2.5-flash")
                            llm_engine = create_engine(model_name=selected_model)
                            context = state.as_markdown_context()
                            
                            analysis_prompt = f"""Ты — опытный бизнес-аналитик. У тебя есть полная информация о проекте, собранная в ходе диалога с пользователем.

Собранные данные о проекте:
{context}

Вопрос пользователя: {prompt}

Проанализируй вопрос пользователя на основе собранных данных и дай развернутый, полезный ответ. 
Если в вопросе есть что-то, что не покрыто собранными данными, честно скажи об этом и предложи, как можно дополнить информацию.

Ответ должен быть:
- Конкретным и основанным на собранных данных
- Полезным для пользователя
- Написанным на русском языке
- Структурированным (используй списки, если уместно)
"""
                            response = llm_engine.ask(analysis_prompt)
                            message_data = {"role": "assistant", "content": response}
                            st.session_state.chat_history.append(message_data)
                        except Exception as e:
                            logger.error(f"Error in analytical mode: {e}")
                            import traceback
                            traceback.print_exc()
                            error_msg = "Извините, произошла ошибка при анализе. Попробуйте переформулировать вопрос."
                            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                else:
                    # Обычный режим сбора данных
                    st.session_state.documents = None
                    
                    # Process message through intelligent manager
                    with st.spinner("Анализирую..."):
                        try:
                            response, _ = intelligent_manager.process_message(prompt)
                            message_data = {"role": "assistant", "content": response}
                            st.session_state.chat_history.append(message_data)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            import traceback
                            traceback.print_exc()
                            error_msg = "Извините, произошла ошибка. Попробуйте переформулировать."
                            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                
                st.rerun()
    
    else:
        # Structured mode - original behavior or analytical mode
        analytical_mode = st.session_state.get("analytical_mode", False)
        
        if analytical_mode:
            # Аналитический режим для структурированной формы
            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Handle user input in analytical mode
            if prompt := st.chat_input("Задайте вопрос о проекте..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                
                # НЕ сбрасываем документы в аналитическом режиме
                with st.spinner("Анализирую вопрос на основе собранных данных..."):
                    try:
                        # Используем LLM для анализа вопроса на основе собранных данных
                        selected_model = st.session_state.get("selected_gemini_model", "gemini-2.5-flash")
                        llm_engine = create_engine(model_name=selected_model)
                        context = state.as_markdown_context()
                        
                        analysis_prompt = f"""Ты — опытный бизнес-аналитик. У тебя есть полная информация о проекте, собранная в ходе диалога с пользователем.

Собранные данные о проекте:
{context}

Вопрос пользователя: {prompt}

Проанализируй вопрос пользователя на основе собранных данных и дай развернутый, полезный ответ. 
Если в вопросе есть что-то, что не покрыто собранными данными, честно скажи об этом и предложи, как можно дополнить информацию.

Ответ должен быть:
- Конкретным и основанным на собранных данных
- Полезным для пользователя
- Написанным на русском языке
- Структурированным (используй списки, если уместно)
"""
                        response = llm_engine.ask(analysis_prompt)
                        message_data = {"role": "assistant", "content": response}
                        st.session_state.chat_history.append(message_data)
                    except Exception as e:
                        logger.error(f"Error in analytical mode: {e}")
                        import traceback
                        traceback.print_exc()
                        error_msg = "Извините, произошла ошибка при анализе. Попробуйте переформулировать вопрос."
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                
                st.rerun()
        else:
            # Обычный структурированный режим сбора данных
            structured_manager: DialogManager = manager
            enqueue_next_question()

            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Введите ответ"):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                try:
                    structured_manager.accept_answer(prompt)
                    st.session_state.documents = None
                    enqueue_next_question()
                    st.rerun()
                except ValueError as exc:
                    st.toast(str(exc))
                    st.rerun()

    # Check completion based on mode
    if mode == "intelligent":
        is_complete = state.is_complete()
    else:
        is_complete = manager.is_complete()
    
    # Показываем кнопки только если все поля заполнены
    if is_complete:
        st.divider()
        
        # Создаем контейнер для кнопок на одном уровне
        col1, col2 = st.columns(2)
        
        # Кнопка генерации или скачивания в первой колонке
        with col1:
            if not st.session_state.get("documents"):
                # Кнопка генерации отчета (показываем если документов еще нет)
                if st.button("Сгенерировать отчет", key="generate_docs", use_container_width=True):
                    try:
                        # Засекаем время начала
                        start_time = time.time()
                        
                        # Создаем контейнер для отображения времени
                        time_display = st.empty()
                        
                        # Функция для форматирования времени
                        def format_time(elapsed):
                            minutes = int(elapsed // 60)
                            seconds = int(elapsed % 60)
                            if minutes > 0:
                                return f"{minutes} мин {seconds} сек"
                            else:
                                return f"{seconds} сек"
                        
                        # Обновляем orchestrator с текущей выбранной моделью
                        selected_model = st.session_state.get("selected_gemini_model", "gemini-2.5-flash")
                        orchestrator = Orchestrator(model_name=selected_model)
                        
                        # Показываем спиннер и запускаем генерацию
                        # В Streamlit сложно обновлять UI во время блокирующей операции,
                        # поэтому время будет показано после завершения
                        with st.spinner("LLM генерирует артефакты..."):
                            bundle = orchestrator.generate_documents(state)
                        
                        # Засекаем время окончания и вычисляем общее время
                        end_time = time.time()
                        total_time = end_time - start_time
                        time_result = format_time(total_time)
                        
                        # Очищаем отображение времени и показываем результат
                        time_display.empty()
                        
                        st.session_state.documents = bundle
                        state.generated_bundle_id = "local"
                        
                        # Включаем аналитический режим
                        st.session_state.analytical_mode = True
                        
                        # Бот пишет сообщение в чат вместо toast
                        success_message = (
                            f"Отлично! Документы успешно сгенерированы за **{time_result}**.\n\n"
                            "Теперь я перешел в аналитический режим. Если у вас есть вопросы касательно этого проекта, "
                            "просто задайте их мне - я проанализирую собранные данные и дам развернутый ответ."
                        )
                        
                        if mode == "intelligent":
                            st.session_state.chat_history.append({"role": "assistant", "content": success_message})
                            st.rerun()
                        else:
                            # Structured mode - добавляем сообщение в историю
                            st.session_state.chat_history.append({"role": "assistant", "content": success_message})
                            st.rerun()
                        
                    except ValueError as exc:
                        logger.warning("Generation blocked: %s", exc)
                        st.error(str(exc))
                    except Exception as exc:
                        logger.error("Generation error: %s", exc)
                        st.error(f"Ошибка при генерации: {exc}")
            else:
                # Кнопка скачивания (показываем если документы уже сгенерированы)
                bundle = st.session_state.documents
                project_name = state.answers.get("goal", "Business Requirements Document")[:50]
                
                # Генерируем PDF данные один раз при загрузке страницы
                # Используем кэширование через session_state чтобы избежать повторной генерации
                if "pdf_data_cache" not in st.session_state or st.session_state.get("pdf_data_cache_id") != project_name:
                    st.session_state.pdf_data_cache = bundle.to_pdf(project_name=project_name)
                    st.session_state.pdf_data_cache_id = project_name
                
                st.download_button(
                    "Скачать общий PDF",
                    data=st.session_state.pdf_data_cache,
                    file_name="ai_ba_documents.pdf",
                    use_container_width=True,
                    key="download_full_pdf"
                )
    
    # Отображаем документы если они сгенерированы
    if st.session_state.get("documents"):
        bundle = st.session_state.documents
        st.divider()
        
        # Отображаем вкладки с документами
        render_document_tabs(bundle)


if __name__ == "__main__":
    main()
