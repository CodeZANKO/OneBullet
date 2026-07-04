import os
import re
import random
import zipfile
import shlex
import time
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from selenium.common.exceptions import TimeoutException

def create_proxy_auth_extension(host: str, port: str, username: str, password: str, dir_path: str) -> str:
    """
    Creates a temporary Chrome extension zip file to authenticate proxies dynamically.
    Chrome doesn't natively support proxy credentials passed via the command line,
    so this extension intercepts web requests and provides credentials.
    """
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy Auth Extension",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """
    
    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{host}",
                port: parseInt({port})
            }},
            bypassList: []
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{
                authCredentials: {{
                    username: "{username}",
                    password: "{password}"
                }}
            }};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """
    ext_path = os.path.join(dir_path, f"proxy_auth_ext_{host}_{port}.zip")
    with zipfile.ZipFile(ext_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return ext_path


class OneScriptCompiler:
    """Compiles visual blocks to text scripts and decompiles text scripts to visual blocks using One Script framework."""
    
    @staticmethod
    def compile_to_script(blocks) -> str:
        lines = []
        for block in blocks:
            b_type = block.get("type", "")
            if b_type == "BROWSER ACTION":
                action = block.get("action", "Start Browser")
                lines.append(f'BLOCK:BROWSERACTION action="{ZanScriptCompiler.escape(action)}"')
            elif b_type == "NAVIGATE":
                url = block.get("url", "")
                timeout = block.get("timeout", 60)
                ban = "true" if block.get("ban_on_timeout", False) else "false"
                lines.append(f'BLOCK:NAVIGATE url="{ZanScriptCompiler.escape(url)}" timeout="{timeout}" ban_on_timeout="{ban}"')
            elif b_type == "ELEMENT ACTION":
                sel_type = block.get("selector_type", "XPATH")
                sel = block.get("selector", "")
                act = block.get("action", "Click")
                val = block.get("value", "")
                var = block.get("variable_name", "")
                idx = block.get("index", 0)
                rec = "true" if block.get("recursive", False) else "false"
                cap = "true" if block.get("is_capture", False) else "false"
                lines.append(
                    f'BLOCK:ELEMENTACTION selector_type="{ZanScriptCompiler.escape(sel_type)}" '
                    f'selector="{ZanScriptCompiler.escape(sel)}" '
                    f'action="{ZanScriptCompiler.escape(act)}" '
                    f'value="{ZanScriptCompiler.escape(val)}" '
                    f'variable_name="{ZanScriptCompiler.escape(var)}" '
                    f'index="{idx}" recursive="{rec}" is_capture="{cap}"'
                )
            elif b_type == "EXECUTE JS":
                script = block.get("script", "")
                var = block.get("variable_name", "")
                lines.append(
                    f'BLOCK:EXECUTEJS script="{ZanScriptCompiler.escape(script)}" '
                    f'variable_name="{ZanScriptCompiler.escape(var)}"'
                )
            elif b_type == "FUNCTION":
                f_type = block.get("function_type", "Constant")
                var = block.get("variable_name", "")
                in_str = block.get("input_string", "")
                cap = "true" if block.get("is_capture", False) else "false"
                lines.append(
                    f'BLOCK:FUNCTION function_type="{ZanScriptCompiler.escape(f_type)}" '
                    f'variable_name="{ZanScriptCompiler.escape(var)}" '
                    f'input_string="{ZanScriptCompiler.escape(in_str)}" is_capture="{cap}"'
                )
            elif b_type == "PARSE":
                source = block.get("source", "<SOURCE>")
                var = block.get("variable_name", "")
                prefix = block.get("prefix", "")
                suffix = block.get("suffix", "")
                mode = block.get("mode", "LR")
                left = block.get("left_string", "")
                right = block.get("right_string", "")
                rec = "true" if block.get("recursive", False) else "false"
                enc = "true" if block.get("enc_output", False) else "false"
                empty = "true" if block.get("create_empty", False) else "false"
                cap = "true" if block.get("is_capture", False) else "false"
                lines.append(
                    f'BLOCK:PARSE source="{ZanScriptCompiler.escape(source)}" '
                    f'variable_name="{ZanScriptCompiler.escape(var)}" '
                    f'prefix="{ZanScriptCompiler.escape(prefix)}" '
                    f'suffix="{ZanScriptCompiler.escape(suffix)}" '
                    f'mode="{ZanScriptCompiler.escape(mode)}" '
                    f'left_string="{ZanScriptCompiler.escape(left)}" '
                    f'right_string="{ZanScriptCompiler.escape(right)}" '
                    f'recursive="{rec}" enc_output="{enc}" create_empty="{empty}" is_capture="{cap}"'
                )
            elif b_type == "KEY CHECK":
                ban_4xx = "true" if block.get("insta_ban_4xx", False) else "false"
                ban_no_key = "true" if block.get("ban_if_no_key", False) else "false"
                keychains = block.get("keychains", "[]")
                if not isinstance(keychains, str):
                    import json
                    keychains = json.dumps(keychains)
                lines.append(
                    f'BLOCK:KEYCHECK insta_ban_4xx="{ban_4xx}" '
                    f'ban_if_no_key="{ban_no_key}" '
                    f'keychains="{ZanScriptCompiler.escape(keychains)}"'
                )
            elif b_type == "BYPASS CF":
                url = block.get("url", "")
                ua = block.get("user_agent", "")
                sec = block.get("security_protocol", "SystemDefault")
                print_info = "true" if block.get("print_response_info", False) else "false"
                redir = "true" if block.get("auto_redirect", False) else "false"
                lines.append(
                    f'BLOCK:BYPASSCF url="{ZanScriptCompiler.escape(url)}" '
                    f'user_agent="{ZanScriptCompiler.escape(ua)}" '
                    f'security_protocol="{ZanScriptCompiler.escape(sec)}" '
                    f'print_response_info="{print_info}" auto_redirect="{redir}"'
                )
            elif b_type == "REQUEST":
                url = block.get("url", "")
                method = block.get("method", "GET")
                redir = "true" if block.get("auto_redirect", True) else "false"
                read_resp = "true" if block.get("read_resp_source", True) else "false"
                accept_enc = "true" if block.get("accept_encoding", True) else "false"
                enc_content = "true" if block.get("encode_content", False) else "false"
                sec = block.get("security_protocol", "SystemDefault")
                req_type = block.get("request_type", "Standard")
                content_type = block.get("content_type", "")
                resp_type = block.get("response_type", "String")
                post_data = block.get("post_data", "")
                cookies = block.get("custom_cookies", "")
                headers = block.get("custom_headers", "")
                lines.append(
                    f'BLOCK:REQUEST url="{ZanScriptCompiler.escape(url)}" '
                    f'method="{ZanScriptCompiler.escape(method)}" '
                    f'auto_redirect="{redir}" read_resp_source="{read_resp}" '
                    f'accept_encoding="{accept_enc}" encode_content="{enc_content}" '
                    f'security_protocol="{ZanScriptCompiler.escape(sec)}" '
                    f'request_type="{ZanScriptCompiler.escape(req_type)}" '
                    f'content_type="{ZanScriptCompiler.escape(content_type)}" '
                    f'response_type="{ZanScriptCompiler.escape(resp_type)}" '
                    f'post_data="{ZanScriptCompiler.escape(post_data)}" '
                    f'custom_cookies="{ZanScriptCompiler.escape(cookies)}" '
                    f'custom_headers="{ZanScriptCompiler.escape(headers)}"'
                )
            elif b_type == "TCP":
                var = block.get("variable_name", "")
                cap = "true" if block.get("is_capture", False) else "false"
                cmd = block.get("command", "Connect")
                host = block.get("host", "")
                port = block.get("port", "80")
                ssl_val = "true" if block.get("ssl", False) else "false"
                hello = "true" if block.get("wait_for_hello", False) else "false"
                lines.append(
                    f'BLOCK:TCP variable_name="{ZanScriptCompiler.escape(var)}" is_capture="{cap}" '
                    f'command="{ZanScriptCompiler.escape(cmd)}" host="{ZanScriptCompiler.escape(host)}" '
                    f'port="{port}" ssl="{ssl_val}" wait_for_hello="{hello}"'
                )
            elif b_type == "UTILITY":
                var = block.get("variable_name", "")
                cap = "true" if block.get("is_capture", False) else "false"
                group = block.get("group", "List")
                act = block.get("action", "Join")
                list_var = block.get("list_var_name", "")
                sep = block.get("separator", ",")
                lines.append(
                    f'BLOCK:UTILITY variable_name="{ZanScriptCompiler.escape(var)}" is_capture="{cap}" '
                    f'group="{ZanScriptCompiler.escape(group)}" action="{ZanScriptCompiler.escape(act)}" '
                    f'list_var_name="{ZanScriptCompiler.escape(list_var)}" separator="{ZanScriptCompiler.escape(sep)}"'
                )
            elif b_type == "SOLVE CAPTCHA":
                var = block.get("variable_name", "")
                c_type = block.get("captcha_type", "ReCaptchaV2")
                site_key = block.get("site_key", "")
                page_url = block.get("page_url", "")
                lines.append(
                    f'BLOCK:SOLVECAPTCHA variable_name="{ZanScriptCompiler.escape(var)}" '
                    f'captcha_type="{ZanScriptCompiler.escape(c_type)}" '
                    f'site_key="{ZanScriptCompiler.escape(site_key)}" '
                    f'page_url="{ZanScriptCompiler.escape(page_url)}"'
                )
            elif b_type == "REPORT CAPTCHA":
                cap_id = block.get("captcha_id", "")
                bad = "true" if block.get("report_bad", False) else "false"
                lines.append(
                    f'BLOCK:REPORTCAPTCHA captcha_id="{ZanScriptCompiler.escape(cap_id)}" report_bad="{bad}"'
                )
            lines.append("") # Empty line spacing
        return "\n".join(lines)

    @staticmethod
    def decompile_to_blocks(script_text: str):
        blocks = []
        lines = script_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
                
            cmd_match = re.match(r"^([A-Z_:]+)\s*(.*)$", line)
            if not cmd_match:
                continue
            cmd = cmd_match.group(1)
            rest = cmd_match.group(2)
            
            matches = re.findall(r'(\w+)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"', rest)
            args = {k: ZanScriptCompiler.unescape(v) for k, v in matches}
            
            if cmd in ["BLOCK:BROWSERACTION", "BROWSER_ACTION"]:
                blocks.append({
                    "type": "BROWSER ACTION",
                    "action": args.get("action", "Start Browser")
                })
            elif cmd in ["BLOCK:NAVIGATE", "NAVIGATE"]:
                blocks.append({
                    "type": "NAVIGATE",
                    "url": args.get("url", ""),
                    "timeout": int(args.get("timeout", 60)),
                    "ban_on_timeout": args.get("ban_on_timeout", "false").lower() == "true"
                })
            elif cmd in ["BLOCK:ELEMENTACTION", "ELEMENT_ACTION"]:
                blocks.append({
                    "type": "ELEMENT ACTION",
                    "selector_type": args.get("selector_type", "XPATH"),
                    "selector": args.get("selector", ""),
                    "action": args.get("action", "Click"),
                    "value": args.get("value", ""),
                    "variable_name": args.get("variable_name", ""),
                    "index": int(args.get("index", 0)),
                    "recursive": args.get("recursive", "false").lower() == "true",
                    "is_capture": args.get("is_capture", "false").lower() == "true"
                })
            elif cmd in ["BLOCK:EXECUTEJS", "EXECUTE_JS"]:
                blocks.append({
                    "type": "EXECUTE JS",
                    "script": args.get("script", ""),
                    "variable_name": args.get("variable_name", "")
                })
            elif cmd in ["BLOCK:FUNCTION", "FUNCTION"]:
                blocks.append({
                    "type": "FUNCTION",
                    "function_type": args.get("function_type", "Constant"),
                    "variable_name": args.get("variable_name", ""),
                    "input_string": args.get("input_string", ""),
                    "is_capture": args.get("is_capture", "false").lower() == "true"
                })
            elif cmd in ["BLOCK:PARSE", "PARSE"]:
                blocks.append({
                    "type": "PARSE",
                    "source": args.get("source", "<SOURCE>"),
                    "variable_name": args.get("variable_name", ""),
                    "prefix": args.get("prefix", ""),
                    "suffix": args.get("suffix", ""),
                    "mode": args.get("mode", "LR"),
                    "left_string": args.get("left_string", ""),
                    "right_string": args.get("right_string", ""),
                    "recursive": args.get("recursive", "false").lower() == "true",
                    "enc_output": args.get("enc_output", "false").lower() == "true",
                    "create_empty": args.get("create_empty", "false").lower() == "true",
                    "is_capture": args.get("is_capture", "false").lower() == "true"
                })
            elif cmd in ["BLOCK:KEYCHECK", "KEY_CHECK"]:
                blocks.append({
                    "type": "KEY CHECK",
                    "insta_ban_4xx": args.get("insta_ban_4xx", "false").lower() == "true",
                    "ban_if_no_key": args.get("ban_if_no_key", "false").lower() == "true",
                    "keychains": args.get("keychains", "[]")
                })
            elif cmd in ["BLOCK:BYPASSCF", "BYPASS_CF"]:
                blocks.append({
                    "type": "BYPASS CF",
                    "url": args.get("url", ""),
                    "user_agent": args.get("user_agent", ""),
                    "security_protocol": args.get("security_protocol", "SystemDefault"),
                    "print_response_info": args.get("print_response_info", "false").lower() == "true",
                    "auto_redirect": args.get("auto_redirect", "false").lower() == "true"
                })
            elif cmd in ["BLOCK:REQUEST", "REQUEST"]:
                blocks.append({
                    "type": "REQUEST",
                    "url": args.get("url", ""),
                    "method": args.get("method", "GET"),
                    "auto_redirect": args.get("auto_redirect", "true").lower() == "true",
                    "read_resp_source": args.get("read_resp_source", "true").lower() == "true",
                    "accept_encoding": args.get("accept_encoding", "true").lower() == "true",
                    "encode_content": args.get("encode_content", "false").lower() == "true",
                    "security_protocol": args.get("security_protocol", "SystemDefault"),
                    "request_type": args.get("request_type", "Standard"),
                    "content_type": args.get("content_type", ""),
                    "response_type": args.get("response_type", "String"),
                    "post_data": args.get("post_data", ""),
                    "custom_cookies": args.get("custom_cookies", ""),
                    "custom_headers": args.get("custom_headers", "")
                })
            elif cmd in ["BLOCK:TCP", "TCP"]:
                blocks.append({
                    "type": "TCP",
                    "variable_name": args.get("variable_name", ""),
                    "is_capture": args.get("is_capture", "false").lower() == "true",
                    "command": args.get("command", "Connect"),
                    "host": args.get("host", ""),
                    "port": args.get("port", "80"),
                    "ssl": args.get("ssl", "false").lower() == "true",
                    "wait_for_hello": args.get("wait_for_hello", "false").lower() == "true"
                })
            elif cmd in ["BLOCK:UTILITY", "UTILITY"]:
                blocks.append({
                    "type": "UTILITY",
                    "variable_name": args.get("variable_name", ""),
                    "is_capture": args.get("is_capture", "false").lower() == "true",
                    "group": args.get("group", "List"),
                    "action": args.get("action", "Join"),
                    "list_var_name": args.get("list_var_name", ""),
                    "separator": args.get("separator", ",")
                })
            elif cmd in ["BLOCK:SOLVECAPTCHA", "SOLVE_CAPTCHA"]:
                blocks.append({
                    "type": "SOLVE CAPTCHA",
                    "variable_name": args.get("variable_name", ""),
                    "captcha_type": args.get("captcha_type", "ReCaptchaV2"),
                    "site_key": args.get("site_key", ""),
                    "page_url": args.get("page_url", "")
                })
            elif cmd in ["BLOCK:REPORTCAPTCHA", "REPORT_CAPTCHA"]:
                blocks.append({
                    "type": "REPORT CAPTCHA",
                    "captcha_id": args.get("captcha_id", ""),
                    "report_bad": args.get("report_bad", "false").lower() == "true"
                })
        return blocks

    @staticmethod
    def escape(s: str) -> str:
        if not isinstance(s, str):
            return str(s)
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

    @staticmethod
    def unescape(s: str) -> str:
        if not isinstance(s, str):
            return str(s)
        return s.replace('\\n', '\n').replace('\\r', '\r').replace('\\"', '"').replace('\\\\', '\\')


# Alias for legacy compatibility
ZanScriptCompiler = OneScriptCompiler
LoliScriptCompiler = OneScriptCompiler


class SeleniumEngine(QThread):
    """
    Executes a series of automation blocks in a separate thread.
    Communicates execution details, logs, and browser HTML back to the main UI thread.
    """
    log_signal = pyqtSignal(str)              # Raw log messages
    state_signal = pyqtSignal(int, str)        # Index, Status (RUNNING, COMPLETED, FAILED)
    html_signal = pyqtSignal(str)             # Page source HTML
    finished_signal = pyqtSignal(bool, str)     # Completed successfully flag, final msg
    variables_signal = pyqtSignal(dict)       # Dynamic variables dictionary
    
    def __init__(self, blocks, settings, variables_input=None, proxies=None):
        super().__init__()
        self.blocks = blocks
        self.settings = settings
        self.variables_input = variables_input or {}
        self.proxies = proxies or []
        
        # Load global settings from settings.json
        from utils.helpers import load_settings
        self.global_settings = load_settings()
        
        self.driver = None
        self.variables = {}
        self.current_index = 0
        self.current_proxy = None
        
        # Thread sync controls for step execution
        self.is_paused = False
        self.is_stopped = False
        self.step_mode = False
        
        self.mutex = QMutex()
        self.wait_cond = QWaitCondition()

    def run(self):
        self.log_signal.emit("[INFO] Engine started.")
        self.variables = self.variables_input.copy()
        
        # Populate ThreadVariables on the current thread object
        import threading
        import requests
        ThreadVariables = {}
        for k, v in self.variables.items():
            ThreadVariables[k] = v
            clean_k = k.strip("<>")
            ThreadVariables[clean_k.upper()] = v
            ThreadVariables[clean_k.lower()] = v
            ThreadVariables[f"<{clean_k.upper()}>"] = v
            ThreadVariables[f"<{clean_k.lower()}>"] = v
        threading.current_thread().ThreadVariables = ThreadVariables
        self.variables_signal.emit(self.variables)
        
        # Initialize http session per thread for Requests Mode
        http_session = requests.Session()
        threading.current_thread().http_session = http_session
        
        self.is_stopped = False
        self.current_index = 0
        
        # Check settings for auto start (respect use_selenium)
        use_sel = self.settings.get("use_selenium", True)
        if use_sel and self.settings.get("always_open", True):
            success = self.init_driver()
            if not success:
                self.finished_signal.emit(False, "Failed to initialize webdriver.")
                try:
                    http_session.close()
                except Exception:
                    pass
                return

        while self.current_index < len(self.blocks):
            if self.is_stopped:
                break
                
            # Handle Pause/Step condition
            self.mutex.lock()
            if self.is_paused:
                self.log_signal.emit(f"[DEBUG] Pausing before Block {self.current_index + 1}")
                self.wait_cond.wait(self.mutex)
            self.mutex.unlock()
            
            if self.is_stopped:
                break
                
            block = self.blocks[self.current_index]
            
            # Deep clone and interpolate block properties before execution using ThreadVariables
            import copy
            import threading
            from utils.helpers import interpolate_value
            t_vars = getattr(threading.current_thread(), "ThreadVariables", {})
            interpolated_block = interpolate_value(copy.deepcopy(block), t_vars)
            block_type = interpolated_block.get("type", "")
            
            self.state_signal.emit(self.current_index, "RUNNING")
            self.log_signal.emit(f"[INFO] Executing Block {self.current_index + 1}: {block_type}")
            
            try:
                # Apply RuriLib General Wait Time (in ms)
                wait_ms = self.global_settings.get("RuriLib", {}).get("General", {}).get("waitTime", 0)
                if wait_ms > 0:
                    time.sleep(wait_ms / 1000.0)
                
                self.execute_block(interpolated_block)
                self.variables_signal.emit(self.variables)
                # Fetch browser page source for HTML preview tab
                if self.driver:
                    try:
                        self.html_signal.emit(self.driver.page_source)
                    except Exception:
                        pass
                else:
                    # Emitting the raw response body string from context variables
                    source_content = self.variables.get("<SOURCE>", self.variables.get("SOURCE", ""))
                    self.html_signal.emit(source_content)
            except Exception as e:
                self.log_signal.emit(f"[ERROR] Block {self.current_index + 1} failed: {str(e)}")
                self.state_signal.emit(self.current_index, "FAILED")
                self.finished_signal.emit(False, f"Error at block {self.current_index + 1}: {str(e)}")
                try:
                    http_session.close()
                except Exception:
                    pass
                return
            else:
                self.state_signal.emit(self.current_index, "COMPLETED")
                
            self.current_index += 1
            
            # In Step Mode, pause after executing a single block
            if self.step_mode and self.current_index < len(self.blocks):
                self.is_paused = True
 
        # Quit driver if set
        if self.settings.get("always_quit", True) and self.driver:
            self.quit_driver()
            
        # Close http session per thread
        try:
            http_session.close()
        except Exception:
            pass
            
        self.log_signal.emit("[INFO] Execution finished successfully.")
        self.finished_signal.emit(True, "Workflow completed successfully.")

    def pause_execution(self):
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()

    def resume_execution(self):
        self.mutex.lock()
        self.is_paused = False
        self.step_mode = False
        self.wait_cond.wakeAll()
        self.mutex.unlock()

    def step_execution(self):
        self.mutex.lock()
        self.step_mode = True
        self.is_paused = False
        self.wait_cond.wakeAll()
        self.mutex.unlock()

    def stop_execution(self):
        self.mutex.lock()
        self.is_stopped = True
        self.is_paused = False
        self.wait_cond.wakeAll()
        self.mutex.unlock()
        self.quit_driver()

    def init_driver(self) -> bool:
        if self.driver is not None:
            return True
            
        from selenium import webdriver
        
        # Load parameters dynamically from global settings
        rl_sel = self.global_settings.get("RuriLib", {}).get("Selenium", {})
        browser_type = rl_sel.get("browserType", "Chrome")
        headless = self.settings.get("headless", False) or rl_sel.get("headlessMode", False)
        default_timeout = rl_sel.get("defaultTimeout", 30)
        
        self.log_signal.emit(f"[INFO] Initializing {browser_type} WebDriver...")
        
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
            self.log_signal.emit(f"[INFO] Using Random User-Agent: {ua}")

        # Setup proxy details
        proxy_arg = None
        auth_ext_path = None
        if self.settings.get("use_proxies", False) and self.proxies:
            self.current_proxy = random.choice(self.proxies)
            proxy = self.current_proxy
            self.log_signal.emit(f"[INFO] Applying Proxy: {proxy['type']}://{proxy['host']}:{proxy['port']}")
            
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
                
                profile_dir = os.path.join(os.getcwd(), "temp_chrome_profiles", f"chrome_profile_{random.randint(10000, 99999)}")
                options.add_argument(f"--user-data-dir={profile_dir}")
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)

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
                if self.settings.get("use_proxies", False) and self.current_proxy:
                    from selenium.webdriver.common.proxy import Proxy, ProxyType
                    p = self.current_proxy
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
                self.driver = webdriver.Firefox(service=service, options=options)

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
                self.driver = webdriver.Edge(service=service, options=options)

            else:  # InternetExplorer
                from selenium.webdriver.ie.service import Service
                from webdriver_manager.microsoft import IEDriverManager
                options = webdriver.IeOptions()
                service = Service(IEDriverManager().install())
                self.driver = webdriver.Ie(service=service, options=options)
            
            # Apply loaded default timeouts
            self.driver.set_page_load_timeout(default_timeout)
            self.driver.implicitly_wait(min(10, default_timeout))
            
            self.log_signal.emit(f"[INFO] {browser_type} WebDriver started successfully.")
            return True
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Failed to start {browser_type} WebDriver: {str(e)}")
            return False

    def quit_driver(self):
        if self.driver:
            self.log_signal.emit("[INFO] Closing WebDriver...")
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            self.log_signal.emit("[INFO] WebDriver closed.")

    def interpolate(self, text: str) -> str:
        """Replaces variable place holders like <USER> or <PASS> with current values."""
        if not isinstance(text, str):
            return text
        import threading
        t_vars = getattr(threading.current_thread(), "ThreadVariables", {})
        variables_to_use = t_vars if t_vars else self.variables
        sorted_keys = sorted(variables_to_use.keys(), key=len, reverse=True)
        for k in sorted_keys:
            v = variables_to_use[k]
            tag = k if (k.startswith("<") and k.endswith(">")) else f"<{k}>"
            text = text.replace(tag, str(v))
        return text

    def set_variable(self, name: str, val):
        self.variables[name] = val
        import threading
        t_vars = getattr(threading.current_thread(), "ThreadVariables", None)
        if t_vars is not None:
            t_vars[name] = val
            if name.startswith("<") and name.endswith(">"):
                t_vars[name[1:-1]] = val
            else:
                t_vars[f"<{name}>"] = val

    def execute_block(self, block):
        block_type = block.get("type", "")
        
        if block_type == "BROWSER ACTION":
            action = block.get("action", "Start Browser")
            
            # Standard & Expanded Actions
            if action in ["Start Browser", "Open"]:
                self.init_driver()
            elif action in ["Close Browser", "Close", "Quit"]:
                self.quit_driver()
            elif action == "Refresh":
                if self.driver:
                    self.driver.refresh()
            elif action == "Go Back":
                if self.driver:
                    self.driver.back()
            elif action == "Go Forward":
                if self.driver:
                    self.driver.forward()
            elif action == "ClearCookies":
                if self.driver:
                    self.log_signal.emit("[INFO] Clearing browser cookies...")
                    self.driver.delete_all_cookies()
            elif action == "Screenshot":
                if self.driver:
                    os.makedirs("screenshots", exist_ok=True)
                    filename = f"screenshots/screenshot_{int(time.time())}.png"
                    self.log_signal.emit(f"[INFO] Taking screenshot and saving to: {filename}")
                    self.driver.save_screenshot(filename)
            elif action == "ScrollToTop":
                if self.driver:
                    self.log_signal.emit("[INFO] Scrolling to page top...")
                    self.driver.execute_script("window.scrollTo(0, 0);")
            elif action == "ScrollToBottom":
                if self.driver:
                    self.log_signal.emit("[INFO] Scrolling to page bottom...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            elif action == "Scroll":
                if self.driver:
                    self.log_signal.emit("[INFO] Scrolling window down...")
                    self.driver.execute_script("window.scrollBy(0, 250);")
            elif action == "OpenNewTab":
                if self.driver:
                    self.log_signal.emit("[INFO] Opening new tab...")
                    self.driver.execute_script("window.open('');")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
        elif block_type == "NAVIGATE":
            url = self.interpolate(block.get("url", ""))
            timeout = int(block.get("timeout", 60))
            ban_on_timeout = block.get("ban_on_timeout", False)
            
            if not url:
                raise ValueError("Navigation URL is empty.")
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
                
            self.log_signal.emit(f"[INFO] Navigating to: {url} with Timeout={timeout}s")
            if self.driver is None:
                self.init_driver()
            
            self.driver.set_page_load_timeout(timeout)
            try:
                self.driver.get(url)
            except TimeoutException as e:
                self.log_signal.emit(f"[WARNING] Page load timed out after {timeout} seconds.")
                if ban_on_timeout and self.current_proxy:
                    never_ban = self.global_settings.get("RuriLib", {}).get("Proxies", {}).get("neverBanProxies", False)
                    if never_ban:
                        self.log_signal.emit(f"[INFO] Skipping proxy ban due to 'Never Ban Proxies' setting.")
                    else:
                        self.log_signal.emit(f"[BAN] Banning current proxy due to page timeout: {self.current_proxy['host']}")
                        self.current_proxy['status'] = "Failed" # Mark proxy as banned
                raise e
            
        elif block_type == "ELEMENT ACTION":
            selector_type = block.get("selector_type", "XPATH")
            selector = self.interpolate(block.get("selector", ""))
            action = block.get("action", "Click")
            value = self.interpolate(block.get("value", ""))
            var_name = block.get("variable_name", "")
            
            # New attributes
            index = int(block.get("index", 0))
            recursive = block.get("recursive", False)
            is_capture = block.get("is_capture", False)
            
            if self.driver is None:
                self.init_driver()
                
            from selenium.webdriver.common.by import By
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
            
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            if action == "Wait for Element":
                self.log_signal.emit(f"[INFO] Waiting for element: {selector}")
                wait_time = 10
                try:
                    wait_time = int(value) if value.isdigit() else 10
                except:
                    pass
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((by_strategy, selector))
                )
                self.log_signal.emit("[INFO] Element is now present.")
                return
                
            # Perform action using find_elements
            rl_sel = self.global_settings.get("RuriLib", {}).get("Selenium", {})
            default_timeout = rl_sel.get("defaultTimeout", 30)
            draw_mouse = rl_sel.get("drawMouseMovement", False)

            WebDriverWait(self.driver, default_timeout).until(
                EC.presence_of_element_located((by_strategy, selector))
            )
            elements = self.driver.find_elements(by_strategy, selector)
            
            if not elements:
                raise ValueError(f"No elements found matching selector: {selector}")
                
            if recursive:
                self.log_signal.emit(f"[INFO] Operating recursively on all matching elements ({len(elements)} found)")
                extracted_texts = []
                for idx, el in enumerate(elements):
                    if action == "Click":
                        if draw_mouse:
                            try:
                                from selenium.webdriver.common.action_chains import ActionChains
                                actions = ActionChains(self.driver)
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
                
                # Combine extracted text if Get Text action
                if action == "Get Text" and var_name:
                    combined = ", ".join(extracted_texts)
                    self.set_variable(var_name, combined)
                    self.log_signal.emit(f"[INFO] Combined recursive result for <{var_name}> = '{combined}'")
                    if is_capture:
                        self.log_signal.emit(f"[CAPTURE] {var_name} = {combined}")
            else:
                if index >= len(elements):
                    raise IndexError(f"Element index {index} out of range. Only {len(elements)} matching elements found.")
                
                el = elements[index]
                self.log_signal.emit(f"[INFO] Operating on element index {index} for: {selector}")
                
                if action == "Click":
                    if draw_mouse:
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
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
                    self.log_signal.emit(f"[INFO] Retrieved text: '{text_val}'")
                    if var_name:
                        self.set_variable(var_name, text_val)
                        self.log_signal.emit(f"[INFO] Assigned variable <{var_name}> = '{text_val}'")
                        if is_capture:
                            self.log_signal.emit(f"[CAPTURE] {var_name} = {text_val}")
                elif action == "Select Dropdown":
                    from selenium.webdriver.support.ui import Select
                    select = Select(el)
                    try:
                        select.select_by_value(value)
                    except Exception:
                        select.select_by_visible_text(value)
                        
        elif block_type == "EXECUTE JS":
            script = self.interpolate(block.get("script", ""))
            var_name = block.get("variable_name", "")
            
            if self.driver is None:
                self.init_driver()
                
            self.log_signal.emit("[INFO] Running JavaScript Script.")
            res = self.driver.execute_script(script)
            self.log_signal.emit(f"[INFO] JavaScript output: {res}")
            if var_name and res is not None:
                self.set_variable(var_name, str(res))
                self.log_signal.emit(f"[INFO] Assigned variable <{var_name}> = '{res}'")
                
        else:
            from engine.block_executor import execute_custom_block
            execute_custom_block(block_type, block, self.variables, self.driver, self.set_variable, self.log_signal.emit)
