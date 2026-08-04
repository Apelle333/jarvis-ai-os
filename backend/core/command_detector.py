"""
JARVIS AI Operating System - Computer Control Intent Detector
Deterministic, bilingual (Italian/English) intent detection for computer
control commands. Turns natural language like "JARVIS apri Chrome" into a
structured :class:`ControlIntent` that the System Agent can execute safely.

This is a fast, rule-based layer that sits in front of the LLM: known
commands are executed deterministically, everything else falls through to
the normal planning / model routing flow.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# Risk levels (ascending). Confirmation is enforced at "high" and above
# when settings.enable_confirmation_prompts is true.
LOW = "low"
MEDIUM = "medium"
HIGH = "high"
CRITICAL = "critical"


@dataclass
class ControlIntent:
    """A structured, executable computer-control command."""
    action: str                       # machine action key (e.g. "open_app")
    category: str                     # applications | windows | input | files | system | confirmation
    target: str = ""                  # app name / window / filename / folder / key...
    params: Dict[str, Any] = field(default_factory=dict)
    risk: str = LOW
    requires_confirmation: bool = False
    description: str = ""
    confidence: float = 0.9


# ---------------------------------------------------------------------------
# App registry: display name (lowercase) -> launchable exe / URI
# ---------------------------------------------------------------------------
KNOWN_APPS = {
    # Browsers
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "cromos": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "mozilla firefox": "firefox.exe",
    "opera": "opera.exe",
    "browser": "chrome.exe",
    "navigatore": "chrome.exe",
    "navigatore web": "chrome.exe",
    # Communication
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "telegram": "Telegram.exe",
    "whatsapp": "WhatsApp.exe",
    "slack": "slack.exe",
    # Office
    "word": "winword.exe",
    "microsoft word": "winword.exe",
    "excel": "excel.exe",
    "microsoft excel": "excel.exe",
    "powerpoint": "powerpoint.exe",
    "microsoft powerpoint": "powerpoint.exe",
    "one note": "onenote.exe",
    "outlook": "outlook.exe",
    # Editors / dev
    "notepad": "notepad.exe",
    "blocco note": "notepad.exe",
    "notepad++": "notepad++.exe",
    "vscode": "Code.exe",
    "visual studio code": "Code.exe",
    "code": "Code.exe",
    "visual studio": "devenv.exe",
    "intellij": "idea64.exe",
    "pycharm": "pycharm64.exe",
    # Windows tools
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "esplora file": "explorer.exe",
    "gestione file": "explorer.exe",
    "risorse del computer": "explorer.exe",
    "calculator": "Calculator.exe",
    "calcolatrice": "Calculator.exe",
    "calcolatore": "Calculator.exe",
    "task manager": "Taskmgr.exe",
    "gestione attivita": "Taskmgr.exe",
    "gestione attività": "Taskmgr.exe",
    "taskmgr": "Taskmgr.exe",
    "cmd": "cmd.exe",
    "prompt dei comandi": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "WindowsTerminal.exe",
    "windows terminal": "WindowsTerminal.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "control panel": "control.exe",
    "pannello di controllo": "control.exe",
    "settings": "ms-settings:",
    "impostazioni": "ms-settings:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    # Games / media
    "steam": "steam.exe",
    "epic games": "EpicGamesLauncher.exe",
    "epic": "EpicGamesLauncher.exe",
    "obs": "obs64.exe",
    "obs studio": "obs64.exe",
    "photoshop": "Photoshop.exe",
    "adobe photoshop": "Photoshop.exe",
    "netflix": "chrome.exe --new-window https://www.netflix.com",
    "youtube": "chrome.exe --new-window https://www.youtube.com",
    "mappe": "chrome.exe --new-window https://maps.google.com",
    "maps": "chrome.exe --new-window https://maps.google.com",
    "posta": "chrome.exe --new-window https://mail.google.com",
    "gmail": "chrome.exe --new-window https://mail.google.com",
    "github": "chrome.exe --new-window https://github.com",
}

# Verb sets (bilingual) per intent family
_VERBS_OPEN = ["apri", "avvia", "lancia", "apre", "aprire", "aprimi", "apriamoci",
               "open", "launch", "start", "run", "get", "boot", "apriamo"]
_VERBS_CLOSE = ["chiudi", "chiude", "chiudere", "ferma", "termina", "uccidi", "esci da",
                "esci da", "close", "kill", "stop", "terminate", "quit", "exit"]
_VERBS_CREATE_FOLDER = ["crea una cartella", "crea cartella", "creami una cartella",
                        "crea la cartella", "nuova cartella", "fai una cartella",
                        "make a folder", "create a folder", "create folder",
                        "new folder", "make folder"]
_VERBS_CREATE_FILE = ["crea un file", "crea file", "creami un file", "make a file",
                      "create a file", "create file", "nuovo file"]
_VERBS_SEARCH = ["cerca", "trova", "cerco", "cercare", "search", "find", "look for"]
_VERBS_DELETE = ["elimina", "cancella", "rimuovi", "distruggi", "delete", "remove", "erase"]
_VERBS_ORGANIZE = ["organizza", "riordina", "ordina", "sistemas", "organize", "tidy", "sort"]
_VERBS_FOCUS = ["focus", "porta in primo piano", "metti in primo piano", "mettici il focus",
                "focusa", "concentra", "bring to front", "set focus"]
_VERBS_SWITCH = ["passa a", "cambia a", "switch to", "go to", "vai su", "vai a", "apri"]
_VERBS_MOVE_WINDOW = ["sposta la finestra", "sposta finestra", "sposta", "move window",
                      "move the window"]
_VERBS_RESIZE_WINDOW = ["ridimensiona", "ridimensiona la finestra", "resize", "ridimensionare"]
_VERBS_MAXIMIZE = ["massimizza", "ingrandisci", "maximize"]
_VERBS_MINIMIZE = ["minimizza", "riduci", "minimize"]
_VERBS_TYPE = ["digita", "scrivi", "scrivi del testo", "type", "type text", "type the text",
               "digita il testo"]
_VERBS_KEY = ["premi", "press", "premere"]
_VERBS_CLICK = ["clicca", "click", "clicka", "doppio clic", "double click", "doppio click",
                "right click", "tasto destro", "clic destro"]
_VERBS_CLIPBOARD = ["clipboard", "appunti", "negli appunti", "copy", "paste", "incolla",
                    "copia negli appunti", "copia", "read clipboard"]

_FILLERS = ["il", "lo", "la", "i", "gli", "le", "the", "a", "an", "per favore", "please",
            "puoi", "potresti", "can you", "could you", "voglio", "vorrei", "per piacere",
            "mi", "ti", "you", "i want to", "per cortesia", "fammi", "fai", "hey", "jarvis"]
_NAME_AFTER = ["chiamato", "chiamata", "di nome", "dal nome", "con nome", "called",
               "named", "con il nome"]
_LOC_AFTER = ["in", "nella", "nel", "nella cartella", "nel percorso", "sul desktop",
              "in the", "on the", "in", "sul desktop"]

_CONFIRM_WORDS = ["si", "sì", "certo", "confermo", "conferma", "procedi", "vai", "va bene",
                  "ok", "okay", "yes", "confirm", "proceed", "go ahead", "fai", "si fai"]
_DENY_WORDS = ["no", "non", "annulla", "cancel", "stop", "fermati", "lascia stare", "non farlo"]

_STATUS_IT = ["stato del pc", "stato del computer", "stato del sistema", "come sta il pc",
              "come va il pc", "come stanno", "status del pc", "stato pc", "come sta il computer"]
_STATUS_EN = ["pc status", "computer status", "system status", "system stats", "system health",
              "status of the pc", "status of the computer", "how is the pc", "how's the pc"]
_CPU_IT = ["uso della cpu", "uso cpu", "carico della cpu", "cpu"]
_RAM_IT = ["uso della ram", "uso ram", "memoria ram", "quantum di memoria", "ram"]
_DISK_IT = ["spazio sul disco", "spazio disco", "disco rigido", "storage", "spazio di memoria"]
_GPU_IT = ["gpu", "scheda grafica", "scheda video"]
_PROCS_IT = ["processi", "cosa sta girando", "cosa gira", "app che girano"]
_PROCS_EN = ["what's running", "running processes", "what is running", "running apps",
             "running applications", "which processes"]

_SCREENSHOT_IT = ["screenshot", "schermata", "cattura schermo", "foto dello schermo",
                  "print screen", "screen shot", "screenshot dello schermo"]
_SCREENSHOT_EN = ["take a screenshot", "screenshot", "capture the screen"]

_KNOWN_IT_APP_WORDS = [
    "chrome", "spotify", "discord", "telegram", "whatsapp", "edge", "firefox", "opera",
    "notepad", "word", "excel", "powerpoint", "vscode", "steam", "epic", "obs", "paint",
    "explorer", "calcolatrice", "blocco note", "calcolatore", "navigatore",
]

# Stop words never treated as an app/window target
_TARGET_STOP = set(["il", "lo", "la", "i", "gli", "le", "un", "una", "the", "a", "an", "mi",
                    "per", "di", "da", "che", "che", "e", "o", "ma", "del", "della", "dello",
                    "delle", "degli", "sul", "sulla", "su", "con", "in", "nel", "nella", "al",
                    "alla", "tuo", "tua", "mio", "mia", "pcf", "pc", "computer", "finestra",
                    "finestre", "app", "applicazione", "applicazioni", "programma", "programmi",
                    "cartella", "cartelle", "folder", "file", "documento", "documenti"])


def _clean(text: str) -> str:
    """Normalize punctuation/whitespace for matching."""
    text = re.sub(r"[?!.,;:]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _contains(text: str, phrases) -> bool:
    for p in phrases:
        if re.search(rf"\b{re.escape(p)}\b", text):
            return True
    return False


def _after(text: str, phrases) -> Optional[str]:
    """Return text after the earliest matching phrase, stripped of fillers."""
    best: Optional[str] = None
    for p in phrases:
        m = re.search(rf"\b{re.escape(p)}\b", text)
        if m:
            tail = text[m.end():]
            if best is None or len(tail) < len(best):
                best = tail
    if best is None:
        return None
    return _strip_fillers(best)


def _strip_fillers(text: str) -> str:
    for f in _FILLERS:
        # replace whole filler word, careful with 'il' matching inside words
        text = re.sub(rf"\b{re.escape(f)}\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for p in ["e poi", "subito", "adesso", "ora", "right now", "now"]:
        text = re.sub(rf"\b{re.escape(p)}\b", " ", text)
    return re.sub(r"\s+", " ", text).strip(" -")


def _extract_named(text: str, phrases) -> Optional[str]:
    """Extract the name following 'chiamato/chiamata/called...'."""
    m = re.search(r"\b(?:chiamat[ao]|di nome|dal nome|con il nome|named|called)\b\s+(.+?)$", text)
    if m:
        return _strip_fillers(m.group(1)).strip(" \"'")
    return None


def _pick_known_app(target: str) -> Optional[str]:
    if not target:
        return None
    # Try progressively: full phrase, then last word, then full lowercase
    for candidate in (target, target.rsplit(" ", 1)[-1]):
        candidate = candidate.strip()
        if candidate in KNOWN_APPS:
            return candidate
    return None


def _app_target(raw: str) -> str:
    """Normalize an extracted app target to a known-app key if possible."""
    t = _clean(raw)
    t = _strip_fillers(t).strip(" \"'")
    if not t:
        return ""
    known = _pick_known_app(t)
    if known:
        return known
    # Fall back to raw token (single word app names like 'chrome')
    for word in _KNOWN_IT_APP_WORDS:
        if word in t:
            return word
    return t


# ---------------------------------------------------------------------------
# Main detection entry point
# ---------------------------------------------------------------------------
def detect_computer_command(text: str, pending: Optional[Dict[str, Any]] = None) -> Optional[ControlIntent]:
    """
    Detect a computer-control intent in ``text``.

    Args:
        text: The raw user command.
        pending: A pending-action record (used to match confirmations).

    Returns:
        A :class:`ControlIntent` when a command is recognized, else ``None``.
    """
    original = text
    t = _clean(text)
    if not t:
        return None

    # 1) Confirmation of a pending action
    if pending:
        for w in _CONFIRM_WORDS:
            if t == w or t.startswith(w + " ") or (w in t and len(t) <= len(w) + 3):
                return ControlIntent(
                    action="confirm_pending",
                    category="confirmation",
                    target="",
                    params={"approved": True},
                    risk=LOW,
                    description="Confirm the pending action",
                )
        for w in _DENY_WORDS:
            if t == w or t.startswith(w + " "):
                return ControlIntent(
                    action="confirm_pending",
                    category="confirmation",
                    target="",
                    params={"approved": False},
                    risk=LOW,
                    description="Deny the pending action",
                )

    # 2) Screenshots
    if _contains(t, _SCREENSHOT_IT + _SCREENSHOT_EN):
        return ControlIntent(
            action="screenshot",
            category="system",
            target="",
            params={},
            risk=LOW,
            description="Capture a screenshot",
        )

    # 3) System status / diagnostics
    if any(p in t for p in _STATUS_IT + _STATUS_EN):
        return ControlIntent(
            action="system_status",
            category="system",
            target="",
            params={},
            risk=LOW,
            description="Show PC status",
        )
    if _contains(t, _GPU_IT):
        return ControlIntent(action="gpu_status", category="system", target="", params={},
                             risk=LOW, description="Show GPU status")
    if _contains(t, _CPU_IT) and _contains(t, ["uso", "carico", "usage", "load", "status", "stato", "percent"]):
        return ControlIntent(action="cpu_status", category="system", target="", params={},
                             risk=LOW, description="Show CPU usage")
    if _contains(t, _RAM_IT) and _contains(t, ["uso", "usage", "carico", "free", "libera", "status", "stato"]):
        return ControlIntent(action="ram_status", category="system", target="", params={},
                             risk=LOW, description="Show RAM status")
    if _contains(t, _DISK_IT) and _contains(t, ["spazio", "space", "libero", "free", "status", "stato", "quanto"]):
        return ControlIntent(action="disk_status", category="system", target="", params={},
                             risk=LOW, description="Show disk space")
    if _contains(t, _PROCS_IT + _PROCS_EN):
        return ControlIntent(action="list_processes", category="system", target="", params={},
                             risk=LOW, description="List running processes")

    # 4) Applications
    if _contains(t, ["quali app", "quali applicazioni", "quali programmi", "app aperte",
                     "programmi aperti", "applicazioni aperte", "running apps",
                     "running applications", "open apps", "open applications",
                     "quali applicazioni sono aperte", "programmi in esecuzione"]):
        return ControlIntent(action="list_apps", category="applications", target="", params={},
                             risk=LOW, description="List running applications")

    open_after = _after(t, _VERBS_OPEN)
    if open_after:
        target = _app_target(open_after)
        if target and target not in _TARGET_STOP:
            return ControlIntent(
                action="open_app",
                category="applications",
                target=target,
                params={"raw": _strip_fillers(open_after)},
                risk=MEDIUM,
                description=f"Open application '{target}'",
            )

    close_after = _after(t, _VERBS_CLOSE)
    if close_after:
        target = _app_target(close_after)
        if target and target not in _TARGET_STOP:
            return ControlIntent(
                action="close_app",
                category="applications",
                target=target,
                params={"raw": _strip_fillers(close_after)},
                risk=HIGH,
                requires_confirmation=True,
                description=f"Close application '{target}'",
            )

    # 5) Files
    named = _extract_named(t, _NAME_AFTER)
    if _contains(t, _VERBS_CREATE_FOLDER):
        name = named or "Nuova cartella"
        return ControlIntent(action="create_folder", category="files", target=name,
                             params={"raw": name}, risk=MEDIUM,
                             description=f"Create folder '{name}'")
    if _contains(t, _VERBS_CREATE_FILE):
        name = named or "new_file.txt"
        return ControlIntent(action="create_file", category="files", target=name,
                             params={"raw": name, "content": ""}, risk=MEDIUM,
                             description=f"Create file '{name}'")
    if _contains(t, _VERBS_SEARCH) and ("file" in t or "documento" in t or "documento" in t
                                        or named or any(p in t for p in ["chiamato", "called", "di nome"])):
        name = named or _after(t, _VERBS_SEARCH) or ""
        return ControlIntent(action="search_files", category="files",
                             target=name.strip().strip(" \"'"), params={"query": name},
                             risk=LOW, description=f"Search files '{name}'")
    if _contains(t, ["cosa c'è", "cosa ce", "mostra la cartella", "mostrami la cartella",
                     "list files", "elenca", "elenco file", "cosa c'è nella cartella",
                     "cosa ce nella cartella", "apri la cartella", "open folder", "open the folder",
                     "show folder", "che file ci sono"]):
        return ControlIntent(action="list_directory", category="files", target="", params={},
                             risk=LOW, description="List directory contents")
    if _contains(t, _VERBS_ORGANIZE):
        folder = "downloads" if "download" in t else ""
        return ControlIntent(action="organize_files", category="files", target=folder,
                             params={"directory": folder}, risk=HIGH, requires_confirmation=True,
                             description=f"Organize files{f' in {folder}' if folder else ''}")
    if _contains(t, _VERBS_DELETE) and ("file" in t or "cartella" in t or "folder" in t):
        name = named or _after(t, _VERBS_DELETE) or ""
        is_folder = "cartella" in t or "folder" in t
        return ControlIntent(action="delete_folder" if is_folder else "delete_file",
                             category="files", target=name.strip().strip(" \"'"),
                             params={"path": name}, risk=CRITICAL, requires_confirmation=True,
                             description=f"Delete {'folder' if is_folder else 'file'} '{name}'")

    # 6) Windows
    if _contains(t, ["quali finestre", "finestre aperte", "list windows", "what windows",
                     "quali programmi sono aperti", "windows open"]):
        return ControlIntent(action="list_windows", category="windows", target="", params={},
                             risk=LOW, description="List open windows")
    if _contains(t, _VERBS_MAXIMIZE):
        target = _app_target(_after(t, _VERBS_MAXIMIZE) or "")
        return ControlIntent(action="maximize_window", category="windows", target=target,
                             params={}, risk=MEDIUM, description=f"Maximize window '{target}'")
    if _contains(t, _VERBS_MINIMIZE):
        target = _app_target(_after(t, _VERBS_MINIMIZE) or "")
        return ControlIntent(action="minimize_window", category="windows", target=target,
                             params={}, risk=MEDIUM, description=f"Minimize window '{target}'")
    if _contains(t, _VERBS_MOVE_WINDOW):
        return ControlIntent(action="move_window", category="windows", target="", params={},
                             risk=MEDIUM, description="Move window")
    if _contains(t, _VERBS_RESIZE_WINDOW):
        return ControlIntent(action="resize_window", category="windows", target="", params={},
                             risk=MEDIUM, description="Resize window")
    if _contains(t, _VERBS_FOCUS):
        target = _app_target(_after(t, _VERBS_FOCUS) or "")
        return ControlIntent(action="focus_window", category="windows", target=target,
                             params={}, risk=MEDIUM, description=f"Focus window '{target}'")
    if _contains(t, _VERBS_SWITCH):
        target = _app_target(_after(t, _VERBS_SWITCH) or "")
        if target and target not in _TARGET_STOP:
            return ControlIntent(action="switch_app", category="windows", target=target,
                                 params={}, risk=MEDIUM,
                                 description=f"Switch to application '{target}'")

    # 7) Input
    if _contains(t, _VERBS_CLIPBOARD) and not ("file" in t or "cartella" in t):
        if _contains(t, ["leggi", "read", "show", "mostra", "cosa c'è negli appunti",
                         "cosa ce negli appunti"]):
            return ControlIntent(action="clipboard_read", category="input", target="", params={},
                                 risk=LOW, description="Read clipboard")
        return ControlIntent(action="clipboard_set", category="input", target="", params={},
                             risk=MEDIUM, description="Clipboard operation")
    if _contains(t, _VERBS_TYPE):
        return ControlIntent(action="keyboard_type", category="input", target="", params={},
                             risk=MEDIUM, description="Type text")
    if _contains(t, _VERBS_KEY):
        return ControlIntent(action="keyboard_press", category="input", target="", params={},
                             risk=MEDIUM, description="Press a key")
    if _contains(t, _VERBS_CLICK):
        return ControlIntent(action="mouse_click", category="input", target="", params={},
                             risk=MEDIUM, description="Mouse click")

    # 8) Diagnostics
    if _contains(t, ["diagnosi", "diagnostic", "test del sistema", "self test", "verifica del pc"]):
        return ControlIntent(action="diagnostics", category="system", target="", params={},
                             risk=LOW, description="Run basic diagnostics")

    return None
