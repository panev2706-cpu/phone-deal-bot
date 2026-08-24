# Bulgarian Phone Deal Bot

This free Python bot checks public listings on **OLX.bg** and **Bazar.bg**, remembers what it has already seen, and sends a Telegram alert when a newly found phone is at or below your price limit. It runs in GitHub Actions, so your iPhone and computer can be turned off.

The first run is deliberately quiet: it records the listings that already exist without alerting you. Later runs alert only for new matching listings.

## Before you start

- Keep the GitHub repository **public**. Standard GitHub-hosted runners are free and unlimited for public repositories. A private repository has a limited monthly allowance and therefore is not a reliable €0 choice for a job that runs every five minutes. See [GitHub's runner documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job) and [Actions billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
- GitHub Secrets stay hidden, but `config.json` and `seen_listings.json` are public in a public repository. They must never contain your Telegram token, chat ID, phone number, address, or other private information.
- Five minutes is GitHub's shortest schedule. Runs are **approximately** every five minutes, not guaranteed to start at the exact minute; GitHub can delay or occasionally drop scheduled work during heavy load. See [GitHub's schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
- OLX access is best-effort. OLX can return HTTP 403, show a challenge, or change its pages. This project does not bypass access controls. OLX's published terms restrict unauthorized automated access and scraping, so review the [OLX terms](https://www.olxgroup.com/terms-of-use-2/) and use the adapter only where you are permitted to do so. Bazar can also change its page without warning.
- The code, Python libraries, Telegram Bot API, and standard public-repository GitHub Actions runner cost €0. No paid API, server, database, proxy, or AI service is used.

## Set up everything from an iPhone

Safari works for the GitHub steps. If GitHub hides a menu, tap Safari's **aA** button and choose **Request Desktop Website**.

### 1. Create your Telegram bot

1. Open Telegram and search for the verified **@BotFather** account.
2. Send `/newbot`.
3. Enter any display name, for example `My Phone Deal Bot`.
4. Enter a unique username ending in `bot`, for example `my_sofia_phone_deals_bot`.
5. BotFather replies with an HTTP API token.

### 2. Save the Telegram bot token

The token looks similar to `123456789:AAExampleLettersAndNumbers`. Temporarily copy it somewhere private. Do **not** paste it into a project file, screenshot it, or send it to another person. You will put it directly into a GitHub Secret in step 5.

If a token is ever exposed, send `/revoke` to BotFather, select the bot, and replace the GitHub Secret with the new token.

### 3. Get your Telegram chat ID

1. Open the bot you just made, tap **Start**, and send it a message such as `hello`.
2. In Safari, open the following address after replacing `<TOKEN>` with the token from BotFather:

   ```text
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

3. Find a section resembling this in the result:

   ```json
   "chat": {"id": 123456789, "first_name": "Your name", "type": "private"}
   ```

4. Copy only the number after `"id":`. Include a leading minus sign if it has one. That number is your `TELEGRAM_CHAT_ID`.
5. Close the page and clear it from Safari history because its address contains the token.

If the response contains `"result":[]`, return to Telegram, send the bot another message, wait a few seconds, and reload. For a group, add the bot, send a message that mentions it, and use the negative ID from that group's `chat` object. Telegram documents this official method as [`getUpdates`](https://core.telegram.org/bots/api#getupdates).

### 4. Create the public GitHub repository and upload the project

1. Sign in at [github.com](https://github.com/) in Safari.
2. Tap **+**, then **New repository**.
3. Name it, for example, `phone-deal-bot`.
4. Select **Public**, then tap **Create repository**.
5. Upload every file from this project and keep the same names and folders. Files such as `.github/workflows/monitor.yml` must not be flattened or renamed.
6. Commit the upload to the default branch (`main`).

On iPhone, GitHub's upload picker may not upload a whole folder. Upload the root files with **Add file → Upload files**. For a nested file, use **Add file → Create new file**, type its full path (for example `scrapers/olx.py`), paste that file's contents, and commit it. Repeat until the repository matches the structure below:

```text
phone-deal-bot/
├── .github/
│   └── workflows/
│       └── monitor.yml
├── bot/
│   ├── __init__.py
│   └── telegram.py
├── scrapers/
│   ├── __init__.py
│   ├── base.py
│   ├── bazar.py
│   └── olx.py
├── tests/
│   ├── fixtures/
│   │   ├── bazar_search.html
│   │   └── olx_search.html
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_main.py
│   ├── test_prices_filters.py
│   ├── test_scrapers.py
│   ├── test_state.py
│   └── test_telegram.py
├── utils/
│   ├── __init__.py
│   ├── config.py
│   ├── filters.py
│   ├── prices.py
│   └── state.py
├── config.json
├── main.py
├── README.md
├── requirements.txt
└── seen_listings.json
```

Do not upload a ZIP file as the project: GitHub Actions cannot run the files while they are still inside the ZIP.

### 5. Add the two GitHub Secrets

In your repository:

1. Tap **Settings**.
2. Open **Secrets and variables → Actions**.
3. Tap **New repository secret**.
4. Name it exactly `TELEGRAM_BOT_TOKEN` and paste the BotFather token as its value.
5. Add a second repository secret named exactly `TELEGRAM_CHAT_ID` and paste the numeric chat ID as its value.

Secret names are case-sensitive. Do not add quotes or spaces around either value.

### 6. Enable GitHub Actions and state saving

1. Open **Settings → Actions → General**.
2. Under **Actions permissions**, allow GitHub actions to run. The workflow uses only `actions/checkout` and `actions/setup-python` plus commands from this repository.
3. Under **Workflow permissions**, choose **Read and write permissions**, then tap **Save**. This allows the workflow to commit only its updated `seen_listings.json` state.
4. Open the repository's **Actions** tab. If GitHub shows **I understand my workflows, go ahead and enable them**, tap it.

The workflow itself also requests only `contents: write`; it does not request access to issues, pull requests, packages, or deployments.

### 7. Choose phones and maximum prices

Open `config.json`, tap the pencil icon, and edit only the values under `searches`. Each entry needs:

- `name`: the friendly phone name shown in Telegram.
- `keywords`: one or more alternative search phrases.
- `max_price_eur`: your maximum price in euros, without the `€` symbol.

Example:

```json
{
  "searches": [
    {
      "name": "iPhone 14 Pro Max",
      "keywords": ["iphone 14 pro max"],
      "max_price_eur": 500
    },
    {
      "name": "iPhone 15 Pro",
      "keywords": ["iphone 15 pro"],
      "max_price_eur": 550
    },
    {
      "name": "Samsung Galaxy S24 Ultra",
      "keywords": ["samsung galaxy s24 ultra", "s24 ultra"],
      "max_price_eur": 600
    }
  ]
}
```

Keep the other settings already present in `config.json`. Add or remove whole search objects as needed, keep commas between objects, and do not add a comma after the last object. The maximum is always configured in EUR; listings written in BGN are converted with exactly `1 EUR = 1.95583 BGN`.

Edit `exclude_keywords` in the same file to reject accessories, broken phones, replicas, locked devices, or any other unwanted words. Matching is case-insensitive. A listing that matches any exclusion is not sent.

Deal labels use the configured percentage below your maximum:

- 🟢 **MATCH**: less than 10% below the limit.
- 🔥 **GOOD DEAL**: at least 10% but less than 20% below the limit.
- 🚨 **GREAT DEAL**: at least 20% below the limit.

The exact percentages can be changed with `good_deal_percent` and `great_deal_percent` in `config.json`.

After editing searches and any exclusions, tap **Commit changes** and commit to `main`. A newly added search (or a materially changed keyword set) gets its own quiet first-run baseline, so advertisements that already existed for that search are not sent as new deals.

### 8. Run the setup test

1. Open **Actions**.
2. Select **Phone deal monitor**.
3. Tap **Run workflow**.
4. Turn on **Send a Telegram setup-test message before monitoring**.
5. Tap the green **Run workflow** button.

Refresh after a few seconds and open the newest run. Every step should become green, and Telegram should receive a setup-test message. The same run records current marketplace listings as its baseline; it intentionally does not send deal alerts for those old listings.

If the run is red, tap it, open the failed step, and use the troubleshooting section below. GitHub hides secret values in logs.

### 9. Confirm automatic monitoring

Return to **Actions → Phone deal monitor** later. Scheduled runs should appear about every five minutes with `schedule` as their trigger. New qualifying listings will now create Telegram alerts; the same marketplace listing ID will not alert twice.

The bot commits changes to `seen_listings.json`, including a periodic heartbeat, so seeing commits made by `github-actions[bot]` is normal. Never manually clear that file unless you intentionally want to create a fresh baseline.

## What an alert contains

An alert includes the configured phone name, marketplace title, original price, converted EUR price, marketplace, location when available, maximum price, amount saved, and a tappable direct link. When the marketplace supplies an image, the bot tries to send it as a photo. If Telegram cannot download the image, the bot automatically sends the same alert as text instead.

Listings with no usable numeric price, listings above your limit, and listings containing an excluded word are skipped. Encountered listings are still remembered so changing a limit later does not turn an old advertisement into a “new” one.

## Optional dry run on a computer

A dry run reads and parses listings but does not send Telegram messages or change `seen_listings.json`:

```bash
python -m pip install -r requirements.txt
python main.py --dry-run --config config.json --state seen_listings.json
```

Run the automated tests with:

```bash
python -m unittest discover -s tests -v
```

## Troubleshooting

### No Telegram setup message

- Confirm that you tapped **Start** in the private chat with your bot.
- Confirm both GitHub Secret names are exact and their values have no quotes or spaces.
- A `401 Unauthorized` error means the bot token is wrong or was revoked.
- A `400 Bad Request: chat not found` error usually means the chat ID is wrong or the bot has never been started in that chat.
- For a group, confirm the bot is still a member and use that group's negative chat ID.

### `getUpdates` is empty

Send the bot a brand-new message and reload the URL. If you previously configured a webhook for this bot, `getUpdates` cannot work until that webhook is removed; using a fresh BotFather bot is usually simplest for a beginner.

### The state-save step says permission denied

Open **Settings → Actions → General → Workflow permissions**, select **Read and write permissions**, and save. If the repository belongs to an organization, an organization policy can override this setting; use a personal public repository instead.

### There is no Run workflow button

Make sure `.github/workflows/monitor.yml` exists on the default branch, then reload the Actions page. GitHub only shows the button for a workflow on the default branch.

### Runs stopped appearing

- Check that the workflow is enabled under **Actions → Phone deal monitor → ⋯ → Enable workflow**.
- Scheduled workflows run only from the default branch.
- GitHub automatically disables scheduled workflows in a public repository after 60 days with no repository activity. The bot writes a monthly state heartbeat to avoid inactivity where possible, but check the Actions tab occasionally. GitHub explains how to [re-enable a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows).
- GitHub can delay or drop an individual scheduled run during very high load. The next run normally catches the listing.

### OLX fails but Bazar works

An OLX HTTP 403 or challenge is an access restriction, not a bad Telegram setup. The bot will report repeated marketplace failures and continue checking other enabled marketplaces. It deliberately does not solve CAPTCHAs, imitate a browser, use proxies, or bypass OLX controls. You can remove `"olx"` from `enabled_marketplaces` in `config.json` while leaving Bazar enabled.

### No deal alerts after the first run

That is expected until a **new** listing appears. The first run only creates a baseline. Also check that the new listing is at or below `max_price_eur` and does not contain an `exclude_keywords` value.

### A marketplace changed its page

The run log will show which scraper could not parse results. The bot keeps the last state and will not invent listings. Page-layout changes require updating that marketplace's separate file under `scrapers/`; the other marketplace continues independently.

## Privacy and delivery notes

- Telegram Bot API calls are sent directly to Telegram. Marketplace pages are fetched directly from GitHub's runner.
- Only the two encrypted GitHub Secrets contain Telegram credentials. State commits contain listing data, not credentials.
- Failed Telegram deliveries are kept for retry on a later run. A rare crash after Telegram accepts a message but before GitHub commits the new state can still cause one duplicate message; no free stateless scheduled system can guarantee a perfect exactly-once transaction across both services.
- Use this project gently for personal monitoring and comply with each marketplace's current rules. Do not increase the schedule or add aggressive parallel requests.

## License and responsibility

This project is provided for personal, educational use without a guarantee that a marketplace will remain accessible or keep the same HTML. You are responsible for complying with marketplace terms and local law.
