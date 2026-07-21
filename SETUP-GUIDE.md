# Setup Guide — Avalla Cloud Monitor

## What you need

1. A free GitHub account.
2. A Discord server and webhook.
3. The contents of this project uploaded to a **public** GitHub repository.

A public repository is recommended because GitHub Actions standard hosted runners are free for public repositories. The webhook remains private because it is added as a GitHub secret, not written into the repository.

---

## Part 1 — Create the Discord webhook

1. Open Discord.
2. Open the server where you want the alerts.
3. Click the server name, then **Server Settings**.
4. Open **Integrations**.
5. Open **Webhooks**.
6. Click **New Webhook**.
7. Name it `Avalla AC Monitor`.
8. Select the alert channel.
9. Click **Copy Webhook URL**.

Do not paste the webhook into any project file.

---

## Part 2 — Create the GitHub repository

1. Sign in to GitHub.
2. Click the `+` button in the top-right.
3. Select **New repository**.
4. Repository name:

   `avalla-ac-monitor`

5. Select **Public**.
6. Do not add a README, `.gitignore`, or licence because this download already contains the files.
7. Click **Create repository**.

---

## Part 3 — Upload the project

The easiest beginner method is GitHub's website.

1. Open your new repository.
2. Click **uploading an existing file**.
3. Unzip the downloaded project on your Mac.
4. Open the unzipped `avalla-cloud-monitor` folder.
5. Drag these items into GitHub's upload area:

   - `.github`
   - `monitor.py`
   - `config.json`
   - `state.json`
   - `README.md`
   - `SETUP-GUIDE.md`

### Important: hidden `.github` folder on macOS

macOS hides folders beginning with a dot.

Inside the unzipped project folder, press:

`Command + Shift + .`

This reveals `.github`.

6. Enter a commit message such as `Add Avalla monitor`.
7. Click **Commit changes**.

---

## Part 4 — Add your private Discord webhook

1. In the GitHub repository, click **Settings**.
2. In the left menu, open **Secrets and variables**.
3. Click **Actions**.
4. Click **New repository secret**.
5. Name:

   `DISCORD_WEBHOOK_URL`

6. Paste the Discord webhook URL into **Secret**.
7. Click **Add secret**.

The name must be exactly `DISCORD_WEBHOOK_URL`.

---

## Part 5 — Enable and test it

1. Open the repository's **Actions** tab.
2. Select **Avalla AC Monitor**.
3. If GitHub displays an enable button, enable workflows.
4. Click **Run workflow**.
5. Tick **Send a Discord test notification instead of checking Avalla**.
6. Click the green **Run workflow** button.

After the run starts, refresh the page. A successful run displays a green tick, and Discord should receive:

`Test successful — your cloud Avalla monitor can send Discord alerts.`

---

## Part 6 — Run the first real check

1. Click **Run workflow** again.
2. Leave the test box unticked.
3. Click **Run workflow**.

The first real run creates a baseline. It does not alert for products that were already present.

Afterwards, the scheduled workflow checks automatically every five minutes.

---

## How it remembers stock

`state.json` stores the last known product status.

The workflow commits this file only when it changes, so it does not create a commit every five minutes. A commit is generally created only when:

- the initial baseline is saved;
- a product is added or removed;
- availability or displayed price changes.

---

## Viewing checks

1. Open the **Actions** tab.
2. Select a workflow run.
3. Open the `monitor` job.
4. Expand **Check Avalla and notify Discord**.

A normal result looks like:

`Check complete: 1 genuine AC listing(s), 0 in stock, 0 alert(s).`

---

## Changing the frequency

Open:

`.github/workflows/monitor.yml`

The current line is:

`- cron: "*/5 * * * *"`

This means every five minutes.

Examples:

- Every 10 minutes: `*/10 * * * *`
- Every 15 minutes: `*/15 * * * *`
- Every hour: `0 * * * *`

GitHub scheduled runs can occasionally start later than the exact cron time, particularly during busy periods.

---

## Security

- Never put the Discord webhook directly into `monitor.py`, `config.json`, or the workflow file.
- Keep it only in the GitHub secret named `DISCORD_WEBHOOK_URL`.
- If the webhook is exposed, delete it in Discord and create a new one.

---

## Stopping the monitor

Open:

`Actions` → `Avalla AC Monitor` → menu button → `Disable workflow`

You can re-enable it later.
