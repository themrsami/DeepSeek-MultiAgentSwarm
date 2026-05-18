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

try:
    from rich.console import Console
    from rich.console import Group
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    console = Console()
except ImportError:
    print("Please install rich: pip install rich")
    sys.exit(1)

# Colors for UI
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
GRAY = '\033[90m'
MAGENTA = '\033[95m'
BLUE = '\033[94m'
WHITE = '\033[97m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

sys.path.append(os.path.dirname(__file__))
from pow_solver.pow import DeepSeekPOW
from auth import load_auth, logout, interactive_login

# DeepSeek limits: ~8000 chars safe per-worker summary for boss prompt
# Total boss prompt should stay under ~32K chars to be safe
MAX_WORKER_RESPONSE_CHARS = 6000

# Global session tracking for cleanup
active_sessions = []
print_lock = threading.Lock()

def cleanup_all_sessions():
    if not active_sessions:
        return
        
    auth_data = load_auth()
    if not auth_data: return
    
    token = auth_data['token']
    cookie_dict = {}
    for c in auth_data['cookies'].split(';'):
        if '=' in c:
            k, v = c.strip().split('=', 1)
            cookie_dict[k] = v

    with print_lock:
        print(f"\n{GRAY}[Cleanup] Deleting {len(active_sessions)} sessions from your account...{RESET}", flush=True)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for sid in active_sessions:
        try:
            requests.post("https://chat.deepseek.com/api/v0/chat_session/delete", headers=headers, json={"chat_session_id": sid}, cookies=cookie_dict, timeout=5)
        except:
            pass
    with print_lock:
        print(f"{GREEN}[Cleanup] Done! All sessions wiped.{RESET}", flush=True)
    active_sessions.clear()

atexit.register(cleanup_all_sessions)

class DeepSeekAgent:
    def __init__(self, name="DeepSeek"):
        self.name = name
        
        auth_data = load_auth()
        if not auth_data:
            self.token = ""
            self.cookies = {}
        else:
            self.token = auth_data['token']
            cookie_dict = {}
            for c in auth_data['cookies'].split(';'):
                if '=' in c:
                    k, v = c.strip().split('=', 1)
                    cookie_dict[k] = v
            self.cookies = cookie_dict
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
            with print_lock:
                print(f"{GRAY}[{self.name}] Creating session...{RESET}", flush=True)
        res = self.req_session.post("https://chat.deepseek.com/api/v0/chat_session/create", headers=self.headers, json={"character_id": None}, cookies=self.cookies, timeout=10)
        res.raise_for_status()
        self.session_id = res.json()['data']['biz_data']['id']
        active_sessions.append(self.session_id)
        self.parent_msg_id = None

    def delete_all_chats(self):
        try:
            res = self.req_session.post('https://chat.deepseek.com/api/v0/chat_session/delete_all', headers=self.headers, cookies=self.cookies, timeout=10)
            return res.status_code == 200
        except Exception:
            return False

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
            console.print(f"\n[bold cyan]{self.name}:[/bold cyan]")
            
        full_response = ""
        thinking_response = ""
        
        live = None
        if not return_text:
            live = Live(console=console, refresh_per_second=15)
            live.start()
            
        try:
            response = self.req_session.post("https://chat.deepseek.com/api/v0/chat/completion", headers=self.headers, json=json_data, cookies=self.cookies, stream=True, timeout=60)
            if response.status_code != 200:
                err = f"[Error] {response.status_code}: {response.text}"
                if not return_text: console.print(f"[red]{err}[/red]")
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
                                    thinking_response += content
                                    if not return_text:
                                        live.update(Panel(thinking_response, title="Thinking...", border_style="yellow"))
                                        
                                elif current_pointer == "response/content":
                                    full_response += content
                                    if not return_text:
                                        if thinking_response:
                                            renderable = Group(
                                                Panel("Thinking process completed.", title="Thought Process", border_style="dim"),
                                                Markdown(full_response)
                                            )
                                        else:
                                            renderable = Markdown(full_response)
                                        live.update(renderable)
                                        
                                elif current_pointer == "response/message_id" and data.get("o") == "SET":
                                    current_response_id = data["v"]
                    except Exception:
                        pass
                        
            if current_response_id:
                self.parent_msg_id = current_response_id
                
            return full_response

        except Exception as e:
            err = f"[Connection Error] {e}"
            if not return_text: console.print(f"\n[red]{err}[/red]")
            return err
        finally:
            if live is not None:
                live.stop()


