pub mod backend;
pub mod settings;
pub mod tray;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(backend::BackendProcess::default())
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            let _ = tray::show_window(app);
        }))
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec!["--start-minimized"]),
        ))
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            let handle = app.handle();
            let cfg = settings::load(handle);

            if cfg.launch_at_startup {
                use tauri_plugin_autostart::ManagerExt;
                if !handle.autolaunch().is_enabled().unwrap_or(false) {
                    let _ = handle.autolaunch().enable();
                }
            }

            if let Err(e) = tray::create_tray(handle, cfg.clone()) {
                eprintln!("[jarvis] tray error: {e}");
            }

            let spawn = handle.clone();
            tauri::async_runtime::spawn(async move {
                backend::ensure_backend(spawn).await;
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // If this is the main window, hide instead of quitting (tray app).
                if window.label() == "main" {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
