import os
import time
import queue
import random
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from engine.selenium_engine import create_proxy_auth_extension


class RunnerEngine(QObject):
    """
    Manages multi-threaded execution of web automation configs
    against a Wordlist of inputs, rotating proxies in real-time.
    """
    progress_signal = pyqtSignal(int, int) # completed, total
    hit_signal = pyqtSignal()
    custom_signal = pyqtSignal()
    tocheck_signal = pyqtSignal()
    cpm_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    hit_found_signal = pyqtSignal(str, str, str, str) # line, status, variables, proxy
    html_signal = pyqtSignal(str) # page source HTML on hit
    finished_signal = pyqtSignal()
    checked_line_signal = pyqtSignal(dict)
    
    def __init__(self, blocks, settings, wordlist_lines, proxies, bots_count, wordlist_type="Default"):
        super().__init__()
        self.blocks = blocks
        self.settings = settings
        self.wordlist_lines = wordlist_lines
        self.proxies = proxies
        self.bots_count = bots_count
        self.wordlist_type = wordlist_type
        
        # Load global settings from settings.json
        from utils.helpers import load_settings
        self.global_settings = load_settings()
        
        self.queue = queue.Queue()
        for line in wordlist_lines:
            self.queue.put(line)
            
        self.is_running = False
        self.hits = 0
        self.custom = 0
        self.tocheck = 0
        self.bad = 0
        self.banned = 0
        self.retries = 0
        self.completed = 0
        self.total = len(wordlist_lines)
        
        self.threads = []
        self.start_time = None
        
    def start(self):
        self.is_running = True
        self.start_time = time.time()
        self.threads = []
        
        # Shuffle proxies if requested in RuriLib Proxies settings
        if self.global_settings.get("RuriLib", {}).get("Proxies", {}).get("shuffleProxiesOnStart", True):
            random.shuffle(self.proxies)
            
        # Start CPM counter
        self.cpm_thread = threading.Thread(target=self.cpm_loop, daemon=True)
        self.cpm_thread.start()
        
        # Start worker threads
        for i in range(min(self.bots_count, self.total)):
            t = threading.Thread(target=self.worker_loop, name=f"RunnerWorker-{i}", daemon=True)
            self.threads.append(t)
            t.start()
            
    def stop(self):
        self.is_running = False
        self.log_signal.emit("[RUNNER] Stop requested. Waiting for threads to close browsers...")
        
    def cpm_loop(self):
        while self.is_running:
            time.sleep(2)
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                cpm = int((self.completed / elapsed) * 60)
                self.cpm_signal.emit(cpm)
                
    def worker_loop(self):
        # Create isolated browser instance per worker thread to avoid start/stop overhead
        driver = None
        active_proxy = None
        import datetime
        import requests
        import random
        
        # Initialize http session per thread for Requests Mode
        http_session = requests.Session()
        threading.current_thread().http_session = http_session
        
        use_sel = self.settings.get("use_selenium", True)
        
        while self.is_running:
            try:
                line = self.queue.get_nowait()
            except queue.Empty:
                break
                
            # Parse line variables based on wordlist type
            from utils.helpers import parse_wordlist_line
            variables = parse_wordlist_line(line, self.wordlist_type)
            
            # Create a thread-safe dictionary/map for each active bot thread
            ThreadVariables = {}
            for k, v in variables.items():
                ThreadVariables[k] = v
                clean_k = k.strip("<>")
                ThreadVariables[clean_k.upper()] = v
                ThreadVariables[clean_k.lower()] = v
                ThreadVariables[f"<{clean_k.upper()}>"] = v
                ThreadVariables[f"<{clean_k.lower()}>"] = v
            
            threading.current_thread().ThreadVariables = ThreadVariables
            threading.current_thread().Captures = {}
            # Pass the active proxy reference to the current thread so request execution can read it
            threading.current_thread().active_proxy = active_proxy
            
            success = False
            status = "FAIL"
            status_desc = ""
            active_proxy_str = f"{active_proxy['host']}:{active_proxy['port']}" if active_proxy else "None"
            
            try:
                # Initialize driver if not active and use_selenium is True
                if use_sel:
                    if driver is None:
                        driver, active_proxy = self.init_worker_driver()
                        if active_proxy:
                            active_proxy_str = f"{active_proxy['host']}:{active_proxy['port']}"
                            threading.current_thread().active_proxy = active_proxy
                        if driver is None:
                            raise RuntimeError("Failed to start webdriver for worker thread.")
                    # Clear session state for next line checking
                    if driver:
                        try:
                            driver.delete_all_cookies()
                        except Exception:
                            pass
                else:
                    driver = None
                    if self.settings.get("use_proxies", False) and self.proxies:
                        if active_proxy is None or active_proxy.get("status") == "Failed":
                            working_proxies = [p for p in self.proxies if p.get("status") != "Failed"]
                            if not working_proxies:
                                working_proxies = self.proxies
                            active_proxy = random.choice(working_proxies)
                            active_proxy_str = f"{active_proxy['host']}:{active_proxy['port']}"
                            threading.current_thread().active_proxy = active_proxy
                    else:
                        active_proxy = None
                        active_proxy_str = "None"
                        threading.current_thread().active_proxy = None
                
                # Execute blocks sequence
                self.execute_sequence(driver, variables, active_proxy)
                success = True
                status = "SUCCESS"
            except AssertionError as ae:
                msg = str(ae)
                if msg.startswith("FAIL:"):
                    status = "FAIL"
                    status_desc = msg.replace("FAIL:", "").strip()
                elif msg.startswith("BAN:"):
                    status = "BAN"
                    status_desc = msg.replace("BAN:", "").strip()
                elif msg.startswith("RETRY:"):
                    status = "RETRY"
                    status_desc = msg.replace("RETRY:", "").strip()
                elif msg.startswith("CUSTOM:"):
                    status = "CUSTOM"
                    status_desc = msg.replace("CUSTOM:", "").strip()
                else:
                    status = "FAIL"
                    status_desc = msg
                self.log_signal.emit(f"[STATUS] {status} for '{line}': {status_desc}")
            except Exception as e:
                status = "ERROR"
                status_desc = str(e)
                self.log_signal.emit(f"[ERROR] Worker failed checking '{line}': {status_desc}")
                # If driver crashed, clean it up so next iteration spawns a fresh one
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = None
                    active_proxy = None
                    threading.current_thread().active_proxy = None

            # Get captured variables if any - strictly routing only captures
            curr_thread = threading.current_thread()
            captures = getattr(curr_thread, "Captures", {})
            save_empty = self.settings.get("save_empty_captures", False)
            capture_parts = []
            for k, v in captures.items():
                v_str = str(v).strip() if v is not None else ""
                if not save_empty and not v_str:
                    continue
                capture_parts.append(f"{k} = {v_str}")
            capture_str = " | ".join(capture_parts) if capture_parts else ""
            
            
            # Record result
            if status == "SUCCESS":
                self.hits += 1
                self.hit_signal.emit()
                self.hit_found_signal.emit(line, "SUCCESS", capture_str, active_proxy_str)
                if driver:
                    try:
                        self.html_signal.emit(driver.page_source)
                    except Exception:
                        pass
                else:
                    # Emitting the raw response body string from context variables
                    source_content = ThreadVariables.get("<SOURCE>", ThreadVariables.get("SOURCE", ""))
                    self.html_signal.emit(source_content)
            elif status == "CUSTOM":
                self.custom += 1
                self.custom_signal.emit()
                self.hit_found_signal.emit(line, "CUSTOM", capture_str, active_proxy_str)
            elif status == "FAIL":
                self.bad += 1
            elif status == "BAN":
                self.banned += 1
                if active_proxy:
                    active_proxy['status'] = "Failed" # Mark proxy as banned
            elif status == "RETRY":
                self.retries += 1
                self.queue.put(line)
            else: # ERROR or fallback
                self.tocheck += 1
                self.tocheck_signal.emit()
                
            if status != "RETRY":
                self.completed += 1
                self.progress_signal.emit(self.completed, self.total)

            self.checked_line_signal.emit({
                "id": self.completed,
                "line": line,
                "proxy": active_proxy_str,
                "status": status,
                "capture": capture_str,
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            })
                
        # Cleanup driver at the end of thread
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
                
        # Close http session per thread
        try:
            http_session.close()
        except Exception:
            pass
                
        # Check if all workers done
        active = any(t.is_alive() for t in self.threads if t != threading.current_thread())
        if not active:
            self.is_running = False
            self.finished_signal.emit()

    def init_worker_driver(self) -> tuple:
        from selenium import webdriver
        
        # Load parameters dynamically from global settings
        rl_sel = self.global_settings.get("RuriLib", {}).get("Selenium", {})
        browser_type = rl_sel.get("browserType", "Chrome")
        headless = self.settings.get("headless", False) or rl_sel.get("headlessMode", False)
        default_timeout = rl_sel.get("defaultTimeout", 30)
        
        active_proxy = None
        
        use_gpu = rl_sel.get("useGpuAcceleration", False)
        common_args = ["--disable-dev-shm-usage", "--no-sandbox", "--log-level=3"]
        if use_gpu:
            common_args.extend(["--enable-gpu", "--ignore-gpu-blocklist"])
        else:
            common_args.append("--disable-gpu")
            
        if self.settings.get("disable_notifications", True):
            common_args.extend(["--disable-notifications", "--disable-popup-blocking"])
            
        ua = self.settings.get("user_agent", "").strip()
        if self.settings.get("use_random_ua", False):
            from utils.helpers import get_random_user_agent
            ua = get_random_user_agent()

        # Setup proxy details
        proxy_arg = None
        auth_ext_path = None
        if self.settings.get("use_proxies", False) and self.proxies:
            active_proxy = random.choice(self.proxies)
            proxy = active_proxy
            
            if proxy.get('username') and proxy.get('password'):
                temp_dir = os.path.join(os.getcwd(), "temp_chrome_profiles")
                os.makedirs(temp_dir, exist_ok=True)
                auth_ext_path = create_proxy_auth_extension(
                    proxy['host'], proxy['port'], proxy['username'], proxy['password'], temp_dir
                )
            else:
                proxy_str = f"{proxy['host']}:{proxy['port']}"
                if proxy['type'].lower() == 'socks5':
                    proxy_arg = f"--proxy-server=socks5://{proxy_str}"
                else:
                    proxy_arg = f"--proxy-server=http://{proxy_str}"

        # Initialize Browser Instance
        try:
            if browser_type == "Chrome":
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                options = webdriver.ChromeOptions()
                
                if headless:
                    options.add_argument("--headless=new")
                    options.add_argument("--window-size=1920,1080")
                
                for arg in common_args:
                    options.add_argument(arg)
                
                if ua:
                    options.add_argument(f"user-agent={ua}")
                
                custom_args = self.settings.get("custom_args", "").strip()
                if custom_args:
                    for arg in custom_args.split():
                        options.add_argument(arg)
                
                if proxy_arg:
                    options.add_argument(proxy_arg)
                
                if auth_ext_path:
                    options.add_extension(auth_ext_path)
                
                # Chrome extensions from settings.json
                for ext in rl_sel.get("chromeExtensions", []):
                    if os.path.exists(ext):
                        options.add_extension(ext)
                
                chrome_bin = rl_sel.get("chromeBinaryLocation", "")
                if chrome_bin:
                    options.binary_location = chrome_bin
                
                profile_dir = os.path.join(os.getcwd(), "temp_chrome_profiles", f"chrome_profile_worker_{random.randint(100000, 999999)}")
                options.add_argument(f"--user-data-dir={profile_dir}")
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)

            elif browser_type == "Firefox":
                from selenium.webdriver.firefox.service import Service
                from webdriver_manager.firefox import GeckoDriverManager
                options = webdriver.FirefoxOptions()
                
                if headless:
                    options.add_argument("--headless")
                
                if ua:
                    options.set_preference("general.useragent.override", ua)
                
                firefox_bin = rl_sel.get("firefoxBinaryLocation", "")
                if firefox_bin:
                    options.binary_location = firefox_bin
                
                # Apply Proxy to Firefox
                if self.settings.get("use_proxies", False) and active_proxy:
                    from selenium.webdriver.common.proxy import Proxy, ProxyType
                    p = active_proxy
                    firefox_proxy = Proxy()
                    firefox_proxy.proxy_type = ProxyType.MANUAL
                    p_str = f"{p['host']}:{p['port']}"
                    if p['type'].lower() == 'socks5':
                        firefox_proxy.socks_proxy = p_str
                    else:
                        firefox_proxy.http_proxy = p_str
                        firefox_proxy.ssl_proxy = p_str
                    options.proxy = firefox_proxy
                
                service = Service(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)

            elif browser_type == "Edge":
                from selenium.webdriver.edge.service import Service
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                options = webdriver.EdgeOptions()
                
                if headless:
                    options.add_argument("--headless=new")
                    options.add_argument("--window-size=1920,1080")
                
                for arg in common_args:
                    options.add_argument(arg)
                
                if ua:
                    options.add_argument(f"user-agent={ua}")
                
                if proxy_arg:
                    options.add_argument(proxy_arg)
                
                service = Service(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)

            else:  # InternetExplorer
                from selenium.webdriver.ie.service import Service
                from webdriver_manager.microsoft import IEDriverManager
                options = webdriver.IeOptions()
                service = Service(IEDriverManager().install())
                driver = webdriver.Ie(service=service, options=options)
            
            # Apply loaded default timeouts
            driver.set_page_load_timeout(default_timeout)
            driver.implicitly_wait(min(10, default_timeout))
            
            return driver, active_proxy
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Worker failed launching WebDriver: {str(e)}")
            return None, None

    def interpolate(self, text: str, variables: dict) -> str:
        if not isinstance(text, str):
            return text
        t_vars = getattr(threading.current_thread(), "ThreadVariables", {})
        variables_to_use = t_vars if t_vars else variables
        
        expanded_vars = {}
        for k, v in variables_to_use.items():
            expanded_vars[k] = v
            clean_k = k.strip("<>")
            expanded_vars[clean_k.upper()] = v
            expanded_vars[clean_k.lower()] = v
            expanded_vars[f"<{clean_k.upper()}>"] = v
            expanded_vars[f"<{clean_k.lower()}>"] = v
            
        # Sort keys to prevent partial matches
        sorted_keys = sorted(expanded_vars.keys(), key=len, reverse=True)
        for k in sorted_keys:
            v = expanded_vars[k]
            tag = k if (k.startswith("<") and k.endswith(">")) else f"<{k}>"
            text = text.replace(tag, str(v))
        return text

    def execute_sequence(self, driver, variables: dict, active_proxy: dict):
        import copy
        import threading
        from utils.helpers import interpolate_value
        
        # Access or initialize ThreadVariables
        t_vars = getattr(threading.current_thread(), "ThreadVariables", None)
        if t_vars is None:
            t_vars = {}
            for k, v in variables.items():
                t_vars[k] = v
                clean_k = k.strip("<>")
                t_vars[clean_k.upper()] = v
                t_vars[clean_k.lower()] = v
                t_vars[f"<{clean_k.upper()}>"] = v
                t_vars[f"<{clean_k.lower()}>"] = v
            threading.current_thread().ThreadVariables = t_vars
            
        def set_variable(name, val):
            variables[name] = val
            t_vars[name] = val
            if name.startswith("<") and name.endswith(">"):
                t_vars[name[1:-1]] = val
            else:
                t_vars[f"<{name}>"] = val

        for block in self.blocks:
            if not self.is_running:
                break
                
            # Apply RuriLib General Wait Time (in ms)
            wait_ms = self.global_settings.get("RuriLib", {}).get("General", {}).get("waitTime", 0)
            if wait_ms > 0:
                time.sleep(wait_ms / 1000.0)
                
            # Deep clone and interpolate the block properties before execution
            interpolated_block = interpolate_value(copy.deepcopy(block), t_vars)
            block_type = interpolated_block.get("type", "")
            
            if block_type == "BROWSER ACTION":
                action = interpolated_block.get("action", "Start Browser")
                if action == "Refresh":
                    driver.refresh()
                elif action == "Go Back":
                    driver.back()
                elif action == "Go Forward":
                    driver.forward()
                elif action == "ClearCookies":
                    driver.delete_all_cookies()
                elif action == "Screenshot":
                    os.makedirs("screenshots", exist_ok=True)
                    filename = f"screenshots/screenshot_{int(time.time())}.png"
                    driver.save_screenshot(filename)
                elif action == "ScrollToTop":
                    driver.execute_script("window.scrollTo(0, 0);")
                elif action == "ScrollToBottom":
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                elif action == "Scroll":
                    driver.execute_script("window.scrollBy(0, 250);")
                elif action == "OpenNewTab":
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])
                    
            elif block_type == "NAVIGATE":
                url = interpolated_block.get("url", "")
                timeout = int(interpolated_block.get("timeout", 60))
                ban_on_timeout = interpolated_block.get("ban_on_timeout", False)
                
                if not url:
                    raise ValueError("URL is empty.")
                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url
                
                driver.set_page_load_timeout(timeout)
                try:
                    driver.get(url)
                except TimeoutException as e:
                    self.log_signal.emit(f"[WARNING] Page load timed out after {timeout} seconds.")
                    if ban_on_timeout and active_proxy:
                        never_ban = self.global_settings.get("RuriLib", {}).get("Proxies", {}).get("neverBanProxies", False)
                        if never_ban:
                            self.log_signal.emit(f"[INFO] Skipping proxy ban due to 'Never Ban Proxies' setting.")
                        else:
                            self.log_signal.emit(f"[BAN] Banning proxy due to page timeout: {active_proxy['host']}")
                            active_proxy['status'] = "Failed" # Mark proxy as banned
                    raise e
                
            elif block_type == "ELEMENT ACTION":
                selector_type = interpolated_block.get("selector_type", "XPATH")
                selector = interpolated_block.get("selector", "")
                action = interpolated_block.get("action", "Click")
                value = interpolated_block.get("value", "")
                var_name = interpolated_block.get("variable_name", "")
                
                index = int(interpolated_block.get("index", 0))
                recursive = interpolated_block.get("recursive", False)
                is_capture = interpolated_block.get("is_capture", False)
                
                by_map = {
                    "XPATH": By.XPATH,
                    "ID": By.ID,
                    "CLASS_NAME": By.CLASS_NAME,
                    "CSS_SELECTOR": By.CSS_SELECTOR,
                    "NAME": By.NAME,
                    "TAG_NAME": By.TAG_NAME,
                    "LINK_TEXT": By.LINK_TEXT
                }
                by_strategy = by_map.get(selector_type, By.XPATH)
                
                if action == "Wait for Element":
                    wait_time = 10
                    try:
                        wait_time = int(value) if value.isdigit() else 10
                    except:
                        pass
                    WebDriverWait(driver, wait_time).until(
                        EC.presence_of_element_located((by_strategy, selector))
                    )
                    continue
                    
                rl_sel = self.global_settings.get("RuriLib", {}).get("Selenium", {})
                default_timeout = rl_sel.get("defaultTimeout", 30)
                draw_mouse = rl_sel.get("drawMouseMovement", False)
 
                WebDriverWait(driver, default_timeout).until(
                    EC.presence_of_element_located((by_strategy, selector))
                )
                elements = driver.find_elements(by_strategy, selector)
                
                if not elements:
                    raise ValueError(f"No elements found matching selector: {selector}")
                    
                if recursive:
                    extracted_texts = []
                    for el in elements:
                        if action == "Click":
                            if draw_mouse:
                                try:
                                    from selenium.webdriver.common.action_chains import ActionChains
                                    actions = ActionChains(driver)
                                    actions.move_to_element(el).perform()
                                    time.sleep(0.1)
                                except Exception:
                                    pass
                            el.click()
                        elif action == "Input Text":
                            el.clear()
                            el.send_keys(value)
                        elif action == "Clear":
                            el.clear()
                        elif action == "Get Text":
                            extracted_texts.append(el.text)
                    if action == "Get Text" and var_name:
                        combined = ", ".join(extracted_texts)
                        set_variable(var_name, combined)
                        if is_capture:
                            self.log_signal.emit(f"[CAPTURE] {var_name} = {combined}")
                            import threading
                            curr_thread = threading.current_thread()
                            if not hasattr(curr_thread, "Captures"):
                                curr_thread.Captures = {}
                            curr_thread.Captures[var_name] = combined
                else:
                    if index >= len(elements):
                        raise IndexError(f"Element index {index} out of range ({len(elements)} found).")
                    
                    el = elements[index]
                    if action == "Click":
                        if draw_mouse:
                            try:
                                from selenium.webdriver.common.action_chains import ActionChains
                                actions = ActionChains(driver)
                                actions.move_to_element(el).perform()
                                time.sleep(0.1)
                            except Exception:
                                pass
                        el.click()
                    elif action == "Input Text":
                        el.clear()
                        el.send_keys(value)
                    elif action == "Clear":
                        el.clear()
                    elif action == "Get Text":
                        text_val = el.text
                        if var_name:
                            set_variable(var_name, text_val)
                            if is_capture:
                                self.log_signal.emit(f"[CAPTURE] {var_name} = {text_val}")
                                import threading
                                curr_thread = threading.current_thread()
                                if not hasattr(curr_thread, "Captures"):
                                    curr_thread.Captures = {}
                                curr_thread.Captures[var_name] = text_val
                    elif action == "Select Dropdown":
                        from selenium.webdriver.support.ui import Select
                        select = Select(el)
                        try:
                            select.select_by_value(value)
                        except Exception:
                            select.select_by_visible_text(value)
                            
            elif block_type == "EXECUTE JS":
                script = interpolated_block.get("script", "")
                var_name = interpolated_block.get("variable_name", "")
                res = driver.execute_script(script)
                if var_name and res is not None:
                    set_variable(var_name, str(res))
                    
            else:
                from engine.block_executor import execute_custom_block
                execute_custom_block(block_type, interpolated_block, t_vars, driver, set_variable, self.log_signal.emit)
