"""Auto-fill form using Selenium for testing purposes."""

from __future__ import annotations

import random
import time
from pathlib import Path
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from app.utils.logger import logger
from app.utils.state import FIELD_SEQUENCE


def load_random_scenario() -> Optional[List[str]]:
    """
    Load random scenario from scenarios folder.
    
    Returns:
        List of 14 answers (one per line) or None if no scenarios found
    """
    scenarios_dir = Path(__file__).parent.parent.parent / "scenarios"
    
    if not scenarios_dir.exists():
        logger.error(f"Scenarios directory not found: {scenarios_dir}")
        return None
    
    # Find all .txt files
    scenario_files = list(scenarios_dir.glob("*.txt"))
    
    if not scenario_files:
        logger.error(f"No scenario files found in {scenarios_dir}")
        return None
    
    # Pick random scenario
    scenario_file = random.choice(scenario_files)
    logger.info(f"Loading scenario: {scenario_file.name}")
    
    # Read scenario (14 lines, one per field)
    try:
        with open(scenario_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if len(lines) < 14:
            logger.warning(f"Scenario {scenario_file.name} has only {len(lines)} lines, expected 14")
            return None
        
        return lines[:14]
    except Exception as e:
        logger.error(f"Error reading scenario {scenario_file}: {e}")
        return None


def create_driver(headless: bool = True):
    """Create and configure Chrome WebDriver."""
    import os
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Find Chrome binary path on macOS
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
    ]
    
    chrome_binary = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_binary = path
            break
    
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
        logger.info(f"Using Chrome at: {chrome_binary}")
    else:
        logger.warning("Chrome binary not found, using default")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def fill_form_directly(manager, state):
    """
    Fill form directly through DialogManager (no browser needed).
    
    Args:
        manager: DialogManager instance
        state: ConversationState instance
    """
    answers = load_random_scenario()
    if not answers:
        logger.error("Failed to load scenario")
        return False
    
    if len(answers) != len(FIELD_SEQUENCE):
        logger.error(f"Scenario has {len(answers)} answers, expected {len(FIELD_SEQUENCE)}")
        return False
    
    logger.info(f"Filling form directly with {len(answers)} answers")
    
    # Reset state first
    state.answers.clear()
    
    # Fill each field directly through manager
    for i, (field_key, answer) in enumerate(zip(FIELD_SEQUENCE, answers), 1):
        logger.info(f"Filling field {i}/14: {field_key} = {answer[:50]}...")
        try:
            manager.accept_answer(answer)
        except ValueError as e:
            logger.warning(f"Error accepting answer for {field_key}: {e}")
            # Set directly if validation fails
            state.answers[field_key] = answer
    
    logger.info("Direct form fill completed!")
    return True


def auto_fill_form(url: str = "http://localhost:8501", delay: float = 1.0):
    """
    Auto-fill the form using Selenium.
    
    Args:
        url: Streamlit app URL
        delay: Delay between actions in seconds
    """
    # Load random scenario
    answers = load_random_scenario()
    if not answers:
        logger.error("Failed to load scenario")
        return False
    
    logger.info(f"Starting auto-fill with {len(answers)} answers")
    
    driver = None
    try:
        # Create driver
        driver = create_driver(headless=False)  # Show browser so user can see
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Fill each field
        for i, answer in enumerate(answers):
            logger.info(f"Filling field {i+1}/14: {answer[:50]}...")
            
            try:
                # Wait for chat input to be visible
                wait = WebDriverWait(driver, 10)
                chat_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[data-testid="stChatInputTextInput"]'))
                )
                
                # Clear and type answer
                chat_input.clear()
                chat_input.send_keys(answer)
                time.sleep(delay)
                
                # Press Enter to submit
                chat_input.send_keys(Keys.RETURN)
                time.sleep(delay + 1)  # Wait for response
                
            except Exception as e:
                logger.error(f"Error filling field {i+1}: {e}")
                continue
        
        logger.info("Auto-fill completed!")
        
        # Wait a bit before closing
        time.sleep(5)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in auto-fill: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Test auto-fill
    print("Тестирование автозаполнения...")
    auto_fill_form()


__all__ = ["auto_fill_form", "load_random_scenario"]

