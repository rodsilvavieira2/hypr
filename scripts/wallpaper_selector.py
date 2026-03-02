#!/usr/bin/env python3

import os
import subprocess

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GdkPixbuf, Gio, Gtk

# Configuration
WALLPAPER_DIR = "/home/rodrigo/Documents/Wallpapers"
SET_WALLPAPER_SCRIPT = os.path.expanduser("~/.config/hypr/scripts/wall")
AUTOSTART_CONFIG = os.path.expanduser("~/.config/hypr/autostart")

# Catppuccin Mocha Palette
COLORS = {
    "base": "#1e1e2e",
    "mantle": "#181825",
    "crust": "#11111b",
    "text": "#cdd6f4",
    "subtext0": "#a6adc8",
    "subtext1": "#bac2de",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay0": "#6c7086",
    "overlay1": "#7f8497",
    "overlay2": "#9399b2",
    "blue": "#89b4fa",
    "lavender": "#b4befe",
    "sapphire": "#74c7ec",
    "sky": "#89dceb",
    "teal": "#94e2d5",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "peach": "#fab387",
    "maroon": "#eba0ac",
    "red": "#f38ba8",
    "mauve": "#cba6f7",
    "pink": "#f5c2e7",
    "flamingo": "#f2cdcd",
    "rosewater": "#f5e0dc",
}

CSS = f"""
window {{
    background-color: {COLORS["base"]};
    color: {COLORS["text"]};
}}

listview {{
    background-color: {COLORS["mantle"]};
}}

row {{
    padding: 10px;
    border-bottom: 1px solid {COLORS["surface0"]};
}}

row:selected {{
    background-color: {COLORS["surface0"]};
    color: {COLORS["lavender"]};
}}

label {{
    color: {COLORS["text"]};
}}

button {{
    background-color: {COLORS["surface0"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface1"]};
    border-radius: 8px;
    padding: 8px 16px;
    margin: 5px;
}}

button:hover {{
    background-color: {COLORS["surface1"]};
    border-color: {COLORS["overlay0"]};
}}

button:active {{
    background-color: {COLORS["surface2"]};
}}

button:disabled {{
    background-color: {COLORS["crust"]};
    color: {COLORS["overlay0"]};
}}

scrollbar slider {{
    background-color: {COLORS["surface1"]};
    min-height: 20px;
    min-width: 20px;
    border-radius: 10px;
}}
"""


