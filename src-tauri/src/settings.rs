use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::Manager;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct AppSettings {
    pub start_minimized: bool,
    pub launch_at_startup: bool,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            start_minimized: false,
            launch_at_startup: false,
        }
    }
}

pub fn settings_path(app: &tauri::AppHandle) -> PathBuf {
    app.path()
        .app_config_dir()
        .unwrap_or_else(|_| std::env::temp_dir().join("jarvis"))
        .join("settings.json")
}

pub fn load(app: &tauri::AppHandle) -> AppSettings {
    let path = settings_path(app);
    match fs::read_to_string(&path) {
        Ok(raw) => serde_json::from_str(&raw).unwrap_or_default(),
        Err(_) => AppSettings::default(),
    }
}

pub fn save(app: &tauri::AppHandle, settings: &AppSettings) {
    let path = settings_path(app);
    if let Some(dir) = path.parent() {
        let _ = fs::create_dir_all(dir);
    }
    if let Ok(raw) = serde_json::to_string_pretty(settings) {
        let _ = fs::write(path, raw);
    }
}
