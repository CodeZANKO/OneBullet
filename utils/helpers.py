import os
import subprocess
import shutil
import glob
import random

# A list of realistic modern User Agents for random selection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0"
]

def kill_chromedrivers() -> str:
    """Kills all running chromedriver processes on Windows."""
    try:
        output = subprocess.check_output("taskkill /F /IM chromedriver.exe /T", shell=True, stderr=subprocess.STDOUT)
        return output.decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        return f"No chromedriver processes found or error: {e.output.decode('utf-8', errors='ignore')}"

def kill_chrome_browsers() -> str:
    """Kills all running Chrome browser processes on Windows."""
    try:
        output = subprocess.check_output("taskkill /F /IM chrome.exe /T", shell=True, stderr=subprocess.STDOUT)
        return output.decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        return f"No Chrome processes found or error: {e.output.decode('utf-8', errors='ignore')}"

def delete_chrome_profiles(base_dir: str) -> str:
    """Deletes temporary Chrome profile folders inside the workspace directory."""
    if not os.path.exists(base_dir):
        return f"Directory {base_dir} does not exist."
    
    count = 0
    errors = []
    # Search for directories named chrome_profile_*
    pattern = os.path.join(base_dir, "chrome_profile_*")
    for profile_path in glob.glob(pattern):
        if os.path.isdir(profile_path):
            try:
                shutil.rmtree(profile_path)
                count += 1
            except Exception as e:
                errors.append(f"Failed to delete {os.path.basename(profile_path)}: {str(e)}")
                
    result = f"Successfully deleted {count} temporary Chrome profiles."
    if errors:
        result += "\nErrors:\n" + "\n".join(errors)
    return result

def get_random_user_agent() -> str:
    """Returns a random modern User Agent."""
    return random.choice(USER_AGENTS)

# Default Settings structure representing all required RuriLib and ZanBullet parameters
DEFAULT_SETTINGS = {
    "RuriLib": {
        "General": {
            "waitTime": 0,
            "requestsTimeout": 10,
            "maxHits": 0,
            "runnerBotsDisplayMode": "Everything",
            "enableBotLog": True,
            "saveLastResponseSource": False,
            "sendToCheckOnAbort": False,
            "hitsWebhookEnabled": False,
            "hitsWebhookUrl": "",
            "hitsWebhookUsername": ""
        },
        "Proxies": {
            "allowConcurrentUse": True,
            "neverBanProxies": False,
            "shuffleProxiesOnStart": True,
            "banLoopEvasion": 10,
            "dontReuseClearanceCookie": False,
            "reloadProxiesWhenAllBanned": True,
            "reloadInterval": 60,
            "reloadSource": "Manager",
            "globalBanKeys": "BAN\nBANNED\nACCESS DENIED\nUNAUTHORIZED",
            "globalRetryKeys": "RETRY\nRETRY_KEY\nRATE LIMIT"
        },
        "Captchas": {
            "captchaService": "TwoCaptcha",
            "apiKey": "",
            "bypassBalanceCheck": False,
            "responseTimeout": 120
        },
        "Selenium": {
            "browserType": "Chrome",
            "headlessMode": False,
            "drawMouseMovement": False,
            "chromeBinaryLocation": "",
            "firefoxBinaryLocation": "",
            "defaultTimeout": 30,
            "chromeExtensions": [],
            "useGpuAcceleration": False
        }
    },
    "OneBullet": {
        "General": {
            "automaticallySetRecommendedBots": True,
            "backupDatabaseDaily": True,
            "disableWarningOnQuit": False,
            "alwaysOnTop": False,
            "defaultAuthor": "One Bullet Development Team",
            "startingWindowWidth": 1280,
            "startingWindowHeight": 800,
            "enableLogging": True,
            "logToFile": False,
            "logBufferSize": 100,
            "ignoreWordlistName": False
        },
        "Sounds": {
            "enableSoundOnHit": True,
            "enableSoundOnCustom": False,
            "enableSoundOnToCheck": False,
            "soundFile": ""
        },
        "Sources": {
            "sourcesList": []
        },
        "Themes": {
            "colors": {
                "backgroundMain": "#121212",
                "backgroundSecondary": "#1e1e1e",
                "foregroundMain": "#ffffff",
                "foregroundGood": "#81c784",
                "foregroundBad": "#e57373",
                "foregroundCustom": "#64b5f6",
                "foregroundRetry": "#ffd54f",
                "foregroundToCheck": "#ffd54f",
                "foregroundMenuSel": "#2196f3"
            },
            "images": {
                "useImages": False,
                "opacity": 100,
                "backgroundImage": "",
                "logo": ""
            },
            "additional": {
                "allowTransparency": False,
                "enableSnow": False,
                "snowAmount": 50
            }
        }
    }
}

