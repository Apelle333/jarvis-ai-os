use std::net::TcpStream;
use std::os::windows::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::Duration;

use tauri::Emitter;
use tauri::Manager;

use crate::settings;

const CREATE_NO_WINDOW: u32 = 0x0800_0000;
const HEALTH_URL: &str = "http://127.0.0.1:8000/health";
const BACKEND_TIMEOUT_SECS: u64 = 90;

/// Resolve the repository `backend/` directory by walking up from the exe dir.
fn resolve_backend_dir() -> Option<PathBuf> {
    if let Ok(dir) = std::env::var("JARVIS_BACKEND_DIR") {
        let p = PathBuf::from(dir);
        if p.join("main.py").exists() {
            return Some(p);
        }
    }

    let mut current = std::env::current_exe().ok()?;
    current.pop(); // exe
    for _ in 0..8 {
        let candidate = current.join("backend");
        if candidate.join("main.py").exists() {
            return Some(candidate);
        }
        if !current.pop() {
            break;
        }
    }
    None
}

fn find_python(backend_dir: &Path) -> Option<PathBuf> {
    let venv_pythonw = backend_dir.join("venv").join("Scripts").join("pythonw.exe");
    if venv_pythonw.exists() {
        return Some(venv_pythonw);
    }
    let venv_python = backend_dir.join("venv").join("Scripts").join("python.exe");
    if venv_python.exists() {
        return Some(venv_python);
    }
    // fall back to anything on PATH
    for name in ["pythonw.exe", "python.exe"] {
        if which(name).is_some() {
            return Some(PathBuf::from(name));
        }
    }
    None
}

fn which(name: &str) -> Option<PathBuf> {
    let path_var = std::env::var_os("PATH")?;
    for dir in std::env::split_paths(&path_var) {
        let candidate = dir.join(name);
        if candidate.exists() {
            return Some(candidate);
        }
    }
    None
}

fn backend_running() -> bool {
    TcpStream::connect_timeout(&"127.0.0.1:8000".parse().unwrap(), Duration::from_millis(600)).is_ok()
}

async fn health_ok() -> bool {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(2))
        .build();
    let Ok(client) = client else {
        return false;
    };
    match client.get(HEALTH_URL).send().await {
        Ok(resp) => {
            let ok = resp.status().is_success();
            ok && resp.text().await.map(|t| t.contains("healthy")).unwrap_or(false)
        }
        Err(_) => false,
    }
}

/// Spawn the FastAPI backend (hidden), redirecting output to a log file.
fn spawn_backend(app: &tauri::AppHandle) -> Option<Child> {
    let backend_dir = resolve_backend_dir()?;
    let python = find_python(&backend_dir)?;

    let log_dir = backend_dir.join("logs");
    let _ = std::fs::create_dir_all(&log_dir);
    let log_path = log_dir.join("tauri_backend.log");
    let log = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
        .ok();

    let stdout = if let Some(f) = &log {
        Stdio::from(f.try_clone().ok()?)
    } else {
        Stdio::null()
    };
    let stderr = if let Some(f) = &log {
        Stdio::from(f.try_clone().ok()?)
    } else {
        Stdio::null()
    };

    let mut cmd = Command::new(&python);
    cmd.current_dir(&backend_dir)
        .args(["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"])
        .stdout(stdout)
        .stderr(stderr)
        .stdin(Stdio::null())
        .creation_flags(CREATE_NO_WINDOW);

    // keep the app from outliving the window on quit
    let _ = app;
    let child = cmd.spawn().ok()?;
    eprintln!("[jarvis] backend spawned via {:?}", python);
    Some(child)
}

pub async fn ensure_backend(app: tauri::AppHandle) {
    // 1. Already running? Just wait for it to become healthy.
    let mut started = false;
    if backend_running() {
        eprintln!("[jarvis] backend already on :8000");
    } else {
        match spawn_backend(&app) {
            Some(_child) => started = true,
            None => {
                eprintln!("[jarvis] could not spawn backend - continuing in offline mode");
            }
        }
    }

    // 2. Wait for /health.
    let mut ok = false;
    for _ in 0..BACKEND_TIMEOUT_SECS {
        if health_ok().await {
            ok = true;
            break;
        }
        tokio::time::sleep(Duration::from_secs(1)).await;
    }

    let _ = started;

    // 3. Reveal the window (unless configured to start minimized).
    let cfg = settings::load(&app);
    if !cfg.start_minimized {
        if let Some(win) = app.get_webview_window("main") {
            let _ = win.show();
            let _ = win.set_focus();
        }
    }

    // 4. Notify the frontend + OS.
    if ok {
        eprintln!("[jarvis] JARVIS systems online");
        let _ = app.emit("backend-ready", ());
        let _ = notify(&app, "JARVIS systems online", "All systems are operational.");
    } else {
        eprintln!("[jarvis] backend did not become healthy in time");
        let _ = app.emit("backend-error", ());
        if let Some(win) = app.get_webview_window("main") {
            let _ = win.show();
            let _ = win.set_focus();
        }
        let _ = notify(&app, "JARVIS backend offline", "Could not reach the core. Check the backend.");
    }
}

fn notify(app: &tauri::AppHandle, title: &str, body: &str) {
    use tauri_plugin_notification::NotificationExt;
    let notification = app
        .notification()
        .builder()
        .title(title)
        .body(body)
        .icon("icons/icon.png");
    let _ = notification.show();
}
