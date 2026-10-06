# GJ AI Tutor — starter pilot

A Streamlit app powered by OpenAI, with Maths, Physics, Chemistry, Accounting, Finance, ACCA qualification papers and a dedicated ACCA DipIFR study option; GCSE/A Level/university/professional levels; hints, step-by-step teaching, interactive quizzes and answer review. Lesson transcripts can be downloaded. Changing lesson settings clears the current conversation.

## ACCA DipIFR

Select `Diploma in IFRS (ACCA DipIFR)` in Subject. Its five study areas use a concise topic map checked against ACCA's December 2026–June 2027 syllabus and study guide, linked inside the app. The outline guides the prompt; it does not load the complete syllabus, IFRS standards or official marking schemes. Practice questions and feedback are AI-generated, independent study support and not ACCA-approved.

Select `ACCA qualification papers` for BT, MA, FA, LW, PM, TX, FR, AA, FM, SBL, SBR, AFM, APM, ATX or AAA. These 15 offered paper options include all four strategic options; candidates normally choose two. Provide the exam sitting and relevant regional variant. Official resource links are included, but this release does not certify full syllabus coverage or automatically read the linked documents. Ethics/experience requirements and the future qualification redesign are not courses in this release.

## Answer review

Choose `Review my answer`. Paste the question and relevant marking guidance, then submit your answer in chat. The reference is sent to OpenAI and used as study data, not instructions. Numerical feedback must be supported by the supplied rubric and is labelled indicative. Without a marking scheme, the tutor gives qualitative feedback. Do not paste personal or confidential information. Official past papers and schemes are linked rather than republished in the public repository.

## First step: GitHub

1. Sign up or sign in at https://github.com.
2. Create a repository named `ai-tutor`.
3. Upload `tutor_app.py`, `requirements.txt`, this README and `.streamlit/config.toml`, preserving the `.streamlit` folder. Add `.gitignore` too if using Git.
4. Commit the files. No genuine secrets are included in this starter package.

## OpenAI account

Create an account at https://platform.openai.com, configure billing and a low provider-side spending limit, then create an API key. Keep the key private. An OpenAI chat subscription does not supply API credits. API costs depend on tokens, model and conversation length.

## Streamlit deployment

Sign in at https://share.streamlit.io using GitHub. Create an app from `ai-tutor`, branch `main`, entrypoint `tutor_app.py`. In Advanced settings → Secrets, enter the following with your own values:

```toml
OPENAI_API_KEY = "REPLACE_WITH_YOUR_PRIVATE_KEY"
APP_PASSWORD = "REPLACE_WITH_A_LONG_RANDOM_PILOT_PASSWORD"
OPENAI_MODEL = "gpt-5.4-mini"
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

The starter has a shared pilot password, 3,000-character questions, a 1,800-token output cap (including reasoning), limited conversation context, a five-second request interval and 30 API attempts per browser session. Browser sessions and app restarts can reset these counters: they are not a global spending cap. Keep provider-side spending limits enabled; do not treat this version as an unrestricted public service.

Messages stay in Streamlit session memory and are sent to OpenAI for responses. There is no persistent student account, database, image upload, document retrieval or verified exam-board curriculum yet. Session transcripts disappear when the session ends; learners can download them. The model's knowledge may be outdated, especially for financial standards. Add approved learning materials before presenting this as a finance exam-preparation product.

Planned next steps: real student authentication and durable quotas, photo questions, curated notes retrieval with citations, then progress tracking.

Official references: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management and https://developers.openai.com/api/docs/models/gpt-5.4-mini.
