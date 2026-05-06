#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  MeshNet Worker — Agente de render Blender                   ║
║                                                              ║
║  Roda em background, conecta ao HOST via Supabase Realtime,  ║
║  detecta o Blender automaticamente e processa jobs de render  ║
║  com prioridade baixa (segundo/terceiro plano).              ║
║                                                              ║
║  USO:                                                        ║
║    pip install supabase websockets psutil requests           ║
║    python meshnet_worker.py                                  ║
║                                                              ║
║  OPÇÕES:                                                      ║
║    --name  "meu-pc"           apelido deste worker           ║
║    --blender "/path/blender"  caminho manual do Blender      ║
║    --threads 4                número de threads de render    ║
║    --priority low|normal      prioridade do processo         ║
║    --output ./renders         pasta de saída dos frames      ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import logging
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path

# ── Verificar dependências ──────────────────────────────────
MISSING = []
try:    import psutil
except: MISSING.append("psutil")
try:    import requests
except: MISSING.append("requests")
try:    import websockets
except: MISSING.append("websockets")

if MISSING:
    print(f"\n[ERRO] Instale as dependências:\n")
    print(f"  pip install {' '.join(MISSING)}\n")
    sys.exit(1)

import psutil
import requests

# ════════════════════════════════════════════════════════════
#  CONFIG SUPABASE
# ════════════════════════════════════════════════════════════
SB_URL = "https://wvzaeoezostmydkpqelt.supabase.co"
SB_KEY = "sb_publishable_sYPZqHBknaVtEr1dS0eILQ_0ViliBl6"
SB_WS  = "wss://wvzaeoezostmydkpqelt.supabase.co/realtime/v1/websocket"

CHANNEL_LOBBY = "meshnet:boinc:lobby:v1"
CHANNEL_ROOM  = "meshnet:boinc:room:v1:"   # + room_id

# ════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("meshnet_worker.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("meshnet")

def banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║              MeshNet Worker — Blender Farm                   ║
╚══════════════════════════════════════════════════════════════╝""")

# ════════════════════════════════════════════════════════════
#  DETECÇÃO DO BLENDER
# ════════════════════════════════════════════════════════════
BLENDER_PATHS = {
    "Windows": [
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    ],
    "Darwin": [  # macOS
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender.app/Contents/MacOS/blender",
        "/opt/homebrew/bin/blender",
        "/usr/local/bin/blender",
    ],
    "Linux": [
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "/snap/bin/blender",
        "/opt/blender/blender",
        os.path.expanduser("~/blender/blender"),
        os.path.expanduser("~/.local/bin/blender"),
    ],
}

def find_blender(manual_path: str = None) -> str | None:
    """Localiza o executável do Blender no sistema."""

    # 1. Caminho manual
    if manual_path and Path(manual_path).is_file():
        log.info(f"Blender encontrado (manual): {manual_path}")
        return manual_path

    # 2. PATH do sistema
    found = shutil.which("blender")
    if found:
        log.info(f"Blender encontrado no PATH: {found}")
        return found

    # 3. Caminhos comuns por OS
    system = platform.system()
    paths  = BLENDER_PATHS.get(system, [])
    for p in paths:
        if Path(p).is_file():
            log.info(f"Blender encontrado: {p}")
            return p

    # 4. Windows: busca no registro
    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\BlenderFoundation\Blender")
            path = winreg.QueryValueEx(key, "Install_Dir")[0]
            exe  = Path(path) / "blender.exe"
            if exe.is_file():
                log.info(f"Blender encontrado no registro: {exe}")
                return str(exe)
        except Exception:
            pass

    return None

def get_blender_version(blender_exe: str) -> str:
    """Retorna a versão do Blender."""
    try:
        result = subprocess.run(
            [blender_exe, "--version"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if "Blender" in line:
                return line.strip()
    except Exception:
        pass
    return "versão desconhecida"

# ════════════════════════════════════════════════════════════
#  INFORMAÇÕES DO SISTEMA
# ════════════════════════════════════════════════════════════
def get_system_info() -> dict:
    """Coleta informações de hardware do worker."""
    cpu_count  = psutil.cpu_count(logical=True)
    cpu_phys   = psutil.cpu_count(logical=False)
    cpu_freq   = psutil.cpu_freq()
    ram        = psutil.virtual_memory()
    disk       = psutil.disk_usage("/")

    return {
        "os":           platform.system(),
        "os_version":   platform.version()[:50],
        "hostname":     platform.node(),
        "cpu_count":    cpu_count,
        "cpu_physical": cpu_phys,
        "cpu_freq_mhz": int(cpu_freq.max) if cpu_freq else 0,
        "ram_total_gb": round(ram.total / 1e9, 1),
        "disk_free_gb": round(disk.free / 1e9, 1),
        "cpu_avail":    round(100 - psutil.cpu_percent(interval=1), 1),
        "ram_avail_gb": round(ram.available / 1e9, 1),
    }

def set_process_priority(priority: str):
    """Define prioridade baixa para não interferir no uso normal."""
    try:
        proc = psutil.Process(os.getpid())
        if priority == "low":
            if platform.system() == "Windows":
                proc.nice(psutil.IDLE_PRIORITY_CLASS)
            else:
                proc.nice(19)  # mínima prioridade no Unix
            log.info("Prioridade do processo: BAIXA (segundo plano)")
        elif priority == "normal":
            proc.nice(0)
            log.info("Prioridade do processo: NORMAL")
    except Exception as e:
        log.warning(f"Não foi possível alterar prioridade: {e}")

# ════════════════════════════════════════════════════════════
#  RENDER COM BLENDER
# ════════════════════════════════════════════════════════════
def render_frames(
    blender_exe: str,
    blend_file:  str,
    output_dir:  str,
    frames:      list[int],
    render_engine: str = "CYCLES",
    samples:     int   = 128,
    threads:     int   = 0,  # 0 = auto
    resolution_x: int  = 0,  # 0 = usa o da cena
    resolution_y: int  = 0,
    on_frame_done = None,
) -> list[dict]:
    """
    Renderiza uma lista de frames usando Blender headless.
    Retorna lista de {frame, path, success, elapsed}.
    """
    results = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Script Python inline que o Blender executa
    blender_script = f"""
import bpy, os, sys

# Configurações de render
scene = bpy.context.scene
scene.render.engine = '{render_engine}'
scene.render.filepath = r'{str(output_path)}/'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

if {threads} > 0:
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = {threads}
else:
    scene.render.threads_mode = 'AUTO'

if {resolution_x} > 0:
    scene.render.resolution_x = {resolution_x}
    scene.render.resolution_y = {resolution_y}
    scene.render.resolution_percentage = 100

if '{render_engine}' == 'CYCLES':
    scene.cycles.samples = {samples}
    scene.cycles.use_denoising = True