def merge_dicts(d1: dict, d2: dict) -> dict:
    """Deep merges d2 into d1 recursively."""
    result = d1.copy()
    for k, v in d2.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = merge_dicts(result[k], v)
        else:
            result[k] = v
    return result

def load_settings() -> dict:
    """Loads settings from settings.json and merges them with defaults."""
    import json
    path = os.path.join(os.getcwd(), "settings.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Map old ZanBullet configuration to OneBullet key for backward compatibility
                if "ZanBullet" in data and "OneBullet" not in data:
                    data["OneBullet"] = data["ZanBullet"]
                return merge_dicts(DEFAULT_SETTINGS, data)
        except Exception:
            pass
    return merge_dicts(DEFAULT_SETTINGS, {})

def save_settings(data: dict):
    """Saves settings to settings.json."""
    import json
    path = os.path.join(os.getcwd(), "settings.json")
    try:
        # Save both or map OneBullet to ZanBullet for backward compatibility
        if "OneBullet" in data:
            data["ZanBullet"] = data["OneBullet"]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def generate_stylesheet(colors: dict) -> str:
    """Generates the main stylesheet dynamically based on customization color settings."""
    bg_main = colors.get("backgroundMain", "#0b0f19")
    bg_sec = colors.get("backgroundSecondary", "#151b27")
    fg_main = colors.get("foregroundMain", "#ffffff")
    fg_good = colors.get("foregroundGood", "#00ff88") # neon green accent
    fg_bad = colors.get("foregroundBad", "#ff1744") # neon red accent
    fg_menu_sel = colors.get("foregroundMenuSel", "#00e5ff") # neon cyan accent
    
    return f"""
/* Global Window & Dialog Backgrounds */
QMainWindow, QDialog {{
    background-color: {bg_main};
}}

/* Generic Widget styles (No background-color here to avoid child inheritance leakage) */
QWidget {{
    color: {fg_main};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif;
    font-size: 13px;
}}

/* Ensure labels have a clean transparent background */
QLabel {{
    background-color: transparent;
    color: {fg_main};
}}

/* Sidebar Container */
QFrame#Sidebar {{
    background-color: #06090f;
    border-right: 1px solid #1c273a;
}}

/* Sidebar Title */
QLabel#SidebarTitle {{
    font-size: 16px;
    font-weight: 800;
    color: {fg_menu_sel};
    padding: 20px 10px;
    letter-spacing: 1px;
    border-bottom: 1px solid #1c273a;
    background-color: transparent;
}}

/* Sidebar Buttons */
QPushButton.SidebarBtn {{
    background-color: transparent;
    color: #90a4ae;
    border: none;
    border-left: 4px solid transparent;
    padding: 14px 20px;
    font-size: 13px;
    font-weight: bold;
    text-align: left;
    border-radius: 0px;
}}

QPushButton.SidebarBtn:hover {{
    background-color: #0f1622;
    color: #ffffff;
}}

QPushButton.SidebarBtn[active="true"] {{
    background-color: #111a2e;
    color: {fg_menu_sel};
    border-left: 4px solid {fg_menu_sel};
}}

/* Containment Card Style (Modern rounded frames) */
QFrame#ContainmentCard, QFrame#runnerCard, QFrame#TableCard, QFrame#AboutCard, QFrame#DetailsCard, QFrame#RunnerCard {{
    background-color: {bg_sec};
    border: 1px solid #1c273a;
    border-radius: 8px;
}}

/* Status Bar */
QStatusBar {{
    background-color: #06090f;
    color: #90a4ae;
    border-top: 1px solid #1c273a;
}}

/* Tab Widget Customization */
QTabWidget::pane {{
    border: 1px solid #1c273a;
    background-color: {bg_main};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: {bg_sec};
    color: #90a4ae;
    border: 1px solid #1c273a;
    border-bottom: none;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
}}

QTabBar::tab:hover {{
    background-color: #1e283d;
    color: #ffffff;
}}

QTabBar::tab:selected {{
    background-color: {bg_main};
    color: {fg_menu_sel};
    border-bottom: 2px solid {fg_menu_sel};
}}

/* Group Box */
QGroupBox {{
    border: 1px solid #1c273a;
    border-radius: 8px;
    margin-top: 15px;
    padding: 15px;
    font-weight: bold;
    font-size: 13px;
    color: #ffffff;
    background-color: {bg_sec};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 8px;
    color: {fg_menu_sel};
    background-color: transparent;
}}

/* Input Fields & Text Edits */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background-color: #0b0f19;
    border: 1px solid #1c273a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    selection-background-color: {fg_menu_sel};
    selection-color: #000000;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {fg_menu_sel};
    background-color: #0e1422;
}}

/* Buttons */
QPushButton {{
    background-color: #151b27;
    color: #ffffff;
    border: 1px solid #232f44;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: #1e283d;
    border-color: {fg_menu_sel};
}}

QPushButton:pressed {{
    background-color: {fg_menu_sel};
    color: #080b11;
}}

QPushButton:disabled {{
    background-color: #0a0e16;
    color: #4b586e;
    border-color: #0a0e16;
}}

/* Tables */
QTableWidget {{
    background-color: #0b0f19;
    gridline-color: #1c273a;
    border: 1px solid #1c273a;
    border-radius: 6px;
    selection-background-color: #111a2e;
    selection-color: {fg_menu_sel};
}}

QTableWidget::item {{
    padding: 8px;
}}

QHeaderView::section {{
    background-color: #070b12;
    color: #90a4ae;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #1c273a;
    font-weight: bold;
}}

/* Checkboxes and Radio Buttons styling */
QCheckBox, QRadioButton {{
    background-color: transparent;
    color: {fg_main};
    padding: 4px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    background-color: #0b0f19;
    border: 1px solid #1c273a;
    border-radius: 3px;
}}

QRadioButton::indicator {{
    border-radius: 8px;
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {fg_menu_sel};
}}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {fg_menu_sel};
    border-color: {fg_menu_sel};
}}

/* Lists */
QListWidget {{
    background-color: #0b0f19;
    border: 1px solid #1c273a;
    border-radius: 6px;
}}

QListWidget::item {{
    padding: 10px;
    border-bottom: 1px solid #0d121c;
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: #0f1622;
}}

QListWidget::item:selected {{
    background-color: #111a2e;
    color: {fg_menu_sel};
    font-weight: bold;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #1c273a;
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {fg_menu_sel};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}

QScrollBar:horizontal {{
    border: none;
    background: transparent;
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: #1c273a;
    min-width: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {fg_menu_sel};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
}}
"""



def parse_wordlist_line(line: str, wordlist_type: str, wordlist_format: str = None) -> dict:
    """
    Parses a single line from a wordlist based on its Wordlist Type,
    returning a dictionary of variable mappings (without < > wrappers).
    """
    import re
    variables = {"LINE": line}
    wtype = (wordlist_type or "Default").strip().lower()
    
    # Custom format mapping
    if wtype == "custom" and wordlist_format:
        tokens = re.split(r'(<[^>]+>)', wordlist_format)
        regex_parts = []
        tag_names = []
        for i, token in enumerate(tokens):
            if token.startswith('<') and token.endswith('>'):
                var_name = token[1:-1]
                tag_names.append(var_name)
                # Determine separator to match up to
                next_token = tokens[i+1] if i + 1 < len(tokens) else ""
                if next_token:
                    sep = re.escape(next_token[0])
                    regex_parts.append(f"([^{sep}]*)")
                else:
                    regex_parts.append(f"(.*)")
            else:
                regex_parts.append(re.escape(token))
                
        pattern_regex = "^" + "".join(regex_parts) + "$"
        try:
            match = re.match(pattern_regex, line)
            if match:
                for var_name, val in zip(tag_names, match.groups()):
                    variables[var_name] = val
        except Exception:
            pass

        # Maintain compatibility aliases
        if "EMAIL" in variables and "USER" not in variables:
            variables["USER"] = variables["EMAIL"]
        if "USER" in variables and "EMAIL" not in variables:
            variables["EMAIL"] = variables["USER"]
        if "PASSWORD" in variables and "PASS" not in variables:
            variables["PASS"] = variables["PASSWORD"]
        if "PASS" in variables and "PASSWORD" not in variables:
            variables["PASSWORD"] = variables["PASS"]
            
        return variables

    # Credentials / Email / Default: Expects "input:password" format.
    # Split by the last ':' or ';' character.
    # Assign left side to <USER> or <EMAIL> and right side to <PASSWORD>.
    if wtype in ["credentials", "email", "default"]:
        idx_colon = line.rfind(':')
        idx_semi = line.rfind(';')
        idx = max(idx_colon, idx_semi)
        if idx != -1:
            left = line[:idx]
            right = line[idx+1:]
        else:
            left = line
            right = ""
        variables["USER"] = left
        variables["EMAIL"] = left
        variables["PASSWORD"] = right
        # Also maintain compatibility for legacy code using PASS
        variables["PASS"] = right
        
    # Card / CreditCard: Expects "number|expiry|cvv" format.
    # Split by '|' or ':'. Assign elements respectively to <CNUM>, <EXP>, and <CVV>.
    elif wtype in ["card", "creditcard"]:
        parts = re.split(r'[|:]', line)
        cnum = parts[0] if len(parts) > 0 else ""
        exp = parts[1] if len(parts) > 1 else ""
        cvv = parts[2] if len(parts) > 2 else ""
        variables["CNUM"] = cnum
        variables["EXP"] = exp
        variables["CVV"] = cvv
        
    # Numeric: Expects pure numbers or IDs. Assign the whole line to <NUM> or <PNUM> (Phone Number).
    elif wtype in ["numeric"]:
        variables["NUM"] = line
        variables["PNUM"] = line
        
    # URLs: Expects links. Assign the full line to <URL>.
    elif wtype in ["urls"]:
        variables["URL"] = line
        
    # Extended (Address / Info): Expects comma/pipe-separated values.
    # Map them dynamically to <ADDRESS>, <COUNTRY>, <ZIP>, etc.
    elif wtype in ["extended"]:
        parts = re.split(r'[,|]', line)
        keys = ["ADDRESS", "COUNTRY", "ZIP", "CITY", "STATE", "FIRSTNAME", "LASTNAME", "PHONE"]
        for idx, part in enumerate(parts):
            val = part.strip()
            if idx < len(keys):
                variables[keys[idx]] = val
            # Also populate generic index-based EXTENDED tags
            variables[f"EXTENDED_{idx}"] = val
            
    else:
        # Fallback to default
        idx_colon = line.rfind(':')
        idx_semi = line.rfind(';')
        idx = max(idx_colon, idx_semi)
        if idx != -1:
            left = line[:idx]
            right = line[idx+1:]
        else:
            left = line
            right = ""
        variables["USER"] = left
        variables["EMAIL"] = left
        variables["PASSWORD"] = right
        variables["PASS"] = right

    return variables


def interpolate_value(val, variables: dict):
    """
    Recursively replaces placeholder tags like <TAG> in any data structure
    with the values in the variables dictionary.
    """
    if isinstance(val, str):
        # Let's expand variables dict to include case variations dynamically
        expanded_vars = {}
        for k, v in variables.items():
            expanded_vars[k] = v
            clean_k = k.strip("<>")
            expanded_vars[clean_k.upper()] = v
            expanded_vars[clean_k.lower()] = v
            expanded_vars[f"<{clean_k.upper()}>"] = v
            expanded_vars[f"<{clean_k.lower()}>"] = v
            
        # Sort keys by length in descending order to avoid partial replacement issues (e.g. USERNAME vs USER)
        sorted_keys = sorted(expanded_vars.keys(), key=len, reverse=True)
        for k in sorted_keys:
            v = expanded_vars[k]
            tag = k if (k.startswith("<") and k.endswith(">")) else f"<{k}>"
            val = val.replace(tag, str(v))
        return val
    elif isinstance(val, dict):
        return {k: interpolate_value(v, variables) for k, v in val.items()}
    elif isinstance(val, list):
        return [interpolate_value(item, variables) for item in val]
    return val


def get_resource_path(relative_path: str) -> str:
    """Gets the absolute path to a resource, supporting both dev environments and PyInstaller."""
    import sys
    try:
        # PyInstaller creates a temporary folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Fall back to the root of the project (parent of utils folder)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)