# ─────────────────────────────────────────────────────────

    def send_message_stream(self, prompt):
        """Generator that yields text chunks as they arrive from DeepSeek (for SSE streaming)."""
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
        
        try:
            response = self.req_session.post(
                "https://chat.deepseek.com/api/v0/chat/completion",
                headers=self.headers, json=json_data, cookies=self.cookies,
                stream=True, timeout=120
            )
            if response.status_code != 200:
                yield f"[Error] {response.status_code}: {response.text}"
                return

            current_response_id = None
            current_pointer = "response/content"

            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            payload = line_str[6:]
                            if payload == "{}": continue
                            data = __import__('json').loads(payload)
                            
                            if current_response_id is None and "response_message_id" in data:
                                current_response_id = data["response_message_id"]
                                
                            if "p" in data:
                                current_pointer = data["p"]
                                
                            if "v" in data:
                                content = data["v"]
                                if not isinstance(content, str): continue
                                
                                if current_pointer == "response/content":
                                    yield content
                                    
                            if current_pointer == "response/message_id" and data.get("o") == "SET":
                                current_response_id = data["v"]
                    except Exception:
                        pass
                        
            if current_response_id:
                self.parent_msg_id = current_response_id
                
        except Exception as e:
            yield f"[Connection Error] {e}"

#  SWARM ORCHESTRATOR
# ─────────────────────────────────────────────────────────

WORKER_PERSPECTIVES = [
    "You are the ANALYTICAL expert. Give a direct, factual, data-driven breakdown. Be precise and thorough.",
    "You are the CREATIVE expert. Think outside the box. Offer unconventional, innovative ideas and angles.",
    "You are the CRITICAL expert. Identify edge cases, potential risks, downsides, and things others might miss.",
    "You are the PRACTICAL expert. Focus on actionable advice, real-world examples, and step-by-step guidance.",
    "You are the RESEARCH expert. Provide deep background knowledge, references, and comprehensive context.",
    "You are the STRATEGIC expert. Think long-term. Consider scalability, future implications, and big-picture planning.",
]

WORKER_COLORS = [GREEN, CYAN, YELLOW, MAGENTA, BLUE, RED]


swarm_workers = []

def get_swarm_workers(num_workers):
    global swarm_workers
    if len(swarm_workers) < num_workers:
        print(f"\n{MAGENTA}{BOLD}╔══════════════════════════════════════╗{RESET}")
        print(f"{MAGENTA}{BOLD}║       INITIALIZING SWARM AGENTS      ║{RESET}")
        print(f"{MAGENTA}{BOLD}╚══════════════════════════════════════╝{RESET}")
        print(f"{GRAY}  Preparing persistent workers... (Only happens once){RESET}")
        
        for i in range(len(swarm_workers), num_workers):
            color = WORKER_COLORS[i % len(WORKER_COLORS)]
            agent = DeepSeekAgent(name=f"Worker-{i+1}")
            agent.model_class = "deepseek_chat"
            print(f"{color}    ● Worker-{i+1}: Creating session...{RESET}", end='', flush=True)
            agent.init_session(silent=True)
            print(f" {GREEN}✓{RESET}", flush=True)
            swarm_workers.append(agent)
            
    return swarm_workers[:num_workers]