print(f"[MeshNet] Engine: {{scene.render.engine}}")
print(f"[MeshNet] Resolução: {{scene.render.resolution_x}}x{{scene.render.resolution_y}}")
print(f"[MeshNet] Saída: {{scene.render.filepath}}")
"""

    for frame in frames:
        frame_start = time.time()
        # Arquivo de saída esperado
        out_file = output_path / f"{frame:04d}.png"

        # Comando Blender headless
        cmd = [
            blender_exe,
            "--background",
            blend_file,
            "--python-expr", blender_script,
            "--render-frame", str(frame),
        ]

        log.info(f"  Renderizando frame {frame}...")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Define prioridade baixa para o processo do Blender
            try:
                bp = psutil.Process(proc.pid)
                if platform.system() == "Windows":
                    bp.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                else:
                    bp.nice(15)
            except Exception:
                pass

            # Lê output em tempo real
            for line in proc.stdout:
                line = line.strip()
                if line and any(k in line for k in ["Fra:", "Time:", "Memory", "MeshNet", "Error", "Warn"]):
                    log.debug(f"  [blender] {line}")

            proc.wait()
            elapsed = round(time.time() - frame_start, 2)

            # Procura o arquivo gerado (Blender pode adicionar sufixo)
            found_file = None
            for ext in [".png", ".jpg", ".jpeg", ".exr"]:
                candidates = [
                    out_file.with_suffix(ext),
                    output_path / f"{frame:04d}{ext}",
                    output_path / f"frame{frame:04d}{ext}",
                ]
                for c in candidates:
                    if c.is_file():
                        found_file = c
                        break
                if found_file:
                    break

            if proc.returncode == 0 and found_file:
                log.info(f"  ✓ Frame {frame} pronto em {elapsed}s → {found_file.name}")
                result = {
                    "frame":   frame,
                    "path":    str(found_file),
                    "success": True,
                    "elapsed": elapsed,
                    "size_kb": round(found_file.stat().st_size / 1024, 1),
                }
                if on_frame_done:
                    on_frame_done(result)
            else:
                log.error(f"  ✗ Frame {frame} falhou (code={proc.returncode})")
                result = {
                    "frame":   frame,
                    "path":    None,
                    "success": False,
                    "elapsed": elapsed,
                    "error":   f"Blender retornou código {proc.returncode}",
                }

        except Exception as e:
            elapsed = round(time.time() - frame_start, 2)
            log.error(f"  ✗ Frame {frame} erro: {e}")
            result = {
                "frame": frame, "path": None,
                "success": False, "elapsed": elapsed, "error": str(e),
            }

        results.append(result)

    return results

# ════════════════════════════════════════════════════════════
#  DOWNLOAD DO ARQUIVO .BLEND
# ════════════════════════════════════════════════════════════
def download_blend(url: str, dest_dir: str) -> str | None:
    """Baixa o arquivo .blend do HOST e salva localmente."""
    try:
        log.info(f"  Baixando .blend de {url[:60]}...")
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()
        dest = Path(dest_dir) / "scene.blend"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        size_mb = round(dest.stat().st_size / 1e6, 1)
        log.info(f"  .blend baixado: {size_mb}MB → {dest}")
        return str(dest)
    except Exception as e:
        log.error(f"  Falha ao baixar .blend: {e}")
        return None

# ════════════════════════════════════════════════════════════
#  CLIENTE SUPABASE REALTIME (WebSocket)
# ════════════════════════════════════════════════════════════
class SupabaseRealtimeClient:
    """
    Cliente WebSocket minimalista para Supabase Realtime.
    Implementa Presence (anunciar presença) e Broadcast (mensagens).
    """

    def __init__(self, url, key):
        self.url    = url
        self.key    = key
        self.ws     = None
        self.ref    = 0
        self.joined = set()
        self._handlers  = {}   # channel → list of (event, callback)
        self._pending   = {}   # ref → future
        self._running   = False
        self._presence_state = {}

    def _next_ref(self):
        self.ref += 1
        return str(self.ref)

    def _ws_url(self):
        return (f"{self.url.replace('https://','wss://').replace('http://','ws://')}"
                f"/realtime/v1/websocket?apikey={self.key}&vsn=1.0.0")

    async def connect(self):
        import websockets
        ws_url = self._ws_url()
        log.info(f"Conectando ao Supabase Realtime...")
        self.ws = await websockets.connect(
            ws_url,
            extra_headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"},
            ping_interval=25,
            ping_timeout=10,
        )
        self._running = True
        log.info("✓ WebSocket Supabase conectado")

    async def listen(self):
        """Loop principal de recebimento de mensagens."""
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
                await self._dispatch(msg)
            except Exception as e:
                log.debug(f"Erro ao processar msg: {e}")

    async def _dispatch(self, msg):
        topic  = msg.get("topic", "")
        event  = msg.get("event", "")
        payload= msg.get("payload", {})
        ref    = msg.get("ref")

        # Resolve pendentes
        if ref and ref in self._pending:
            self._pending[ref].set_result(msg)
            del self._pending[ref]
            return

        # Heartbeat do servidor
        if event == "heartbeat":
            await self._send({"topic":"phoenix","event":"heartbeat",
                               "payload":{},"ref":self._next_ref()})
            return

        # Presence state sync
        if event == "presence_state":
            self._presence_state[topic] = payload
            await self._call_handlers(topic, "presence_sync", payload)
            return

        if event == "presence_diff":
            joins  = payload.get("joins", {})
            leaves = payload.get("leaves", {})
            state  = self._presence_state.get(topic, {})
            state.update(joins)
            for k in leaves: state.pop(k, None)
            self._presence_state[topic] = state
            if joins:  await self._call_handlers(topic,"presence_join", joins)
            if leaves: await self._call_handlers(topic,"presence_leave",leaves)
            return

        # Broadcast
        if event == "broadcast":
            await self._call_handlers(topic, "broadcast", payload)
            return

    async def _call_handlers(self, topic, event, payload):
        for (ch, ev, cb) in self._handlers.get(topic, []):
            if ev == event or ev == "*":
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(payload)
                    else:
                        cb(payload)
                except Exception as e:
                    log.error(f"Handler erro: {e}")

    async def _send(self, msg):
        if self.ws and not self.ws.closed:
            await self.ws.send(json.dumps(msg))

    async def join_channel(self, topic, config=None):
        """Assina um canal Supabase."""
        ref = self._next_ref()
        params = {
            "config": config or {
                "broadcast": {"self": False, "ack": False},
                "presence": {},
            }
        }
        await self._send({
            "topic": topic,
            "event": "phx_join",
            "payload": params,
            "ref": ref,
        })
        self.joined.add(topic)
        log.debug(f"Canal {topic} assinado")
        await asyncio.sleep(0.5)  # aguarda confirmação

    async def track(self, topic, payload):
        """Anuncia presença em um canal."""
        await self._send({
            "topic": topic,
            "event": "presence",
            "payload": {"type": "presence", "event": "track", "payload": payload},
            "ref": self._next_ref(),
        })

    async def broadcast(self, topic, event, payload):
        """Envia mensagem broadcast para um canal."""
        await self._send({
            "topic": topic,
            "event": "broadcast",
            "payload": {"type": "broadcast", "event": event, "payload": payload},
            "ref": self._next_ref(),
        })

    def on(self, topic, event, callback):
        """Registra handler para um evento de um canal."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append((topic, event, callback))

    async def untrack(self, topic):
        await self._send({
            "topic": topic,
            "event": "presence",
            "payload": {"type": "presence", "event": "untrack"},
            "ref": self._next_ref(),
        })

