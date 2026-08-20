# Push this project to your GitHub

The zip already contains a committed git repo (initial commit on `main`), so you only
need to point it at your remote and push. I can't push for you — that needs your GitHub
credentials, which stay with you.

## Steps

1. Create an empty repo on GitHub (no README/;.gitignore — this project already has them).
2. Unzip and push:

```bash
unzip stock-intelligence-ai.zip
cd stock-intelligence-ai

# use YOUR repo URL here (HTTPS or SSH)
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

If prompted for a password over HTTPS, use a **Personal Access Token** (GitHub no longer
accepts account passwords for git). SSH (`git@github.com:<you>/<repo>.git`) avoids the
prompt if you have a key set up.

## Then you get an APK automatically

Pushing to `main` triggers the included workflow (`android/.github/workflows/android.yml`).
GitHub → **Actions** → **Android build** → when green, open the run → **Artifacts** →
download **`app-debug-apk`**. That's your installable APK.

## Notes

- `.gitignore` already excludes secrets (`.env`, keystores, `keystore.properties`). Only
  `backend/.env.example` is committed — safe, it has no real values.
- Want the repo public vs private? Either works; the Actions build runs the same.
- If `git push` rejects because the remote isn't empty, run `git pull --rebase origin main`
  first, then push.