def run_swarm(prompt, context_summary, boss_agent, num_workers=4, cli_mode=True):
    """Sequential persistent swarm pipeline to guarantee 100% success on free accounts."""
    workers = get_swarm_workers(num_workers)
    
    if cli_mode:
        print(f"\n{MAGENTA}{BOLD}╔══════════════════════════════════════╗{RESET}")
        print(f"{MAGENTA}{BOLD}║       SWARM MODE PROCESSING          ║{RESET}")
        print(f"{MAGENTA}{BOLD}╚══════════════════════════════════════╝{RESET}")
    
    ordered_responses = []
    worker_outputs = []
    
    for i, agent in enumerate(workers):
        color = WORKER_COLORS[i % len(WORKER_COLORS)]
        perspective = WORKER_PERSPECTIVES[i % len(WORKER_PERSPECTIVES)]
        
        # Build strict prompt for worker (injecting global context)
        worker_prompt = f"[{perspective}]\n\nRECENT CONVERSATION (Context):\n{context_summary}\n\nUSER REQUEST:\n{prompt}\n\nProvide your expert analysis based strictly on your assigned persona. Be concise."
        
        if cli_mode:
            print(f"  {color}▶ Worker-{i+1} is thinking...{RESET}", end='', flush=True)
        
        # Send message (blocks until stream is done) - auto retries if empty
        max_retries = 3
        response_text = ""
        for attempt in range(max_retries):
            # If not in CLI mode, we suppress outputs inside send_message
            response_text = agent.send_message(worker_prompt, return_text=True)
            if len(response_text) > 50:
                break
            time.sleep(2)
            
        char_count = len(response_text)
        status = f"{GREEN}OK{RESET}" if char_count > 50 else f"{RED}FAILED{RESET}"
        
        if cli_mode:
            print(f"\r  {color}✓ Worker-{i+1} responded! ({char_count} chars) [{status}]{RESET}   ")
            
        ordered_responses.append(response_text)
        worker_outputs.append({
            "worker": f"Worker-{i+1}",
            "perspective": perspective.split('.')[0].replace('You are the ', ''),
            "response": response_text
        })
    
    # ── Boss synthesizes ──
    if cli_mode:
        print(f"\n{YELLOW}{BOLD}  ⚡ Boss Agent is synthesizing the final answer...{RESET}\n")
    
    boss_prompt = f"The user asked: '{prompt}'.\n\nYour expert workers have analyzed this:\n\n"
    for i, r in enumerate(ordered_responses):
        label = WORKER_PERSPECTIVES[i % len(WORKER_PERSPECTIVES)].split('.')[0].replace('You are the ', '')
        if len(r) > 50:
            boss_prompt += f"═══ WORKER {i+1} ({label}) ═══\n{r}\n\n"
            
    boss_prompt += "Synthesize ONE comprehensive final answer. Resolve any contradictions. Do NOT mention the workers or boss."
    
    if cli_mode:
        boss_final = boss_agent.send_message(boss_prompt)
        return boss_final
    else:
        boss_final = boss_agent.send_message(boss_prompt, return_text=True)
        return {
            "boss_response": boss_final,
            "worker_responses": worker_outputs
        }


# ─────────────────────────────────────────────────────────
#  INTERACTIVE CLI
# ─────────────────────────────────────────────────────────

