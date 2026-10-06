# GJ AI Tutor — starter pilot

A Streamlit app powered by Claude, with Maths, Physics, Chemistry, Accounting and Finance; GCSE/A Level/university/professional levels; hints, step-by-step teaching and interactive quizzes. Lesson transcripts can be downloaded. Changing lesson settings clears the current conversation.

## First step: GitHub

1. Sign up or sign in at https://github.com.
2. Create a repository named `ai-tutor`.
3. Upload `tutor_app.py`, `requirements.txt`, this README and `.streamlit/config.toml`, preserving the `.streamlit` folder. Add `.gitignore` too if using Git.
4. Commit the files. No genuine secrets are included in this starter package.

## Claude account

Create an account at https://console.anthropic.com, configure billing and a low provider-side spending limit, then create an API key. Keep the key private. A Claude chat subscription does not supply API credits. API costs depend on tokens, model and conversation length.

## Streamlit deployment

Sign in at https://share.streamlit.io using GitHub. Create an app from `ai-tutor`, branch `main`, entrypoint `tutor_app.py`. In Advanced settings → Secrets, enter the following with your own values:

```toml
ANTHROPIC_API_KEY = "REPLACE_WITH_YOUR_PRIVATE_KEY"
APP_PASSWORD = "REPLACE_WITH_A_LONG_RANDOM_PILOT_PASSWORD"
ANTHROPIC_MODEL = "claude-haiku-4-5"
```

Deploy, open the generated URL, enter your pilot password and test a lesson. Never commit these actual values to GitHub or paste the key into a chat. The app will show a setup message until both required secrets are configured.

## Run locally (optional)

Use Python 3.11 or newer. Install with `python -m pip install -r requirements.txt`. Create `.streamlit/secrets.toml` using the same settings above, then run `python -m streamlit run tutor_app.py`.

## Pilot checks

- Test all three teaching modes; a quiz should ask one question and wait.
- Change subject or level and verify that the old lesson clears.
- Download a transcript.
- Check missing-key and invalid-key messages without exposing credentials.
- Check maths answers against a textbook before student use.

## Limits and next upgrades

The starter has a shared pilot password, 3,000-character questions, a 1,000-token response cap, limited conversation context, a five-second request interval and 30 API attempts per browser session. Browser sessions and app restarts can reset these counters: they are not a global spending cap. Keep provider-side spending limits enabled; do not treat this version as an unrestricted public service.

Messages stay in Streamlit session memory and are sent to Anthropic for responses. There is no persistent student account, database, image upload, document retrieval or verified exam-board curriculum yet. Session transcripts disappear when the session ends; learners can download them. The model's knowledge may be outdated, especially for financial standards. Add approved learning materials before presenting this as a finance exam-preparation product.

Planned next steps: real student authentication and durable quotas, photo questions, curated notes retrieval with citations, then progress tracking.

Official references: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management and https://platform.claude.com/docs/en/models/overview.
