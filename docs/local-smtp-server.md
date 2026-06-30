# Local SMTP Server on the Raspberry Pi

This project can use a local SMTP server on the Pi. The recommended production shape is:

```text
Backend container
  -> host.docker.internal:25
  -> Postfix on Raspberry Pi
  -> external authenticated SMTP relay
  -> recipient inbox
```

Do not rely on direct delivery from a home Raspberry Pi unless you control a domain, DNS, reverse DNS/PTR, SPF, DKIM, DMARC, and a clean static IP. Most consumer networks have poor outbound mail deliverability and many providers block or heavily filter home-IP mail.

## Option A: Test-only inbox with Mailpit

Use this when you want to test email without sending anything to the Internet.

Start the optional Mailpit service:

```bash
docker compose --profile mailtest up -d mailpit
```

Then set `.env` for the backend container:

```env
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=test@local.test
SMTP_FROM_NAME=Denny
SMTP_USE_TLS=false
SMTP_USE_SSL=false
```

Restart backend:

```bash
docker compose up --build -d backend
```

Open the Mailpit inbox:

```text
http://TAILSCALE_IP:8025
```

## Option B: Real delivery through local Postfix relay

Use this when you want the Pi to accept local SMTP from the app and then forward mail through a real SMTP provider.

Run this from the repo on the Pi:

```bash
SMTP_RELAY_HOST=smtp.example.com \
SMTP_RELAY_PORT=587 \
SMTP_RELAY_USERNAME=you@example.com \
SMTP_RELAY_PASSWORD='provider-password-or-app-password' \
SMTP_FROM_DOMAIN=example.com \
bash scripts/postfix-local-relay.sh
```

Then set `.env` for the backend:

```env
SMTP_HOST=host.docker.internal
SMTP_PORT=25
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=you@example.com
SMTP_FROM_NAME=Denny
SMTP_USE_TLS=false
SMTP_USE_SSL=false
SMTP_REPLY_TO=
ALLOW_AUTO_SEND_EMAILS=false
```

Restart the app:

```bash
docker compose up --build -d
```

## Test from the Pi host

```bash
echo 'hello from postfix' | mail -s 'Pi Postfix test' your@email.com
```

Check logs:

```bash
sudo journalctl -u postfix -n 100 --no-pager
sudo tail -n 100 /var/log/mail.log 2>/dev/null || true
mailq
```

Flush queued mail after fixing config:

```bash
sudo postqueue -f
```

## Test from the backend container

```bash
docker compose exec backend python - <<'PY'
from app.services.outreach_mailer import SMTPMailer

SMTPMailer().send(
    "your@email.com",
    "Backend SMTP test",
    "This was sent by the backend through the Pi local relay."
)
print("sent")
PY
```

## Gmail SMTP example

For Gmail SMTP, use an app password if your account supports it:

```bash
SMTP_RELAY_HOST=smtp.gmail.com \
SMTP_RELAY_PORT=587 \
SMTP_RELAY_USERNAME=yourgmail@gmail.com \
SMTP_RELAY_PASSWORD='your-16-character-app-password' \
SMTP_FROM_DOMAIN=gmail.com \
bash scripts/postfix-local-relay.sh
```

Then set:

```env
SMTP_FROM_EMAIL=yourgmail@gmail.com
```

## Production recommendation

For outreach, a transactional/outbound provider is usually better than Gmail SMTP because it gives clearer logs, domain authentication, bounce handling, and reputation controls.

Before sending real outreach, configure:

- SPF
- DKIM
- DMARC
- A clear sender identity
- A visible unsubscribe instruction
- Low sending volume
- Manual review before send

Keep:

```env
ALLOW_AUTO_SEND_EMAILS=false
```

until the review and response-tracking workflow is complete.