def interactive_cli():
    # Banner
    print(f"""
{MAGENTA}{BOLD}╔══════════════════════════════════════════╗
║     DeepSeek MultiAgent Swarm CLI        ║
╚══════════════════════════════════════════╝{RESET}

{WHITE}{BOLD}Toggle Commands:{RESET}
  {YELLOW}/think{RESET}       Toggle DeepThink (R1 reasoning)     {GRAY}[combinable]{RESET}
  {YELLOW}/search{RESET}      Toggle Web Search                   {GRAY}[combinable]{RESET}
  {YELLOW}/expert{RESET}      Switch to Expert model               {GRAY}[exclusive]{RESET}
  {YELLOW}/instant{RESET}     Switch to Instant model              {GRAY}[exclusive]{RESET}

{WHITE}{BOLD}Swarm Commands:{RESET}
  {MAGENTA}/swarm{RESET}       Toggle multi-agent swarm mode
  {MAGENTA}/agents N{RESET}    Set number of swarm workers (2-6)

{WHITE}{BOLD}Session & Data:{RESET}
  {GREEN}/login{RESET}       Login via Browser
  {RED}/logout{RESET}      Logout and remove credentials
  {RED}/clearall{RESET}    Delete all chats from DeepSeek account
  {RED}/exit{RESET}        Quit & auto-delete all sessions
  {CYAN}/help{RESET}        Show this menu again

{GRAY}──────────────────────────────────────────{RESET}
{GRAY}  Think + Search can be ON at same time.
  Expert/Instant are mutually exclusive.
  Swarm mode uses N workers + 1 boss.
  All sessions auto-cleanup on exit.{RESET}
{GRAY}──────────────────────────────────────────{RESET}
""")

    boss = None
    swarm_mode = False
    num_workers = 4
    conversation_context = []
    
    # Check Auth
    if not load_auth():
        print(f"{YELLOW}[Warning] You are not logged in!{RESET}")
        print(f"{GRAY}Type /login to authenticate via browser.{RESET}\n")
    else:
        boss = DeepSeekAgent(name="DeepSeek")
        try:
            boss.init_session(silent=True)
        except Exception:
            print(f"{RED}[Error] Failed to initialize. Is your token expired? Type /login to re-authenticate.{RESET}\n")
            boss = None
    
    while True:
        try:
            # Build status bar
            flags = []
            if swarm_mode: flags.append(f"{MAGENTA}SWARM({num_workers}){RESET}")
            if boss and boss.model_class == "deepseek_reasoner": flags.append(f"{RED}EXPERT{RESET}")
            elif boss and boss.model_class == "deepseek_chat": flags.append(f"{CYAN}INSTANT{RESET}")
            if boss and getattr(boss, 'thinking_enabled', False): flags.append(f"{YELLOW}THINKING{RESET}")
            if boss and getattr(boss, 'search_enabled', False): flags.append(f"{BLUE}SEARCH{RESET}")
            
            indicator = f"[{'|'.join(flags)}]"
            user_input = input(f"\n{indicator} {BOLD}You:{RESET} ").strip()
            
            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                print(f"{YELLOW}Exiting gracefully...{RESET}")
                break
            elif user_input == "":
                continue
                
            # Slash Commands
            if user_input.startswith('/'):
                cmd_parts = user_input.lower().split()
                cmd = cmd_parts[0]
                
                if cmd == '/think':
                    boss.thinking_enabled = not boss.thinking_enabled
                    state = f"{GREEN}ON{RESET}" if boss.thinking_enabled else f"{RED}OFF{RESET}"
                    print(f"{GRAY}[System]{RESET} DeepThink → {state}")
                elif cmd == '/search':
                    boss.search_enabled = not boss.search_enabled
                    state = f"{GREEN}ON{RESET}" if boss.search_enabled else f"{RED}OFF{RESET}"
                    print(f"{GRAY}[System]{RESET} Web Search → {state}")
                elif cmd == '/expert':
                    boss.model_class = "deepseek_reasoner"
                    print(f"{GRAY}[System]{RESET} Model → {RED}EXPERT{RESET}")
                elif cmd == '/instant':
                    boss.model_class = "deepseek_chat"
                    print(f"{GRAY}[System]{RESET} Model → {GREEN}INSTANT{RESET}")
                elif cmd == '/swarm':
                    swarm_mode = not swarm_mode
                    state = f"{GREEN}ON{RESET}" if swarm_mode else f"{RED}OFF{RESET}"
                    print(f"{GRAY}[System]{RESET} Swarm Mode → {state} {GRAY}({num_workers} workers){RESET}")
                elif cmd == '/agents':
                    if len(cmd_parts) > 1:
                        try:
                            n = int(cmd_parts[1])
                            if 2 <= n <= 6:
                                num_workers = n
                                print(f"{GRAY}[System]{RESET} Swarm workers → {MAGENTA}{num_workers}{RESET}")
                            else:
                                print(f"{RED}[System] Workers must be between 2-6{RESET}")
                        except ValueError:
                            print(f"{RED}[System] Usage: /agents 4{RESET}")
                    else:
                        print(f"{GRAY}[System] Current workers: {num_workers}. Usage: /agents N (2-6){RESET}")
                elif cmd == '/help':
                    print(f"""
{WHITE}{BOLD}Toggle Commands:{RESET}
  {YELLOW}/think{RESET}       Toggle DeepThink     {YELLOW}/search{RESET}      Toggle Search
  {YELLOW}/expert{RESET}      Expert model          {YELLOW}/instant{RESET}     Instant model
{WHITE}{BOLD}Swarm:{RESET}
  {MAGENTA}/swarm{RESET}       Toggle swarm          {MAGENTA}/agents N{RESET}    Set workers (2-6)
{WHITE}{BOLD}Session & Auth:{RESET}
  {GREEN}/login{RESET}       Login via Browser     {RED}/logout{RESET}       Logout
  {RED}/clearall{RESET}    Clear all chats       {RED}/exit{RESET}        Quit & cleanup
  {CYAN}/help{RESET}         This menu""")
                elif cmd == '/login':
                    if interactive_login():
                        # Re-initialize Boss
                        boss = DeepSeekAgent(name="DeepSeek")
                        boss.init_session(silent=True)
                        print(f"{GREEN}[System] Boss agent ready!{RESET}")
                elif cmd == '/logout':
                    save_auth(None)
                    boss = None
                    print(f"{GREEN}[Success] Logged out successfully. Credentials removed.{RESET}")
                    print(f"{GRAY}Type /login to re-authenticate.{RESET}")
                elif cmd == '/clearall':
                    if boss is None:
                        print(f"{RED}[Error] You must be logged in to clear chats.{RESET}")
                        continue
                    confirm = input(f"{RED}Are you sure you want to permanently delete ALL chats from your DeepSeek account? (y/n): {RESET}")
                    if confirm.lower() == 'y':
                        print(f"{YELLOW}Deleting all chats...{RESET}")
                        success = boss.delete_all_chats()
                        if success:
                            print(f"{GREEN}[Success] All chat history has been permanently deleted.{RESET}")
                        else:
                            print(f"{RED}[Error] Failed to delete chats. Token might be expired.{RESET}")
                else:
                    print(f"{RED}[System] Unknown: {cmd}. Type /help{RESET}")
                continue
            
            if boss is None:
                print(f"{RED}[Error] You must /login before sending messages.{RESET}")
                continue
                
            # Track conversation for context
            conversation_context.append(f"User: {user_input}")
            
            if swarm_mode:
                context_summary = "\n".join(conversation_context[-6:])
                if len(context_summary) > 2000:
                    context_summary = context_summary[-2000:]
                
                response = run_swarm(user_input, context_summary, boss, num_workers)
                if response:
                    # Keep a short summary of the Boss response for context
                    summary = response[:300] + "..." if len(response) > 300 else response
                    conversation_context.append(f"DeepSeek: {summary}")
            else:
                response = boss.send_message(user_input)
                if response:
                    summary = response[:300] + "..." if len(response) > 300 else response
                    conversation_context.append(f"DeepSeek: {summary}")
            
            # Keep context window manageable (last 10 exchanges)
            if len(conversation_context) > 20:
                conversation_context = conversation_context[-20:]
            
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted. Exiting...{RESET}")
            break
            
if __name__ == "__main__":
    interactive_cli()
