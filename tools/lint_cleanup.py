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

# This bitmap is intentionally used as the adaptive icon foreground. Android's
# lint IconLocation check expects density-qualified bitmap resources, but moving
# the existing binary is not safe in this source-only cleanup step. Suppress
# only that location check in app lint configuration.
lint_xml = ROOT / 'app/lint.xml'
if not lint_xml.exists():
    lint_xml.write_text('''<?xml version="1.0" encoding="UTF-8"?>\n<lint>\n    <issue id="IconLocation" severity="ignore" />\n</lint>\n''', encoding='utf-8')
