# RHPY — HR Vacation Request CLI

Modern API on legacy RHPI tool that manage vacations and leaves

A command-line tool for managing vacation requests in an enterprise context. Employees can submit requests, check their balance, and view team availability. Managers can validate pending requests.

---

## Setup

Before using any command, store your credentials once:

```bash
rhpy login <username> <password>
```

Credentials are saved locally in `config.json` and reused for all subsequent commands.

> ⚠️ `config.json` stores credentials in plain text. Keep this file secure and add it to your `.gitignore`.

---

## Commands

### `login`

Save your credentials locally.

```bash
rhpy login <username> <password>
```

---

### `add`

Submit a new time-off request.

```bash
rhpy add <type> <start> <end>
```

| Argument | Description |
|---|---|
| `type` | Type of absence (see table below) |
| `start` | Start date in `dd/mm/yy` format |
| `end` | End date in `dd/mm/yy` format |

**Absence types:**

| Code | Label | Description |
|---|---|---|
| `cp` | Congés payés | Paid vacation |
| `jr` | Jour de repos | Rest day |
| `ho` | Télétravail | Home office / remote work |

**Example:**

```bash
rhpy add cp 01/08/25 15/08/25
# Submits a paid vacation request from August 1st to August 15th, 2025
```

---

### `balance`

Display your current leave balance.

```bash
rhpy balance
```

---

### `status`

Show the current and upcoming availability of your team — who is on leave or working remotely in the near future.

```bash
rhpy status
```

---

### `validate`

> 👔 Manager only

Review and validate pending time-off requests from your team.

```bash
rhpy validate
```

---

### `tt`

Submit your recurring télétravail (home office) schedule in one step.

```bash
rhpy tt
```

---

## Date Format

All dates must be provided in `dd/mm/yy` format.

| Input | Meaning |
|---|---|
| `13/10/25` | October 13th, 2025 |
| `01/01/26` | January 1st, 2026 |



## Not supported
* multiple contract. It only takes the first one

# Mac Installation

1. Download Chrome
2. Download Chromedriver, with same version number as Chrome
https://chromedriver.chromium.org/downloads
3. Move the driver to the /usr/local/bin folder



# Docker
## Build
```
docker build -t pdechastellier/rhpy:0.9 .
```
## Run and attach
```
docker run --rm -ti pdechastellier/rhpy:0.9 /bin/bash
```

Vulnerability scan - snyk
docker scan
