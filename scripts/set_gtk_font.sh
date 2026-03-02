#!/usr/bin/env bash

# Check if arguments are provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"<Font Family> <Size>\""
    echo "Example: $0 \"Noto Sans 11\""
    echo "Current font: $(gsettings get org.gnome.desktop.interface font-name)"
    exit 1
fi

NEW_FONT="$1"

# Verify gsettings is installed
if ! command -v gsettings &> /dev/null; then
    echo "Error: 'gsettings' tool not found. Please install it."
    exit 1
fi

echo "Setting GTK system font to: '$NEW_FONT'"

# Set the interface font (Controls the text in menus, buttons, etc.)
gsettings set org.gnome.desktop.interface font-name "$NEW_FONT"

# Also update settings.ini for applications that don't use gsettings (or if not running a full DE)
update_gtk_config() {
    local config_file="$1"
    local config_dir=$(dirname "$config_file")

    if [ ! -d "$config_dir" ]; then
        mkdir -p "$config_dir"
    fi

    if [ ! -f "$config_file" ]; then
        echo "[Settings]" > "$config_file"
    fi

    if grep -q "^gtk-font-name" "$config_file"; then
        sed -i "s/^gtk-font-name=.*/gtk-font-name=$NEW_FONT/" "$config_file"
    else
        if ! grep -q "\[Settings\]" "$config_file"; then
            echo "[Settings]" >> "$config_file"
        fi
        echo "gtk-font-name=$NEW_FONT" >> "$config_file"
    fi
    echo "Updated $config_file"
}

update_gtk_config "$HOME/.config/gtk-3.0/settings.ini"
update_gtk_config "$HOME/.config/gtk-4.0/settings.ini"

echo "Done. Changes should apply immediately to running GTK applications."