class WallpaperSelector(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Wallpaper Selector")
        self.set_default_size(900, 600)

        # Apply CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Main Layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        self.set_child(main_box)

        # Left Pane: List of Wallpapers
        left_frame = Gtk.Frame()
        main_box.append(left_frame)

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_frame.set_child(left_box)

        # Header
        list_header = Gtk.Label(label="Available Wallpapers")
        list_header.set_xalign(0)
        list_header.set_margin_start(10)
        list_header.set_margin_end(10)
        list_header.set_margin_top(10)
        list_header.set_margin_bottom(10)
        left_box.append(list_header)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_width(250)
        scrolled_window.set_vexpand(True)
        left_box.append(scrolled_window)

        # GtkListView setup
        self.wallpaper_files = self.get_wallpapers()
        # Create a model from the list of strings
        self.string_list = Gtk.StringList.new(self.wallpaper_files)

        self.selection_model = Gtk.SingleSelection(model=self.string_list)
        self.selection_model.connect("selection-changed", self.on_selection_changed)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.setup_list_item)
        factory.connect("bind", self.bind_list_item)

        self.list_view = Gtk.ListView(model=self.selection_model, factory=factory)
        scrolled_window.set_child(self.list_view)

        # Right Pane: Preview and Action
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_hexpand(True)
        main_box.append(right_box)

        # Preview Area
        preview_frame = Gtk.Frame()
        preview_frame.set_vexpand(True)
        right_box.append(preview_frame)

        self.preview_image = Gtk.Image()
        self.preview_image.set_pixel_size(500)  # approximate max size
        preview_frame.set_child(self.preview_image)

        # Controls Area
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls_box.set_halign(Gtk.Align.END)
        right_box.append(controls_box)

        self.lbl_selected = Gtk.Label(label="No wallpaper selected")
        self.lbl_selected.set_halign(Gtk.Align.START)
        right_box.prepend(self.lbl_selected)

        self.apply_button = Gtk.Button(label="Apply Wallpaper")
        self.apply_button.connect("clicked", self.on_apply_clicked)
        self.apply_button.set_sensitive(False)
        controls_box.append(self.apply_button)

        quit_button = Gtk.Button(label="Quit")
        quit_button.connect("clicked", self.on_quit_clicked)
        controls_box.append(quit_button)

        self.selected_wallpaper = None

        # Initial check
        if not self.wallpaper_files:
            if not os.path.exists(WALLPAPER_DIR):
                self.lbl_selected.set_label(f"Error: {WALLPAPER_DIR} not found")
            else:
                self.lbl_selected.set_label("No images found in directory")

    def get_wallpapers(self):
        if not os.path.exists(WALLPAPER_DIR):
            return []
        try:
            return sorted(
                [
                    f
                    for f in os.listdir(WALLPAPER_DIR)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))
                ]
            )
        except Exception as e:
            print(f"Error reading directory: {e}")
            return []

    def setup_list_item(self, factory, list_item):
        label = Gtk.Label()
        label.set_xalign(0)
        list_item.set_child(label)

    def bind_list_item(self, factory, list_item):
        label = list_item.get_child()
        item = list_item.get_item()
        label.set_label(item.get_string())

    def on_selection_changed(self, selection_model, position, n_items):
        selected_item = selection_model.get_selected_item()
        if selected_item:
            filename = selected_item.get_string()
            self.selected_wallpaper = os.path.join(WALLPAPER_DIR, filename)
            self.lbl_selected.set_label(f"Selected: {filename}")
            self.update_preview()
            self.apply_button.set_sensitive(True)
        else:
            self.selected_wallpaper = None
            self.apply_button.set_sensitive(False)

    def update_preview(self):
        if self.selected_wallpaper:
            try:
                # Load image at a reasonable size for preview
                texture = Gdk.Texture.new_from_filename(self.selected_wallpaper)
                self.preview_image.set_from_paintable(texture)

            except Exception as e:
                print(f"Error loading preview: {e}")
                self.preview_image.set_from_icon_name("image-missing")

    def on_apply_clicked(self, widget):
        if self.selected_wallpaper:
            print(f"Setting wallpaper: {self.selected_wallpaper}")
            # 1. Apply immediately
            try:
                subprocess.Popen([SET_WALLPAPER_SCRIPT, self.selected_wallpaper])
            except Exception as e:
                print(f"Failed to run wallpaper script: {e}")

            # 2. Persist to autostart
            self.persist_wallpaper(self.selected_wallpaper)

    def persist_wallpaper(self, wallpaper_path):
        if not os.path.exists(AUTOSTART_CONFIG):
            print(f"Autostart file not found at {AUTOSTART_CONFIG}")
            return

        try:
            with open(AUTOSTART_CONFIG, "r") as f:
                lines = f.readlines()

            new_lines = []
            updated = False

            # Search for the line calling the wall script and replace it
            for line in lines:
                if "scripts/wall" in line and not line.strip().startswith("#"):
                    new_line = f"$scripts/wall {wallpaper_path} &\n"
                    new_lines.append(new_line)
                    updated = True
                else:
                    new_lines.append(line)

            if updated:
                with open(AUTOSTART_CONFIG, "w") as f:
                    f.writelines(new_lines)
                print(f"Updated autostart config with {wallpaper_path}")
            else:
                print("Could not find wallpaper line in autostart to update")

        except Exception as e:
            print(f"Failed to update autostart: {e}")

    def on_quit_clicked(self, widget):
        self.close()


class WallpaperApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.rodrigo.WallpaperSelector")

    def do_activate(self):
        win = WallpaperSelector(self)
        win.present()


if __name__ == "__main__":
    app = WallpaperApp()
    app.run(None)
