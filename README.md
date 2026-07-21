# Avalla Cloud Air-Conditioner Monitor

This project checks Avalla's refurbished air-conditioner collection every five minutes using GitHub Actions.

It sends a Discord alert when:

- a genuine refurbished air conditioner is newly listed **and available**;
- an existing refurbished air conditioner changes from sold out to **in stock**.

It ignores obvious accessories including window kits, hoses, filters and replacement parts.

## Cost

To keep frequent five-minute checks free, create this as a **public GitHub repository** and use the standard GitHub-hosted runner.

Your Discord webhook is not stored in the code. It is held in a GitHub repository secret.

## Files

- `monitor.py` — monitor logic.
- `config.json` — Avalla URL and product filters.
- `state.json` — remembers the previous product status.
- `.github/workflows/monitor.yml` — cloud schedule.
- `SETUP-GUIDE.md` — beginner-friendly installation instructions.

No proxies and no external Python packages are required.
