#!/usr/bin/env bash
set -euo pipefail

# Configure Postfix on the Raspberry Pi as a local SMTP relay for the Docker app.
# Recommended usage:
#   SMTP_RELAY_HOST=smtp.example.com \
#   SMTP_RELAY_PORT=587 \
#   SMTP_RELAY_USERNAME=you@example.com \
#   SMTP_RELAY_PASSWORD='app-password-or-provider-password' \
#   SMTP_FROM_DOMAIN=example.com \
#   bash scripts/postfix-local-relay.sh
#
# The backend should use:
#   SMTP_HOST=host.docker.internal
#   SMTP_PORT=25
#   SMTP_USE_TLS=false
#   SMTP_USE_SSL=false
#   SMTP_USERNAME=
#   SMTP_PASSWORD=

if [[ -z "${SMTP_RELAY_HOST:-}" ]]; then
  echo "SMTP_RELAY_HOST is required. Use an external relay such as Gmail SMTP, SES, Postmark, Mailgun, Resend, or SendGrid." >&2
  exit 2
fi

SMTP_RELAY_PORT="${SMTP_RELAY_PORT:-587}"
SMTP_FROM_DOMAIN="${SMTP_FROM_DOMAIN:-localdomain}"
PI_HOSTNAME="${PI_HOSTNAME:-$(hostname -f 2>/dev/null || hostname)}"

if command -v docker >/dev/null 2>&1; then
  DOCKER_SUBNET="${DOCKER_SUBNET:-$(docker network ls --format '{{.Name}}' | grep '_default$' | head -n1 | xargs -r docker network inspect -f '{{(index .IPAM.Config 0).Subnet}}' 2>/dev/null || true)}"
fi
DOCKER_SUBNET="${DOCKER_SUBNET:-172.16.0.0/12}"

echo "Installing Postfix and mail tools..."
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postfix libsasl2-modules mailutils ca-certificates

echo "Configuring Postfix for local Docker relay..."
sudo postconf -e "myhostname = ${PI_HOSTNAME}"
sudo postconf -e "myorigin = ${SMTP_FROM_DOMAIN}"
sudo postconf -e "inet_interfaces = all"
sudo postconf -e "inet_protocols = ipv4"
sudo postconf -e "mynetworks = 127.0.0.0/8 ${DOCKER_SUBNET}"
sudo postconf -e "smtpd_recipient_restrictions = permit_mynetworks,reject_unauth_destination"
sudo postconf -e "relayhost = [${SMTP_RELAY_HOST}]:${SMTP_RELAY_PORT}"
sudo postconf -e "smtp_tls_security_level = encrypt"
sudo postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"

if [[ -n "${SMTP_RELAY_USERNAME:-}" && -n "${SMTP_RELAY_PASSWORD:-}" ]]; then
  echo "Writing relay credentials to /etc/postfix/sasl_passwd..."
  sudo bash -c "cat > /etc/postfix/sasl_passwd" <<EOF
[${SMTP_RELAY_HOST}]:${SMTP_RELAY_PORT} ${SMTP_RELAY_USERNAME}:${SMTP_RELAY_PASSWORD}
EOF
  sudo postmap /etc/postfix/sasl_passwd
  sudo chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db
  sudo postconf -e "smtp_sasl_auth_enable = yes"
  sudo postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
  sudo postconf -e "smtp_sasl_security_options = noanonymous"
else
  echo "No SMTP_RELAY_USERNAME/PASSWORD set; configuring unauthenticated upstream relay."
  sudo postconf -e "smtp_sasl_auth_enable = no"
fi

# Keep SMTP closed to the public Internet. Allow only local/Docker network access.
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow OpenSSH || true
  sudo ufw deny 25/tcp || true
  sudo ufw allow from "${DOCKER_SUBNET}" to any port 25 proto tcp || true
  sudo ufw --force enable || true
fi

sudo systemctl enable postfix
sudo systemctl restart postfix

postconf -n | sed -n '/^myhostname/p;/^myorigin/p;/^inet_interfaces/p;/^mynetworks/p;/^relayhost/p;/^smtp_sasl_auth_enable/p;/^smtp_tls_security_level/p'

echo ""
echo "Postfix local relay is configured. Set app .env to:"
echo "SMTP_HOST=host.docker.internal"
echo "SMTP_PORT=25"
echo "SMTP_USERNAME="
echo "SMTP_PASSWORD="
echo "SMTP_USE_TLS=false"
echo "SMTP_USE_SSL=false"
echo ""
echo "Send a test from the Pi host with:"
echo "echo 'hello from postfix' | mail -s 'Pi Postfix test' your@email.com"
