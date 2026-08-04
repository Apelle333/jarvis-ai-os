use tauri::menu::{CheckMenuItem, Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::Manager;
use tauri::{AppHandle, Emitter};

use crate::settings;

const MENU_ID_SHOW: &str = "show";
const MENU_ID_HIDE: &str = "hide";
const MENU_ID_START_MIN: &str = "start_min";
const MENU_ID_AUTOSTART: &str = "autostart";
const MENU_ID_QUIT: &str = "quit";

pub fn create_tray(app: &AppHandle, cfg: settings::AppSettings) -> tauri::Result<()> {
    let show = MenuItem::with_id(app, MENU_ID_SHOW, "Show JARVIS", true, None::<&str>)?;
    let hide = MenuItem::with_id(app, MENU_ID_HIDE, "Hide", true, None::<&str>)?;
    let sep = PredefinedMenuItem::separator(app)?;
    let start_min = CheckMenuItem::with_id(app, MENU_ID_START_MIN, "Start Minimized", true, cfg.start_minimized, None::<&str>)?;
    let autostart = CheckMenuItem::with_id(app, MENU_ID_AUTOSTART, "Launch at Startup", true, cfg.launch_at_startup, None::<&str>)?;
    let quit = MenuItem::with_id(app, MENU_ID_QUIT, "Quit JARVIS", true, None::<&str>)?;

    let menu = Menu::with_items(
        app,
        &[&show, &hide, &sep, &start_min, &autostart, &sep, &quit],
    )?;

    let icon = app
        .default_window_icon()
        .cloned()
        .ok_or_else(|| tauri::Error::AssetNotFound("icon".into()))?;

    TrayIconBuilder::with_id("jarvis-tray")
        .icon(icon)
        .menu(&menu)
        .tooltip("JARVIS")
        .show_menu_on_left_click(false)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            MENU_ID_SHOW => show_window(app),
            MENU_ID_HIDE => hide_window(app),
            MENU_ID_START_MIN => toggle_start_minimized(app),
            MENU_ID_AUTOSTART => toggle_autostart(app),
            MENU_ID_QUIT => {
                let _ = app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let tauri::tray::TrayIconEvent::Click {
                button: tauri::tray::MouseButton::Left,
                ..
            } = event
            {
                let app = tray.app_handle();
                show_window(app);
            }
        })
        .build(app)?;

    Ok(())
}

pub fn show_window(app: &AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        let _ = win.show();
        let _ = win.set_focus();
    }
}

pub fn hide_window(app: &AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        let _ = win.hide();
    }
}

fn toggle_start_minimized(app: &AppHandle) {
    let mut cfg = settings::load(app);
    cfg.start_minimized = !cfg.start_minimized;
    settings::save(app, &cfg);
    let _ = app.emit("settings-updated", &cfg);
}

fn toggle_autostart(app: &AppHandle) {
    use tauri_plugin_autostart::ManagerExt;
    let mut cfg = settings::load(app);
    let current = app.autolaunch().is_enabled().unwrap_or(false);
    if current {
        let _ = app.autolaunch().disable();
        cfg.launch_at_startup = false;
    } else {
        let _ = app.autolaunch().enable();
        cfg.launch_at_startup = true;
    }
    settings::save(app, &cfg);
    let _ = app.emit("settings-updated", &cfg);
}
