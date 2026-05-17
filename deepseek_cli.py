import requests
import json
import sys
import os
import time
import atexit
import concurrent.futures
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Colors for UI
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
GRAY = '\033[90m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
RESET = '\033[0m'

sys.path.append(os.path.dirname(__file__))
from pow_solver.pow import DeepSeekPOW

TOKEN = "4Qn7z3tRCQLa+OI6sGqD313OcwQV0dFUOvoztChaTbuTFY5FHfN3m8GXBQGvkV1W"
COOKIES = {
    "aws-waf-token": "f1a1e45e-8294-44c7-a8e9-fe3b035d5817:BQoAjJVYIeILAAAA:9wYjt0sHghCsEL9A+mxacVW03Top24zoFDQGJ+G+69Q3Ec12Z4+8UI+78GXDwKUA+/v9/DoS81AnVhqOEW4OcdA8fWm2xW8IvmAZfywPhcuBR7FHTtkRIgXjdazpA59ZCUMt8iHdInH3W/vPSecDiB1+34zoejo69XK9JfpxpxvmmECVG767IPhSYEa5+rY=",
    "smidV2": "202605171743367e0a94fcabd251066a9f145a1ec3954b003acbfdcef91ebc0"
}

# Global list of sessions to clean up
active_sessions = []

def cleanup_all_sessions():
    if not active_sessions:
        return
    print(f"\n{GRAY}[System] Cleaning up {len(active_sessions)} chat sessions...{RESET}")
    for sid in active_sessions:
        try:
            requests.post(
                "https://chat.deepseek.com/api/v0/chat_session/delete",
                headers={"Authorization": f"Bearer {TOKEN}"},
                json={"chat_session_id": sid},
                cookies=COOKIES,
                timeout=5
            )
        except:
            pass
    active_sessions.clear()

atexit.register(cleanup_all_sessions)

class DeepSeekAgent:
    def __init__(self, name="DeepSeek", token=TOKEN, cookies=COOKIES):
        self.name = name
        self.token = token
        self.cookies = cookies
        self.pow_solver = DeepSeekPOW()
        self.session_id = None
        self.parent_msg_id = None
        
        self.thinking_enabled = False
        self.search_enabled = False
        self.model_class = "deepseek_chat" 
        
        self.req_session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.req_session.mount('https://', HTTPAdapter(max_retries=retries))
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Origin": "https://chat.deepseek.com",
            "Referer": "https://chat.deepseek.com/"
        }

    def _get_pow_header(self):
        try:
            pow_res = self.req_session.post("https://chat.deepseek.com/api/v0/chat/create_pow_challenge", headers=self.headers, json={"target_path": "/api/v0/chat/completion"}, cookies=self.cookies, timeout=10)
            pow_res.raise_for_status()
            return self.pow_solver.solve_challenge(pow_res.json()['data']['biz_data']['challenge'])
        except Exception:
            return ""

    def init_session(self, silent=False):
        if not silent:
            print(f"{GRAY}[{self.name}] Initializing session...{RESET}")
        res = self.req_session.post("https://chat.deepseek.com/api/v0/chat_session/create", headers=self.headers, json={"character_id": None}, cookies=self.cookies, timeout=10)
        res.raise_for_status()
        self.session_id = res.json()['data']['biz_data']['id']
        active_sessions.append(self.session_id)
        self.parent_msg_id = None

    def send_message(self, prompt, return_text=False):
        self.headers['x-ds-pow-response'] = self._get_pow_header()
        
        json_data = {
            'chat_session_id': self.session_id,
            'parent_message_id': self.parent_msg_id,
            'prompt': prompt,
            'ref_file_ids': [],
            'thinking_enabled': self.thinking_enabled,
            'search_enabled': self.search_enabled,
            'model_class': self.model_class 
        }

        if not return_text:
            print(f"{CYAN}{BOLD}{self.name}:{RESET} ", end='', flush=True)
            
        full_response = ""
        try:
            response = self.req_session.post("https://chat.deepseek.com/api/v0/chat/completion", headers=self.headers, json=json_data, cookies=self.cookies, stream=True, timeout=30)
            if response.status_code != 200:
                err = f"[Error] {response.status_code}: {response.text}"
                if not return_text: print(f"{RED}{err}{RESET}")
                return err

            current_response_id = None
            current_pointer = "response/content"
            is_thinking = False

            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            payload = line_str[6:]
                            if payload == "{}": continue
                            data = json.loads(payload)
                            
                            if current_response_id is None and "response_message_id" in data:
                                current_response_id = data["response_message_id"]
                                
                            if "p" in data:
                                current_pointer = data["p"]
                                
                            if "v" in data:
                                content = data["v"]
                                if not isinstance(content, str): continue
                                
                                if current_pointer == "response/thinking_content":
                                    if not return_text:
                                        if not is_thinking:
                                            print(f"\n{GRAY}[Thinking...]\n", end='', flush=True)
                                            is_thinking = True
                                        print(f"{GRAY}{content}{RESET}", end='', flush=True)
                                        
                                elif current_pointer == "response/content":
                                    if not return_text:
                                        if is_thinking:
                                            print(f"\n[End Thinking]\n{RESET}", end='', flush=True)
                                            is_thinking = False
                                        print(content, end='', flush=True)
                                    full_response += content
                                        
                                elif current_pointer == "response/message_id" and data.get("o") == "SET":
                                    current_response_id = data["v"]
                    except Exception:
                        pass
                        
            if not return_text: print()
            if current_response_id:
                self.parent_msg_id = current_response_id
                
            return full_response

        except Exception as e:
            err = f"[Connection Error] {e}"
            if not return_text: print(f"\n{RED}{err}{RESET}")
            return err

