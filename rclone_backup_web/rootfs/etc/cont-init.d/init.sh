#!/usr/bin/with-contenv bashio
set -eu

# Login is handled by Home Assistant ingress, not by a second UI password.
mkdir -p /root/.config/rclone /var/run/s6/container_environment /run/nginx
if [[ ! -e /config ]]; then
    ln -s /homeassistant /config
fi

config_path="$(bashio::config 'config_path')"
if [[ -z "$config_path" || "$config_path" == "null" ]]; then
    config_path=/homeassistant/rclone.conf
fi
if bashio::config.has_value 'rclone_config'; then
    config_path=/root/.config/rclone/rclone.conf
    umask 077
    bashio::config 'rclone_config' > "$config_path"
else
    mkdir -p "$(dirname "$config_path")"
    if [[ ! -f "$config_path" ]]; then
        (umask 077; touch "$config_path")
    fi
fi
printf '%s' "$config_path" > /var/run/s6/container_environment/RCLONE_CONFIG
bashio::log.info "Installed version: $(cat /usr/share/rclone-backup-web/rclone-version)"
bashio::log.info "Rclone configuration: $config_path"