# ════════════════════════════════════════════════════════════
#  WORKER PRINCIPAL
# ════════════════════════════════════════════════════════════
class MeshNetWorker:

    def __init__(self, args):
        self.worker_id  = str(uuid.uuid4())[:8]
        self.name       = args.name or platform.node()
        self.blender    = args.blender
        self.threads    = args.threads
        self.priority   = args.priority
        self.output_dir = Path(args.output).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.room_id    = None
        self.sysinfo    = {}
        self.blender_ver= "não encontrado"
        self.client     = None
        self.running    = True
        self.current_job= None

        self._job_queue = asyncio.Queue()

    async def setup(self):
        """Inicializa hardware e detecta Blender."""
        log.info("Coletando informações do sistema...")
        self.sysinfo = get_system_info()

        # Detecta Blender
        blender_path = find_blender(self.blender)
        if blender_path:
            self.blender = blender_path
            self.blender_ver = get_blender_version(blender_path)
            log.info(f"Blender: {self.blender_ver}")
        else:
            log.warning("⚠ Blender não encontrado. Jobs de render serão recusados.")
            log.warning("  Instale o Blender ou use --blender /caminho/para/blender")

        # Prioridade do processo
        set_process_priority(self.priority)

        log.info(f"Worker ID: {self.worker_id}")
        log.info(f"Nome: {self.name}")
        log.info(f"Sistema: {self.sysinfo['os']} | "
                 f"CPU: {self.sysinfo['cpu_count']} cores | "
                 f"RAM: {self.sysinfo['ram_total_gb']}GB")
        log.info(f"Saída: {self.output_dir}")

    async def run(self):
        """Loop principal do worker."""
        await self.setup()

        while self.running:
            try:
                await self._connect_and_run()
            except Exception as e:
                log.error(f"Erro de conexão: {e}")
                log.info("Reconectando em 8s...")
                await asyncio.sleep(8)

    async def _connect_and_run(self):
        """Conecta ao Supabase e entra no lobby."""
        self.client = SupabaseRealtimeClient(SB_URL, SB_KEY)
        await self.client.connect()

        # Assina canal do lobby
        lobby_topic = f"realtime:{CHANNEL_LOBBY}"
        await self.client.join_channel(lobby_topic)

        # Handler: HOST anuncia projeto no lobby
        self.client.on(lobby_topic, "presence_join", self._on_lobby_presence)
        self.client.on(lobby_topic, "presence_sync", self._on_lobby_sync)
        self.client.on(lobby_topic, "broadcast",     self._on_lobby_broadcast)

        # Anuncia presença no lobby
        await self.client.track(lobby_topic, {
            "type":        "WORKER_LOBBY",
            "worker_id":   self.worker_id,
            "name":        self.name,
            "blender":     bool(self.blender),
            "blender_ver": self.blender_ver,
            "os":          self.sysinfo["os"],
            "cpu_count":   self.sysinfo["cpu_count"],
            "ram_gb":      self.sysinfo["ram_total_gb"],
        })

        log.info("✓ Conectado ao lobby — aguardando projetos...")
        log.info("  (Pressione Ctrl+C para encerrar)\n")

        # Inicia processador de jobs em paralelo
        asyncio.ensure_future(self._job_processor())

        # Heartbeat periódico
        asyncio.ensure_future(self._heartbeat_loop())

        # Loop de recebimento
        await self.client.listen()

    async def _on_lobby_sync(self, payload):
        """Ao sincronizar presença do lobby — descobre projetos abertos."""
        for key, presences in payload.items():
            for p in (presences if isinstance(presences, list) else [presences]):
                if p.get("type") == "ROOM" and not self.room_id:
                    # Encontrou um projeto aberto — entra automaticamente
                    log.info(f"Projeto descoberto: {p.get('room_name')} (ID:{p.get('room_id')})")
                    # Aguarda um pouco para não entrar em todos de uma vez
                    await asyncio.sleep(1)
                    if not self.room_id:
                        await self._join_project(p.get("room_id"))

    async def _on_lobby_presence(self, joins):
        """Novo HOST anunciou projeto no lobby."""
        for key, presences in joins.items():
            for p in (presences if isinstance(presences, list) else [presences]):
                if p.get("type") == "ROOM" and not self.room_id:
                    log.info(f"Novo projeto: {p.get('room_name')} (ID:{p.get('room_id')})")
                    await asyncio.sleep(1)
                    if not self.room_id:
                        await self._join_project(p.get("room_id"))

    async def _on_lobby_broadcast(self, payload):
        pass  # Reservado

    async def _join_project(self, room_id: str):
        """Entra em um projeto como worker."""
        self.room_id = room_id
        room_topic   = f"realtime:{CHANNEL_ROOM}{room_id}"

        await self.client.join_channel(room_topic, {
            "broadcast": {"self": False, "ack": False},
            "presence":  {},
        })

        # Handler de mensagens da sala
        self.client.on(room_topic, "broadcast", self._on_room_msg)

        # Anuncia presença na sala
        info = get_system_info()
        await self.client.track(room_topic, {
            "type":      "WORKER",
            "worker_id": self.worker_id,
            "name":      self.name,
            "os":        info["os"],
            "cpu_avail": info["cpu_avail"],
            "ram_avail": info["ram_avail_gb"],
            "cpu_count": info["cpu_count"],
            "ram_total": info["ram_total_gb"],
            "blender":   bool(self.blender),
            "blender_ver": self.blender_ver,
        })

        # Pede estado atual
        await self.client.broadcast(room_topic, "msg", {
            "type": "GET_STATE",
            "from": self.worker_id,
        })

        log.info(f"✓ Entrou no projeto {room_id} como worker")

    async def _on_room_msg(self, payload):
        """Recebe mensagens do canal da sala."""
        msg = payload.get("payload", payload)
        t   = msg.get("type", "")

        if t == "RENDER_JOB" and msg.get("target") == self.worker_id:
            if not self.blender:
                log.warning("Job recusado — Blender não instalado")
                await self._send_result_error(msg, "Blender não encontrado neste worker")
                return
            if self.current_job:
                log.warning(f"Job {msg.get('job_id')} recusado — já processando outro")
                return
            await self._job_queue.put(msg)

        elif t == "ROOM_STATE":
            # Atualiza métricas exibidas
            state = msg.get("state", {})
            if state:
                ac = state.get("active_count", 0)
                log.debug(f"Estado: {ac} worker(s) na sala")

        elif t == "HB":
            pass  # heartbeat de outros workers

    async def _job_processor(self):
        """Processador de jobs em background."""
        while self.running:
            try:
                job = await asyncio.wait_for(self._job_queue.get(), timeout=5.0)
                await self._process_job(job)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                log.error(f"Erro no processador de jobs: {e}")

    async def _process_job(self, msg: dict):
        """Processa um job de render."""
        job_id      = msg.get("job_id")
        frames      = msg.get("frames", [])
        chunk_idx   = msg.get("chunk_index", 0)
        total_chunks= msg.get("total_chunks", 1)
        blend_url   = msg.get("blend_url")    # URL para download do .blend
        blend_path  = msg.get("blend_path")   # caminho local se na mesma máquina
        engine      = msg.get("engine", "CYCLES")
        samples     = msg.get("samples", 128)
        res_x       = msg.get("resolution_x", 0)
        res_y       = msg.get("resolution_y", 0)

        self.current_job = job_id
        room_topic = f"realtime:{CHANNEL_ROOM}{self.room_id}"

        log.info(f"\n{'='*55}")
        log.info(f"  Job {job_id} · chunk {chunk_idx+1}/{total_chunks}")
        log.info(f"  Frames: {frames}")
        log.info(f"  Engine: {engine} · Samples: {samples}")
        log.info(f"{'='*55}")

        # Notifica HOST que começou
        await self.client.broadcast(room_topic, "msg", {
            "type":        "JOB_STARTED",
            "job_id":      job_id,
            "from":        self.worker_id,
            "chunk_index": chunk_idx,
            "frames":      frames,
        })

        # Obtém o arquivo .blend
        work_dir = self.output_dir / f"job_{job_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        if blend_url:
            # Download do arquivo
            blend_file = await asyncio.get_event_loop().run_in_executor(
                None, download_blend, blend_url, str(work_dir)
            )
            if not blend_file:
                await self._send_result_error(
                    {"job_id":job_id,"chunk_index":chunk_idx}, "Falha ao baixar .blend")
                self.current_job = None
                return
        elif blend_path and Path(blend_path).is_file():
            blend_file = blend_path
        else:
            log.error("Nenhum arquivo .blend disponível para este job")
            await self._send_result_error(
                {"job_id":job_id,"chunk_index":chunk_idx}, "Arquivo .blend não disponível")
            self.current_job = None
            return

        # Renderiza em thread separada (não bloqueia o event loop)
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: render_frames(
                blender_exe    = self.blender,
                blend_file     = blend_file,
                output_dir     = str(work_dir),
                frames         = frames,
                render_engine  = engine,
                samples        = samples,
                threads        = self.threads,
                resolution_x   = res_x,
                resolution_y   = res_y,
                on_frame_done  = lambda r: log.info(f"  ✓ Frame {r['frame']} → {r.get('size_kb',0)}KB"),
            )
        )

        # Monta resultado
        frames_ok  = [r for r in results if r["success"]]
        frames_err = [r for r in results if not r["success"]]
        total_time = sum(r["elapsed"] for r in results)

        log.info(f"\n  Resultado: {len(frames_ok)}/{len(results)} frames OK em {total_time:.1f}s")

        # Envia resultado ao HOST
        await self.client.broadcast(room_topic, "msg", {
            "type":        "RENDER_RESULT",
            "job_id":      job_id,
            "from":        self.worker_id,
            "chunk_index": chunk_idx,
            "results": [
                {
                    "frame":   r["frame"],
                    "path":    r["path"],
                    "success": r["success"],
                    "elapsed": r["elapsed"],
                    "size_kb": r.get("size_kb", 0),
                    "error":   r.get("error"),
                }
                for r in results
            ],
            "summary": {
                "frames_ok":   len(frames_ok),
                "frames_err":  len(frames_err),
                "total_time_s": round(total_time, 2),
                "worker":      self.name,
            }
        })

        self.current_job = None
        log.info(f"  Job {job_id} enviado ao HOST ✓\n")

    async def _send_result_error(self, msg, error_msg):
        if not self.room_id: return
        room_topic = f"realtime:{CHANNEL_ROOM}{self.room_id}"
        await self.client.broadcast(room_topic, "msg", {
            "type":        "RENDER_RESULT",
            "job_id":      msg.get("job_id"),
            "from":        self.worker_id,
            "chunk_index": msg.get("chunk_index", 0),
            "results":     [],
            "error":       error_msg,
        })

    async def _heartbeat_loop(self):
        """Envia heartbeat periódico com métricas atualizadas."""
        while self.running and self.room_id:
            await asyncio.sleep(10)
            if not self.room_id: break
            info = get_system_info()
            room_topic = f"realtime:{CHANNEL_ROOM}{self.room_id}"
            try:
                await self.client.broadcast(room_topic, "msg", {
                    "type":      "HB",
                    "from":      self.worker_id,
                    "cpu_avail": info["cpu_avail"],
                    "ram_avail": info["ram_avail_gb"],
                    "busy":      bool(self.current_job),
                })
            except Exception:
                break

    def stop(self):
        self.running = False
        log.info("\nWorker encerrado.")

# ════════════════════════════════════════════════════════════
#  ENTRYPOINT
# ════════════════════════════════════════════════════════════
def parse_args():
    import argparse
    p = argparse.ArgumentParser(
        description="MeshNet Worker — agente de render Blender distribuído",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python meshnet_worker.py
  python meshnet_worker.py --name "workstation-ana" --threads 8
  python meshnet_worker.py --blender "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe"
  python meshnet_worker.py --priority low --output D:\\renders
        """
    )
    p.add_argument("--name",     default="",    help="Apelido deste worker (padrão: hostname)")
    p.add_argument("--blender",  default="",    help="Caminho do executável do Blender")
    p.add_argument("--threads",  default=0,     type=int, help="Threads de render (0=auto)")
    p.add_argument("--priority", default="low", choices=["low","normal"], help="Prioridade do processo")
    p.add_argument("--output",   default="./meshnet_renders", help="Pasta de saída dos frames")
    return p.parse_args()

async def main():
    banner()
    args   = parse_args()
    worker = MeshNetWorker(args)

    # Graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            pass  # Windows não suporta add_signal_handler

    try:
        await worker.run()
    except KeyboardInterrupt:
        worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
