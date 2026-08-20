# Get an installable APK

I can't compile inside my sandbox (no Android SDK, and Google's Maven is network-blocked
there), so the APK is built by a machine that has the toolchain. Two ways — the first
needs nothing installed on your computer.

## Option A — GitHub Actions (no local setup, ~4 min) ✅ recommended

You get a real, installable **debug APK** as a downloadable file.

1. Create a new GitHub repo and push this project (the whole `stock-intelligence-ai`
   folder). The workflow lives at `android/.github/workflows/android.yml`.
   - If you put the repo root at `stock-intelligence-ai/`, keep the `android/` folder
     as-is — the workflow's `working-directory` is `android`.
2. GitHub → **Actions** tab → the **Android build** workflow runs automatically on push
   (or click **Run workflow**).
3. When it finishes (green check), open the run → **Artifacts** → download
   **`app-debug-apk`**. Inside is `app-debug.apk`.
4. Copy it to your Android phone, enable **Install unknown apps** for your file manager,
   and tap to install.

That APK is signed with Android's standard debug key — installable on any device, not
Play-Store-publishable. For a Play release, do Option C.

## Option B — Android Studio (local, if you have it)

1. Open the `android/` folder in Android Studio; let Gradle sync.
2. `Build → Build Bundle(s) / APK(s) → Build APK(s)`.
3. Studio shows a "locate" link → that's your `app-debug.apk`.

Or from a terminal in `android/`: `./gradlew assembleDebug`
→ `app/build/outputs/apk/debug/app-debug.apk`.

## Option C — Signed release APK / AAB (for the Play Store)

1. Create a keystore once:
   ```
   keytool -genkey -v -keystore release.jks -keyalg RSA -keysize 2048 \
     -validity 10000 -alias sia
   ```
2. **Local build:** create `android/keystore.properties` (gitignored):
   ```
   storeFile=/absolute/path/release.jks
   storePassword=...
   keyAlias=sia
   keyPassword=...
   ```
   then `./gradlew bundleRelease` → `app/build/outputs/bundle/release/app-release.aab`.
3. **CI build:** in the GitHub repo → Settings → Secrets → Actions, add:
   `KEYSTORE_BASE64` (`base64 -w0 release.jks`), `SIGNING_STORE_PASSWORD`,
   `SIGNING_KEY_ALIAS`, `SIGNING_KEY_PASSWORD`. The workflow then also produces a signed
   APK + AAB under the **`app-release`** artifact.

## Make the app show real data

The APK talks to the backend at `BASE_URL` (default `http://10.0.2.2:8000` = emulator's
host alias). For a physical phone, set `BASE_URL` in `android/app/build.gradle.kts` to your
backend's reachable address (LAN IP during dev, or a deployed HTTPS URL) and rebuild.
Until then the app still runs — it just needs the backend reachable to populate.
