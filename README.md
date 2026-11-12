# P2P Networks Customer Dashboard

A Django web portal that gives P2P Networks' customers one place to see the health of their network equipment, whichever vendor it comes from. Despite the repository name, this project is not peer-to-peer communication software: "P2P" is the company name (`p2pnetworks.net`).

The dashboard pulls inventory, status, location and usage data from three vendor clouds into its own database, then shows each customer only the devices that belong to them:

| Vendor | Source | What is collected |
|---|---|---|
| **Peplink** | InControl 2 API (OAuth client credentials) | Organizations, groups, devices, WAN/cellular/Starlink interface status, bandwidth usage, GPS location |
| **Cisco Meraki** | Meraki Dashboard API (`meraki` SDK) | Organizations, networks, devices, uplink status, network events |
| **Ubiquiti UniFi** | UniFi Controller API | Sites, devices, device status |

## Features

- **Multi-tenant customer view.** Staff link users to one or more customers, and customers to Peplink groups, Meraki networks and UniFi sites. A logged-in user can switch between the customers they belong to.
- **Overview dashboard** (`/`): the customer's routers plus WAN, LAN, wireless and threat summaries.
- **Device status history:** online, offline, alerting and dormant counts over time, charted by day or other intervals.
- **Router details** (`/dashboard/router-details/<vendor>/<serial>/`): interface status, raw device data, and bandwidth used.
- **Starlink monitoring:** per-interface throughput history, and data used against a monthly limit set per device in the admin.
- **Cellular and WAN history**, kept for trend charts.
- **GPS tracking:** location history and heading for mobile routers, drawn on a Leaflet map.
- **Admin back office** (`/admin/`, Semantic UI admin) for managing customers, organizations, devices, users and sync logs.
- **Data retention:** history older than `DATA_RETENTION_DAYS` (default 180) is pruned.

## How it works

```
Peplink InControl ─┐
Meraki Dashboard  ─┼─► dashboard/data_sync.py ─► PostgreSQL ─► Django views/templates ─► customer browser
UniFi Controller  ─┘   (run by management commands on cron)
```

Sync jobs write to the database and record each run in `DataSyncLog`. Pages read only from the database, so they stay fast and still load if a vendor API is down.

## Project layout

| Path | Purpose |
|---|---|
| `userdashboard/` | Django project: settings, root URLs, home dashboard view, customer switching |
| `dashboard/` | Core app: models, sync logic, device and chart views, admin, management commands |
| `dashboard/data_sync.py` | Sync functions for every vendor (organizations, groups/networks/sites, devices, statuses, GPS) |
| `dashboard/management/commands/` | `sync_all_devices`, `sync_device_statuses`, `delete_old_records` |
| `incontrol/client.py` | Peplink InControl 2 API client |
| `merakiapi/helper.py` | Meraki helper (network events per customer) |
| `unifi/`, `unifiapi/` | UniFi Controller / UISP API clients |
| `common/utils.py` | Shared helpers: status calculation, coordinate conversion, heading, logging |
| `templates/`, `static/` | UI theme (Bootstrap admin template), Leaflet maps, charts |
| `apps/`, `custom/`, `elements/`, `layouts/` | Demo pages from the UI theme; not part of the monitoring features |
| `conf/` | Deployment files: gunicorn config, systemd unit template, `local_settings.py` template |

## Requirements

- Python 3.11+
- PostgreSQL. The models use `ArrayField`, so SQLite will not work.
- API access to whichever vendors you use: a Peplink InControl client ID and secret, a Meraki API key, and a UniFi controller URL with a username and password.

## Setup

```bash
git clone https://github.com/synapsemo/Networkingproject-P2P-communication.git
cd Networkingproject-P2P-communication
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/python-pip.txt
cp conf/local_settings.py.tmpl conf/local_settings.py
```

`userdashboard/settings.py` runs `conf/local_settings.py` at the end, if the file exists. The file is git-ignored, so put your environment-specific settings and secrets there:

```python
DEBUG = False
SECRET_KEY = "..."
ALLOWED_HOSTS = ["dashboard.example.com"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "dashboard",
        "USER": "...",
        "PASSWORD": "...",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

PEPLINK_CLIENT_ID = "..."
PEPLINK_CLIENT_SECRET = "..."
MERAKI_API_KEY = "..."
UNIFI_ENDPOINT_URL = "https://unifi.example.com:8443"
UNIFI_USERNAME = "..."
UNIFI_PASSWORD = "..."
```

Then create the database tables and an admin user, and start the server:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Syncing data

Run these management commands on a schedule, for example with cron:

| Command | What it does | Suggested schedule |
|---|---|---|
| `python manage.py sync_all_devices` | Pulls organizations, groups/networks/sites and the device inventory from every vendor | Hourly or daily |
| `python manage.py sync_device_statuses` | Records the current status of each device, interface, Starlink link, cellular link and WAN | Every 5 minutes |
| `python manage.py delete_old_records` | Deletes history older than `DATA_RETENTION_DAYS` | Daily |

Example crontab:

```cron
*/5 * * * * cd /path/to/src && /path/to/env/bin/python manage.py sync_device_statuses
0 * * * *   cd /path/to/src && /path/to/env/bin/python manage.py sync_all_devices
0 3 * * *   cd /path/to/src && /path/to/env/bin/python manage.py delete_old_records
```

After the first sync, open `/admin/` to create customers, link them to their Peplink groups, Meraki networks and UniFi sites, and assign users to them.

## Deployment

Production runs under gunicorn behind a reverse proxy:

- `conf/gunicorn.conf.py` binds to `127.0.0.1:8000` and starts `2 × CPU` workers.
- `conf/dashboard.service.tmpl` is a systemd unit template. Copy it to `/etc/systemd/system/`, adjust the paths and user, then enable it.
- Run `python manage.py collectstatic` so that static files are written to `host_static_files/` for the web server.

## Tech stack

Django 5 · django-allauth · django-semantic-admin · PostgreSQL · pandas · Meraki SDK · requests · gunicorn · Bootstrap · Leaflet