def worker_task(i, prompt):
    perspectives = [
        "Focus on direct, factual, and analytical breakdown.",
        "Focus on creative, out-of-the-box, and unconventional ideas.",
        "Focus on edge cases, potential risks, and downsides.",
        "Focus on summarizing the core essence with practical examples."
    ]
    agent = DeepSeekAgent(name=f"Worker-{i+1}")
    agent.model_class = "deepseek_chat" # Fast for workers
    agent.init_session(silent=True)
    worker_prompt = f"You are Expert {i+1}. {perspectives[i]}\nAnalyze this prompt: '{prompt}'"
    return agent.send_message(worker_prompt, return_text=True)

def interactive_cli():
    boss = DeepSeekAgent(name="Boss")
    boss.init_session(silent=True)
    
    swarm_mode = False
    
    # UI Header
    print(f"\n{MAGENTA}{BOLD}========================================={RESET}")
    print(f"{MAGENTA}{BOLD}       DeepSeek Advanced CLI UI          {RESET}")
    print(f"{MAGENTA}{BOLD}========================================={RESET}")
    print(f"{GREEN}Commands:{RESET}")
    print(f"  {YELLOW}/think{RESET}    - Toggle DeepThink (R1)")
    print(f"  {YELLOW}/search{RESET}   - Toggle Web Search")
    print(f"  {YELLOW}/expert{RESET}   - Switch to Expert model")
    print(f"  {YELLOW}/instant{RESET}  - Switch to Instant model")
    print(f"  {YELLOW}/swarm{RESET}    - Toggle Multi-Agent Swarm (Boss & 4 Workers)")
    print(f"  {YELLOW}/exit{RESET}     - Quit and cleanup chats")
    print(f"{GRAY}-----------------------------------------{RESET}\n")
    
    while True:
        try:
            # Build dynamic prompt indicator
            flags = []
            if swarm_mode: flags.append(f"{MAGENTA}SWARM{RESET}")
            if boss.model_class == "deepseek_reasoner": flags.append(f"{RED}EXPERT{RESET}")
            else: flags.append(f"{GREEN}INSTANT{RESET}")
            if boss.thinking_enabled: flags.append(f"{YELLOW}THINK{RESET}")
            if boss.search_enabled: flags.append(f"{CYAN}SEARCH{RESET}")
            
            indicator = f"[{'|'.join(flags)}]"
            user_input = input(f"\n{indicator} {BOLD}You:{RESET} ").strip()
            
            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                print(f"{YELLOW}Exiting gracefully...{RESET}")
                break
            elif user_input == "":
                continue
                
            # Slash Commands
            if user_input.startswith('/'):
                cmd = user_input.lower()
                if cmd == '/think':
                    boss.thinking_enabled = not boss.thinking_enabled
                    print(f"{GRAY}[System] DeepThink -> {boss.thinking_enabled}{RESET}")
                elif cmd == '/search':
                    boss.search_enabled = not boss.search_enabled
                    print(f"{GRAY}[System] Search -> {boss.search_enabled}{RESET}")
                elif cmd == '/expert':
                    boss.model_class = "deepseek_reasoner"
                    print(f"{GRAY}[System] Model -> EXPERT{RESET}")
                elif cmd == '/instant':
                    boss.model_class = "deepseek_chat"
                    print(f"{GRAY}[System] Model -> INSTANT{RESET}")
                elif cmd == '/swarm':
                    swarm_mode = not swarm_mode
                    print(f"{GRAY}[System] Swarm Mode -> {swarm_mode}{RESET}")
                else:
                    print(f"{RED}[System] Unknown command: {cmd}{RESET}")
                continue
            
            if swarm_mode:
                print(f"{MAGENTA}[Swarm] Dispatching task to 4 Expert Workers...{RESET}")
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [executor.submit(worker_task, i, user_input) for i in range(4)]
                    
                    # Simple spinner while waiting
                    spinners = ['|', '/', '-', '\\']
                    idx = 0
                    while not all(f.done() for f in futures):
                        print(f"\r{GRAY}Workers are brainstorming... {spinners[idx % 4]}{RESET}", end='', flush=True)
                        idx += 1
                        time.sleep(0.1)
                    print(f"\r{GREEN}[Swarm] 4 Experts responded! Boss is synthesizing final answer...{RESET}\n")
                    
                    responses = [f.result() for f in futures]
                
                boss_prompt = f"The user asked: '{user_input}'.\nHere are 4 perspectives from your expert workers:\n"
                for i, r in enumerate(responses):
                    boss_prompt += f"--- Expert {i+1} ---\n{r}\n\n"
                boss_prompt += "Please review all of them, extract the best insights, and provide a single, beautifully synthesized ultimate answer to the user."
                
                boss.send_message(boss_prompt)
            else:
                boss.send_message(user_input)
            
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted. Exiting...{RESET}")
            break
            
if __name__ == "__main__":
    interactive_cli()
