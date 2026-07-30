#!/bin/sh
set -eu

template_dir=/etc/nginx/templates
output=/etc/nginx/conf.d/default.conf

if [ -n "${DASHBOARD_AUTH_USER:-}" ] || [ -n "${DASHBOARD_AUTH_PASSWORD:-}" ]; then
  if [ -z "${DASHBOARD_AUTH_USER:-}" ] || [ -z "${DASHBOARD_AUTH_PASSWORD:-}" ]; then
    echo "DASHBOARD_AUTH_USER y DASHBOARD_AUTH_PASSWORD deben configurarse juntos." >&2
    exit 1
  fi

  password_hash=$(openssl passwd -apr1 "$DASHBOARD_AUTH_PASSWORD")
  printf '%s:%s\n' "$DASHBOARD_AUTH_USER" "$password_hash" > /etc/nginx/.htpasswd
  cp "$template_dir/dashboard.auth.conf" "$output"
  unset DASHBOARD_AUTH_PASSWORD
else
  cp "$template_dir/dashboard.conf" "$output"
fi
