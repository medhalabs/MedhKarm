# Notifications (standup and weekly report by email and WhatsApp)

**Status:** Built (Phase 3): per-founder settings, email (Resend or SMTP) and WhatsApp (Meta Cloud API), daily standup and Monday report; not yet sent for real (needs the provider keys)  
**Code:** `backend/app/features/notifications/` · jobs `backend/app/workers/handlers/standup.py` · `backend/app/features/standups/weekly.py` · `frontend/src/features/notifications/` · page `/admin/settings` · migration `0011_notification_settings`  
**Last updated:** 2026-10-05

## What it is

Every morning, each founder gets **their own standup**: what was done, what's planned, what's blocked and what needs them. Every Monday they also get a **weekly report**: runs started, released and stopped, what's waiting, and tokens used.
- **Email** gets the full text.
- **WhatsApp** gets one line with a link to the inbox.
- **Each founder chooses** the address, the number, the hour, and whether to get each update.
- **Nothing is sent until they save an address** (opt-in).

## Priya, the voice of the updates

Priya, the office manager, is the face of these messages. The standup starts "Good morning, it's Priya. Here is your standup." and ends with her name; the WhatsApp line starts "Priya:". She also sends **nudges** when something has waited for you for a day (see [inbox.md](inbox.md)); each founder can switch nudges off with **Let Priya remind me when something waits a day**.

## How it works

1. **Settings** (`/admin/settings` → `PUT /settings/notifications`):
   - email, and a WhatsApp number in E.164 form (`+919876543210`; spaces and brackets are removed)
   - the standup hour (0–23, in `STANDUP_TIMEZONE`, default Asia/Kolkata)
   - daily on/off and weekly on/off
