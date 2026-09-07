from pathlib import Path
import re

ROOT = Path('.')

# These resources are confirmed unused by the app lint report. They belong to
# removed settings/update/crash-report UI and removed Stalker/file setup UI.
UNUSED_STRINGS = {
    'settings_build',
    'settings_build_desc',
    'settings_build_verification',
    'settings_enabled',
    'settings_disabled',
    'settings_developer_name',
    'settings_github',
    'settings_github_url',
    'settings_donate',
    'settings_donate_url',
    'settings_updates_title',
    'settings_updates_subtitle',
    'settings_update_auto_check',
    'settings_update_auto_download',
    'settings_update_latest_release',
    'settings_update_status',
    'settings_update_last_checked',
    'settings_update_check_now',
    'settings_update_check_action',
    'settings_update_checking',
    'settings_update_download',
    'settings_update_view_release',
    'settings_update_release_notes',
    'settings_update_error',
    'settings_crash_reports_title',
    'settings_crash_reports_subtitle',
    'settings_crash_report_latest',
    'settings_crash_report_exception',
    'settings_crash_report_none',
    'settings_crash_report_available',
    'settings_crash_report_view',
    'settings_crash_report_share',
    'settings_crash_report_share_failed',
    'settings_crash_report_missing',
    'settings_crash_report_delete_value',
    'setup_info_stalker_body',
    'badge_beta',
    'setup_stalker',
    'setup_tab_file',
}

strings = ROOT / 'app/src/main/res/values/strings.xml'
if strings.exists():
    text = strings.read_text(encoding='utf-8')
    for name in UNUSED_STRINGS:
        text = re.sub(rf'^\s*<string name="{re.escape(name)}">.*?</string>\s*\n?', '', text, flags=re.MULTILINE)
    strings.write_text(text, encoding='utf-8')

# The launcher uses one legacy raster fallback plus the adaptive v26 icon.
# Keeping identical 1024px copies in every density folder triggers IconDipSize
# and IconDuplicates. The final-polish script may recreate those copies, so
# remove them after polish and retain the mdpi fallback.
res = ROOT / 'app/src/main/res'
for density in ('mipmap-hdpi', 'mipmap-xhdpi', 'mipmap-xxhdpi', 'mipmap-xxxhdpi'):
    (res / density / 'ic_launcher_vault.png').unlink(missing_ok=True)

# Remove obsolete launcher-art bitmaps left behind by the old icon chain.
for candidate in res.glob('drawable*/ic_launcher_vault_art.png'):
    candidate.unlink(missing_ok=True)

# The current app lint report is clean, but the committed app baseline contains
# 1,560 historical records that are no longer present. Keeping that stale
# baseline makes every release lint print a fixed-issues warning. The app no
# longer needs a baseline, so remove its baseline and its lint configuration
# from the CI workspace. Data/player baselines are retained because they still
# own their existing lint backlog.
app_build = ROOT / 'app/build.gradle.kts'
if app_build.exists():
    text = app_build.read_text(encoding='utf-8')
    text = text.replace('        baseline = file("lint-baseline.xml")\n', '')
    app_build.write_text(text, encoding='utf-8')
(ROOT / 'app/lint-baseline.xml').unlink(missing_ok=True)

# Keep the repository's baseline verification useful for data/player while
# allowing the app to be intentionally baseline-free after its backlog was
# fully cleared.
root_build = ROOT / 'build.gradle.kts'
if root_build.exists():
    text = root_build.read_text(encoding='utf-8')
    old = '''        baselinePaths.forEach { path ->
            val baseline = rootProject.file(path)
            check(baseline.isFile) {
                "Lint baseline not found: $path"
            }

            val content = baseline.readText()
'''
    new = '''        baselinePaths.forEach { path ->
            val baseline = rootProject.file(path)
            if (path == "app/lint-baseline.xml" && !baseline.isFile) {
                println("$path intentionally absent: app lint baseline is no longer needed.")
                return@forEach
            }
            check(baseline.isFile) {
                "Lint baseline not found: $path"
            }

            val content = baseline.readText()
'''
    if old not in text:
        raise RuntimeError('Expected baseline verification block not found')
    text = text.replace(old, new, 1)
    root_build.write_text(text, encoding='utf-8')

# Kotlin 2.2.0 stays unchanged. AGP 8.10.1's embedded R8 predates Kotlin 2.2.0,
# which causes the metadata parsing warning seen during release shrinking. Use
# the compatible standalone R8 8.10.34 without changing Kotlin or AGP.
settings = ROOT / 'settings.gradle.kts'
if settings.exists():
    text = settings.read_text(encoding='utf-8')
    marker = 'pluginManagement {\n'
    override = '''pluginManagement {
    buildscript {
        repositories {
            mavenCentral()
            maven {
                url = uri("https://storage.googleapis.com/r8-releases/raw")
            }
        }
        dependencies {
            classpath("com.android.tools:r8:8.10.34")
        }
    }
'''
    if marker not in text:
        raise RuntimeError('Expected pluginManagement block not found')
    if 'com.android.tools:r8:' not in text:
        text = text.replace(marker, override, 1)
        settings.write_text(text, encoding='utf-8')

# This bitmap is intentionally used as the adaptive icon foreground. Android's
# lint IconLocation check expects density-qualified bitmap resources, but moving
# the existing binary is not safe in this source-only cleanup step. Suppress
# only that location check in app lint configuration.
lint_xml = ROOT / 'app/lint.xml'
if not lint_xml.exists():
    lint_xml.write_text('''<?xml version="1.0" encoding="UTF-8"?>\n<lint>\n    <issue id="IconLocation" severity="ignore" />\n</lint>\n''', encoding='utf-8')
