import os
import re
import time
import base64
import hashlib
import hmac
import socket
import ssl
import threading
import urllib.parse
import requests

def parse_date_to_unix(date_str):
    try:
        import dateutil.parser as dparser
        return str(int(dparser.parse(date_str).timestamp()))
    except Exception:
        try:
            return str(int(time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))))
        except Exception:
            return str(int(time.time()))

def execute_custom_block(block_type, block, variables, driver, set_variable_func, log_func):
    if block_type == "FUNCTION":
        fn_type = block.get("function_type", "Constant")
        in_str = block.get("input_string", "")
        var_name = block.get("variable_name", "")
        is_capture = block.get("is_capture", False)
        
        res = ""
        if fn_type == "Constant":
            res = in_str
        elif fn_type == "Base64Encode":
            res = base64.b64encode(in_str.encode('utf-8', errors='ignore')).decode('utf-8')
        elif fn_type == "Base64Decode":
            try:
                # Add padding if missing
                missing_padding = len(in_str) % 4
                if missing_padding:
                    in_str += '=' * (4 - missing_padding)
                res = base64.b64decode(in_str.encode('utf-8', errors='ignore')).decode('utf-8', errors='ignore')
            except Exception as e:
                res = f"DECODE_ERROR: {str(e)}"
        elif fn_type == "Hash":
            res = hashlib.sha256(in_str.encode('utf-8', errors='ignore')).hexdigest()
        elif fn_type == "HMAC":
            # Use default key or extract key if present
            key = b"secret"
            res = hmac.new(key, in_str.encode('utf-8', errors='ignore'), hashlib.sha256).hexdigest()
        elif fn_type == "Translate":
            res = in_str
        elif fn_type == "DateToUnixTime":
            res = parse_date_to_unix(in_str)
        elif fn_type == "Length":
            res = str(len(in_str))
        elif fn_type == "ToLowercase":
            res = in_str.lower()
        elif fn_type == "ToUppercase":
            res = in_str.upper()
        else:
            res = in_str
            
        if var_name:
            set_variable_func(var_name, res)
            log_func(f"[INFO] FUNCTION ({fn_type}) -> Assigned variable <{var_name}> = '{res}'")
            if is_capture:
                log_func(f"[CAPTURE] {var_name} = {res}")
                import threading
                curr_thread = threading.current_thread()
                if not hasattr(curr_thread, "Captures"):
                    curr_thread.Captures = {}
                curr_thread.Captures[var_name] = res

    elif block_type == "PARSE":
        source_tag = block.get("source", "<SOURCE>")
        var_name = block.get("variable_name", "")
        prefix = block.get("prefix", "")
        suffix = block.get("suffix", "")
        mode = block.get("mode", "LR")  # LR, CSS, JSON, REGEX
        left_str = block.get("left_string", "")
        right_str = block.get("right_string", "")
        
        recursive = block.get("recursive", False)
        enc_output = block.get("enc_output", False)
        create_empty = block.get("create_empty", False)
        use_regex = block.get("use_regex", False)
        is_capture = block.get("is_capture", False)
        
        source_content = ""
        try:
            if source_tag == "<SOURCE>":
                # Default to reading from "<SOURCE>" buffer populated by previous request
                source_content = variables.get("<SOURCE>", variables.get("SOURCE", ""))
                if not source_content and driver:
                    try:
                        source_content = driver.page_source
                    except Exception:
                        pass
            else:
                source_content = source_tag
                
            if not source_content:
                source_content = ""
                
            results = []
            if mode == "LR":
                if left_str or right_str:
                    if use_regex:
                        pattern = f"{left_str}(.*?){right_str}"
                    else:
                        escaped_left = re.escape(left_str)
                        escaped_right = re.escape(right_str)
                        pattern = f"{escaped_left}(.*?){escaped_right}"
                    
                    matches = re.findall(pattern, source_content, re.DOTALL)
                    results = []
                    for m in matches:
                        if isinstance(m, tuple):
                            results.append(m[0] if m else "")
                        else:
                            results.append(str(m))
                else:
                    results = [source_content]
                    
            elif mode == "REGEX":
                pattern = left_str
                if pattern:
                    matches = re.findall(pattern, source_content, re.DOTALL)
                    results = []
                    for m in matches:
                        if isinstance(m, tuple):
                            results.append(m[0] if m else "")
                        else:
                            results.append(str(m))
                        
            elif mode == "JSON":
                import json
                path = left_str
                data = json.loads(source_content)
                if path.startswith("$."):
                    path = path[2:]
                parts = path.split('.')
                val = data
                for part in parts:
                    if not part:
                        continue
                    if '[' in part and ']' in part:
                        array_name, index_str = part.replace(']', '').split('[')
                        if array_name:
                            val = val[array_name]
                        val = val[int(index_str)]
                    else:
                        val = val[part]
                results = [str(val)]
                    
            elif mode == "CSS":
                from bs4 import BeautifulSoup
                selector = left_str
                attr = right_str
                soup = BeautifulSoup(source_content, 'html.parser')
                elements = soup.select(selector)
                for el in elements:
                    if attr:
                        val = el.get(attr, "")
                    else:
                        val = el.get_text()
                    results.append(val)
                    
            final_results = []
            for r in results:
                final_results.append(f"{prefix}{r}{suffix}")
                
            res_val = ""
            if final_results:
                if recursive:
                    res_val = ", ".join(final_results)
                else:
                    res_val = final_results[0]
            else:
                if create_empty:
                    res_val = ""
                else:
                    res_val = "" # Safe fallback instead of crashing
                    log_func(f"[WARNING] PARSE block failed to extract any matches in mode {mode}, using empty fallback.")
        except Exception as e:
            log_func(f"[ERROR] PARSE block processing failed: {str(e)}")
            res_val = "" # Fallback
            
        if enc_output and res_val:
            res_val = urllib.parse.quote(res_val)
            
        if var_name:
            set_variable_func(var_name, res_val)
            log_func(f"[INFO] PARSE ({mode}) -> Assigned variable <{var_name}> = '{res_val[:100]}'")
            if is_capture:
                log_func(f"[CAPTURE] {var_name} = {res_val}")
                import threading
                curr_thread = threading.current_thread()
                if not hasattr(curr_thread, "Captures"):
                    curr_thread.Captures = {}
                curr_thread.Captures[var_name] = res_val

    elif block_type == "KEY CHECK":
        insta_ban_4xx = block.get("insta_ban_4xx", False)
        ban_if_no_key = block.get("ban_if_no_key", False)
        keychains = block.get("keychains", [])
        
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        resp_code = str(variables.get("<RESPONSE_CODE>", variables.get("RESPONSE_CODE", "")))
        if insta_ban_4xx and resp_code.startswith("4"):
            log_func(f"[KEY CHECK] Insta Ban 4xx triggered (Response Code: {resp_code})")
            raise AssertionError("BAN: Insta Ban 4xx triggered")
            
        source_content = ""
        if driver:
            try:
                source_content = driver.page_source
            except Exception:
                pass
        if not source_content:
            source_content = variables.get("<SOURCE>", variables.get("SOURCE", ""))
            
        headers_content = variables.get("<HEADERS>", variables.get("HEADERS", ""))
        
        matched_type = None
        for keychain in keychains:
            kc_type = keychain.get("type", "Success")
            kc_mode = keychain.get("mode", "OR")
            keys = keychain.get("keys", [])
            
            matches = []
            for key in keys:
                is_present = (key in source_content) or (key in headers_content) or (key == resp_code)
                matches.append(is_present)
                
            is_matched = False
            if kc_mode == "AND":
                is_matched = all(matches) if matches else False
            else:  # OR
                is_matched = any(matches) if matches else False
                
            if is_matched:
                matched_type = kc_type
                log_func(f"[KEY CHECK] Keychain matched: Type={kc_type}, Mode={kc_mode}")
                break
                
        if matched_type:
            if matched_type == "Success":
                return
            elif matched_type == "Failure":
                raise AssertionError("FAIL: Keychain matched Failure")
            elif matched_type == "Ban":
                raise AssertionError("BAN: Keychain matched Ban")
            elif matched_type == "Retry":
                raise AssertionError("RETRY: Keychain matched Retry")
            elif matched_type == "Custom":
                raise AssertionError("CUSTOM: Keychain matched Custom")
            else:
                return
                
        if ban_if_no_key:
            log_func("[KEY CHECK] Ban if no key found triggered.")
            raise AssertionError("BAN: No keychain matched and Ban If No Key Found is enabled")

    elif block_type == "BYPASS CF":
        url = block.get("url", "")
        ua = block.get("user_agent", "")
        sec_proto = block.get("security_protocol", "SystemDefault")
        print_info = block.get("print_response_info", False)
        auto_redirect = block.get("auto_redirect", False)
        
        if not url:
            raise ValueError("BYPASS CF URL is empty.")
            
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
            
        log_func(f"[BYPASS CF] Navigating to challenge URL: {url}")
        if driver:
            driver.get(url)
            for i in range(15):
                title = driver.title.lower()
                if "cloudflare" not in title and "just a moment" not in title and "checking your browser" not in title:
                    break
                log_func(f"[BYPASS CF] Waiting for challenge... (Elapsed: {i+1}s)")
                time.sleep(1)
            log_func("[BYPASS CF] Challenge bypass completed or timed out.")
            if print_info:
                log_func(f"[BYPASS CF] Page title: {driver.title}")

    elif block_type == "REQUEST":
        url = block.get("url", "")
        method = block.get("method", "GET").upper()
        auto_redirect = block.get("auto_redirect", True)
        read_resp = block.get("read_resp_source", True)
        accept_enc = block.get("accept_encoding", True)
        encode_content = block.get("encode_content", False)
        
        post_data = block.get("post_data", "")
        custom_cookies = block.get("custom_cookies", "")
        custom_headers = block.get("custom_headers", "")
        content_type = block.get("content_type", "")
        
        if not url:
            raise ValueError("REQUEST URL is empty.")
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
            
        import threading
        curr_thread = threading.current_thread()
        session = getattr(curr_thread, "http_session", None)
        if session is None:
            session = requests.Session()
            setattr(curr_thread, "http_session", session)
            
        active_proxy = getattr(curr_thread, "active_proxy", None)
        req_proxies = None
        if active_proxy:
            ptype = active_proxy.get("type", "http").lower()
            if ptype not in ["http", "https", "socks5", "socks4"]:
                ptype = "http"
            host = active_proxy.get("host")
            port = active_proxy.get("port")
            user = active_proxy.get("username")
            pwd = active_proxy.get("password")
            
            auth_part = ""
            if user and pwd:
                auth_part = f"{urllib.parse.quote(user)}:{urllib.parse.quote(pwd)}@"
                
            proxy_url = f"{ptype}://{auth_part}{host}:{port}"
            req_proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
        
        headers = {}
        if accept_enc:
            headers["Accept-Encoding"] = "gzip, deflate, br"
        if content_type:
            headers["Content-Type"] = content_type
            
        for line in custom_headers.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()
                
        if "User-Agent" not in headers:
            ua = variables.get("User-Agent", variables.get("user_agent", ""))
            if ua:
                headers["User-Agent"] = ua
                
        cookies = {}
        if driver:
            try:
                for cookie in driver.get_cookies():
                    cookies[cookie['name']] = cookie['value']
            except Exception:
                pass
                
        for line in custom_cookies.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                cookies[k.strip()] = v.strip()
                
        if cookies:
            for k, v in cookies.items():
                session.cookies.set(k, v)
                
        log_func(f"[HTTP REQUEST] {method} -> {url}")
        try:
            req_args = {
                "headers": headers,
                "allow_redirects": auto_redirect,
                "timeout": 30
            }
            if req_proxies:
                req_args["proxies"] = req_proxies
                
            if method in ["POST", "PUT", "PATCH"]:
                if encode_content:
                    req_args["data"] = urllib.parse.parse_qs(post_data)
                else:
                    req_args["data"] = post_data
                    
            resp = session.request(method, url, **req_args)
            
            set_variable_func("RESPONSE_CODE", str(resp.status_code))
            set_variable_func("<RESPONSE_CODE>", str(resp.status_code))
            
            resp_headers = "\n".join([f"{k}: {v}" for k, v in resp.headers.items()])
            set_variable_func("HEADERS", resp_headers)
            set_variable_func("<HEADERS>", resp_headers)
            
            if read_resp:
                set_variable_func("SOURCE", resp.text)
                set_variable_func("<SOURCE>", resp.text)
                
            log_func(f"[HTTP REQUEST] Completed. Status Code: {resp.status_code}. Response Length: {len(resp.text)} chars")
            
            if driver:
                try:
                    for k, v in resp.cookies.items():
                        driver.add_cookie({"name": k, "value": v, "path": "/"})
                except Exception:
                    pass
        except Exception as e:
            log_func(f"[ERROR] HTTP REQUEST failed: {str(e)}")
            set_variable_func("RESPONSE_CODE", "0")
            set_variable_func("<RESPONSE_CODE>", "0")
            set_variable_func("HEADERS", "")
            set_variable_func("<HEADERS>", "")
            if read_resp:
                set_variable_func("SOURCE", "")
                set_variable_func("<SOURCE>", "")

    elif block_type == "TCP":
        cmd = block.get("command", "Connect")
        host = block.get("host", "")
        port_val = block.get("port", "80")
        ssl_enabled = block.get("ssl", False)
        wait_hello = block.get("wait_for_hello", False)
        var_name = block.get("variable_name", "")
        is_capture = block.get("is_capture", False)
        
        curr_thread = threading.current_thread()
        sock = getattr(curr_thread, "tcp_socket", None)
        
        if cmd == "Connect":
            if not host:
                raise ValueError("TCP Connect requires a Host.")
            port = int(port_val) if str(port_val).isdigit() else 80
            log_func(f"[TCP] Connecting to {host}:{port} (SSL={ssl_enabled})...")
            
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(10)
            
            if ssl_enabled:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(raw_sock, server_hostname=host)
            else:
                sock = raw_sock
                
            sock.connect((host, port))
            setattr(curr_thread, "tcp_socket", sock)
            log_func("[TCP] Connected successfully.")
            
            if wait_hello:
                data = sock.recv(4096).decode('utf-8', errors='ignore')
                log_func(f"[TCP] Received hello: {data}")
                if var_name:
                    set_variable_func(var_name, data)
                    
        elif cmd == "Disconnect":
            if sock:
                log_func("[TCP] Disconnecting socket...")
                try:
                    sock.close()
                except Exception:
                    pass
                setattr(curr_thread, "tcp_socket", None)
                log_func("[TCP] Disconnected.")
                
        elif cmd == "Send":
            data_to_send = block.get("host", "") + "\r\n"
            if sock:
                log_func(f"[TCP] Sending raw data: {data_to_send.strip()}")
                sock.sendall(data_to_send.encode('utf-8'))
            else:
                raise RuntimeError("TCP Socket not connected. Run 'Connect' first.")
                
        elif cmd == "Receive":
            if sock:
                log_func("[TCP] Receiving data...")
                data = sock.recv(4096).decode('utf-8', errors='ignore')
                log_func(f"[TCP] Received: {data}")
                if var_name:
                    set_variable_func(var_name, data)
                    if is_capture:
                        log_func(f"[CAPTURE] {var_name} = {data}")
                        import threading
                        curr_thread = threading.current_thread()
                        if not hasattr(curr_thread, "Captures"):
                            curr_thread.Captures = {}
                        curr_thread.Captures[var_name] = data
            else:
                raise RuntimeError("TCP Socket not connected. Run 'Connect' first.")

    elif block_type == "UTILITY":
        group = block.get("group", "List")
        action = block.get("action", "Join")
        var_name = block.get("variable_name", "")
        is_capture = block.get("is_capture", False)
        list_var = block.get("list_var_name", "")
        separator = block.get("separator", ",")
        
        res = ""
        if group == "List":
            if action == "Join":
                lst = variables.get(list_var, [])
                if isinstance(lst, str):
                    lst = [lst]
                res = separator.join([str(x) for x in lst])
            elif action == "Split":
                val = variables.get(list_var, "")
                res = val.split(separator)
                
        elif group == "File":
            if action == "Zip":
                path_to_zip = list_var
                target_zip = separator
                if os.path.exists(path_to_zip):
                    import zipfile
                    with zipfile.ZipFile(target_zip, 'w') as zipf:
                        if os.path.isdir(path_to_zip):
                            for root, dirs, files in os.walk(path_to_zip):
                                for file in files:
                                    zipf.write(os.path.join(root, file), 
                                               os.path.relpath(os.path.join(root, file), os.path.join(path_to_zip, '..')))
                        else:
                            zipf.write(path_to_zip, os.path.basename(path_to_zip))
                    res = f"Zipped to {target_zip}"
            elif action == "Clear":
                if os.path.exists(list_var):
                    with open(list_var, "w") as f:
                        f.write("")
                    res = "Cleared file content"
                    
        elif group == "System":
            if action == "Join":
                res = os.environ.get(list_var, "")
            else:
                res = str(time.time())
                
        if var_name:
            set_variable_func(var_name, res)
            log_func(f"[UTILITY] Group={group}, Action={action} -> Assigned variable <{var_name}> = '{str(res)[:100]}'")
            if is_capture:
                log_func(f"[CAPTURE] {var_name} = {res}")
                import threading
                curr_thread = threading.current_thread()
                if not hasattr(curr_thread, "Captures"):
                    curr_thread.Captures = {}
                curr_thread.Captures[var_name] = res