2. **Scheduling** (the worker's tick, `standup_schedule`):
   - It queues `standup.send` for every company whose standup is on, that has an address, and whose hour has passed today.
   - On Mondays it also queues `report.weekly`.
   - Unique keys (`standup.send:<company>:<day>`, `report.weekly:<company>:<day>`) mean once a day or week, however many workers run.
3. **The standup job** builds the standup over the 24 hours up to the company's hour, **from its own runs only**. It sends:
   - email: subject "Standup 05 Oct: <headline>", the full text and an inbox link
   - WhatsApp: one line ("Standup Mon 05 Oct: … Needs you: … Done 2, planned 1, blocked 0. Open: <link>")

   It also writes the standup to the worker's log.
4. **The weekly job** (`standups/weekly.py`) covers the company's runs over the 7 days before the Monday: started, released, failed, not approved, cancelled, waiting for approval, and tokens.
5. **Sending** (`NotificationService.deliver`):
   - Each channel is tried separately, and one failing doesn't stop the other.
   - A channel whose keys aren't on the server reports "isn't set up on the server".
   - The job retries only when **every** channel failed (a provider outage).
6. **"Send me a test"** sends a short message on every channel set up, and shows what happened on each.

## Setting up the providers

**Email, with Resend (recommended):**
1. Sign up at resend.com and create an API key.
2. To send from your own address, add and verify your domain (medhkarm.in, once bought). Until then, Resend's `onboarding@resend.dev` sender only delivers to the email you signed up with.
3. In `backend/.env`: `RESEND_API_KEY=…`, `EMAIL_FROM=MedhKarm <updates@medhkarm.in>`.

**Email, with any SMTP server** (if there's no Resend key), e.g. Gmail with an app password: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER=…`, `SMTP_PASSWORD=…`, `EMAIL_FROM=…`.

**WhatsApp, with Meta's WhatsApp Cloud API:**
1. Go to developers.facebook.com → create an app of type **Business**, then add the **WhatsApp** product. Meta gives you a test number, or add your own business number.
2. In WhatsApp Manager, create a message template:
   - name `medhkarm_update`, category **Utility**, language **English**
   - body: `MedhKarm update: {{1}}`
   - wait for approval (usually minutes)
3. Create a permanent access token: a System User in Business Settings, with `whatsapp_business_messaging` permission.
4. In `backend/.env`: `WHATSAPP_TOKEN=…`, `WHATSAPP_PHONE_NUMBER_ID=…` (from the app's WhatsApp → API Setup page), and optionally `WHATSAPP_TEMPLATE`, `WHATSAPP_TEMPLATE_LANGUAGE`.
5. With Meta's test number, add your own phone as a test recipient first.

**Finally:** `APP_URL` (default `http://localhost:3000`) makes the inbox links in updates point to the right place.

## Code map

| File | Responsibility |
| --- | --- |
| `notifications/schemas.py` | `Channel`, `Update` (subject, text, short), `NotificationSettings` (checks email and E.164), `CompanySettings`, `Delivery` |
| `notifications/interfaces.py` | `Notifier`, `SettingsRepository` |
| `notifications/providers/resend_email.py` | `ResendEmail` |
| `notifications/providers/smtp_email.py` | `SmtpEmail` (STARTTLS) |
| `notifications/providers/meta_whatsapp.py` | `MetaWhatsApp` (template message), `template_text()` (Meta's variable rules) |
| `notifications/service.py` | `NotificationService`: get, save, deliver, send_test, due_standups, due_weekly |
| `notifications/dependencies.py` | `notifiers(settings)`: the providers whose keys are set |
| `notifications/router.py` | `/settings/notifications` |
| `standups/render.py` · `standups/weekly.py` | `to_short()`; `build_weekly`, `weekly_text`, `weekly_short` |
| `workers/handlers/standup.py` | `SendStandup`, `SendWeekly`, `standup_schedule` |
| `frontend/…/notifications/` | `SettingsPage`, `SettingsForm` (save, test), `parseSettings` |

## API

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/settings/notifications` | `{settings, available}`: `available` = channels with keys on the server | Bearer |
| PUT | `/settings/notifications` | Save `{email, whatsapp, standup_on, standup_hour, weekly_on}` | Bearer |
| POST | `/settings/notifications/test` | Send a test; `[{channel, to, ok, error}]` | Bearer |

## Data model

`notification_settings`: `company_id` (PK, FK companies), `email`, `whatsapp`, `standup_on`, `standup_hour`, `weekly_on`, `updated_at`.

## Events

None. Jobs: `standup.send` (now per company) and `report.weekly` (new).

## Dependencies

- **Config:** `RESEND_API_KEY`, `EMAIL_FROM`, `SMTP_*`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_TEMPLATE` (default `medhkarm_update`), `WHATSAPP_TEMPLATE_LANGUAGE` (default `en`), `APP_URL`, `STANDUP_TIMEZONE`, `STANDUP_SCHEDULE`
- **Uses:** `standups`, `runs` (the company's runs), `events` (tokens), `auth`

## Design decisions

- 2026-10-05 — **Both channels** (Pavan): email for the full standup, WhatsApp for a one-line nudge with a link. Meta's templates allow no line breaks in a variable.
- 2026-10-05 — **Resend, SMTP as the fallback:** one HTTPS call and a free tier; SMTP covers founders who'd rather use their own mailbox.
- 2026-10-05 — **Meta's Cloud API directly**, not a reseller (Twilio, Gupshup): no middleman fee, and the official route in India. Business-initiated messages need an approved template.
- 2026-10-05 — **Opt-in, per company:** nothing goes out until the founder saves an address, and each company gets only its own work.

## How to run and test

- `uv run pytest app/features/notifications tests/test_founder_updates.py`
- Live (with keys): `/admin/settings` → save → **Send me a test**.

## Known limitations and gotchas

- Not yet sent for real: no Resend key or WhatsApp app yet.
- One timezone for everyone (`STANDUP_TIMEZONE`); per-founder timezones come with founders outside India.
- Plain-text email (no HTML design yet). One email address and one WhatsApp number per company.
- WhatsApp replies from the founder aren't read yet (two-way chat would be the next step, through Meta's webhooks).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| "email isn't set up on the server" | No `RESEND_API_KEY` or `SMTP_HOST` | Add one to `backend/.env`, restart the API and worker |
| Resend 403 / "only send testing emails to your own address" | Unverified domain | Verify the domain, or send to the account's own address |
| WhatsApp 400 "template name does not exist" | Template not approved, or a different name or language | Check WhatsApp Manager; set `WHATSAPP_TEMPLATE` / `_LANGUAGE` |
| WhatsApp 131030 "recipient not in allowed list" | Meta's test number | Add the recipient as a test number in the app |
| No standup arrives | No address saved, the standup is off, the hour hasn't passed, or the worker isn't running | Check `/admin/settings`; start the worker |

## Changelog

| Date | Change |
| --- | --- |
| 2026-10-07 | Priya's nudges: a `nudge_on` setting (migration `0018`), `due_nudges`, and the `priya.nudge` job ([inbox.md](inbox.md)) |
| 2026-10-05 | Created: settings, Resend/SMTP email, Meta WhatsApp, per-company standup and weekly report, test send |
