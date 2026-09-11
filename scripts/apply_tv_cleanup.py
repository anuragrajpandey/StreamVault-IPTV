from pathlib import Path
import re, shutil

ROOT = Path('.')
APP = ROOT / 'app/src/main/java/com/streamvault/app'

# Entirely TV-irrelevant feature packages/services.
for rel in [
    'cast', 'backup', 'ui/screens/downloads', 'service/DownloadForegroundService.kt',
    'player/PlayerCastCoordinator.kt', 'player/PlayerRecordingCoordinator.kt',
]:
    p = APP / rel
    if p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()

# Remove dedicated CastModule, which lives outside the cast package.
for rel in ['di/CastModule.kt']:
    p = APP / rel
    if p.exists():
        p.unlink()

# Remove imports belonging to removed features.
patterns = [
    r'^import com\.streamvault\.app\.cast\..*\n',
    r'^import com\.streamvault\.app\.backup\..*\n',
    r'^import com\.streamvault\.app\.service\.DownloadForegroundService\n',
    r'^import com\.streamvault\.domain\.model\.Download.*\n',
    r'^import com\.streamvault\.domain\.repository\.DownloadManager\n',
    r'^import com\.streamvault\.app\.ui\.screens\.player\.PlayerCastCoordinator\n',
    r'^import com\.streamvault\.app\.ui\.screens\.player\.PlayerRecordingCoordinator\n',
]

for p in ROOT.rglob('*.kt'):
    s = p.read_text()
    old = s
    for pat in patterns:
        s = re.sub(pat, '', s, flags=re.M)
    if s != old:
        p.write_text(s)

def remove_functions_containing_cast(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    function_re = re.compile(r'^\s*(?:(?:public|private|protected|internal|override|suspend|inline|tailrec|operator|infix)\s+)*fun\s+\w*Cast\w*\s*\(')
    function_re2 = re.compile(r'^\s*(?:(?:public|private|protected|internal|override|suspend|inline|tailrec|operator|infix)\s+)*fun\s+(?:cast\w*|\w*cast\w*)\s*\(', re.I)
    while i < len(lines):
        line = lines[i]
        if function_re.match(line) or function_re2.match(line):
            brace_count = line.count('{') - line.count('}')
            i += 1
            while i < len(lines) and brace_count <= 0 and '{' not in lines[i]:
                i += 1
            if i < len(lines):
                brace_count += lines[i].count('{') - lines[i].count('}')
                i += 1
            while i < len(lines) and brace_count > 0:
                brace_count += lines[i].count('{') - lines[i].count('}')
                i += 1
            continue
        out.append(line)
        i += 1
    return ''.join(out)

for p in ROOT.rglob('*.kt'):
    s = p.read_text()
    old = s
    s = remove_functions_containing_cast(s)
    s = re.sub(r'^\s*(?:private\s+|public\s+|internal\s+|protected\s+)?(?:val|var)\s+\w*(?:Cast|cast)\w*\s*[:=].*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*@Inject\s*\n\s*(?:lateinit\s+)?var\s+\w*cast\w*\s*:\s*[^\n]+\n', '', s, flags=re.I | re.M)
    s = re.sub(r'^.*\b(?:castEvents|isCasting|CastUiEvent|CastPlaybackReportMode|CastStartResult|CastMediaRequest|CastMediaRequestBuildResult)\b.*\n', '', s)
    s = re.sub(r'^.*\b(?:castManager|castPlaybackCoordinator|castMediaRequestFactory|castPlaybackReportMode)\b.*\n', '', s, flags=re.I)
    s = re.sub(r'^.*\b(?:openCastRouteChooser|castEpisode|castResumeEpisode|startCasting|isCast(?:ing)?|Cast[A-Za-z0-9_]*)\b.*\n', '', s)
    if s != old:
        p.write_text(s)

# Remove Downloads/backup navigation.
p = APP / 'navigation/AppNavigation.kt'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^import .*DownloadsScreen.*\n', '', s, flags=re.M)
    s = s.replace('    const val DOWNLOADS = "downloads"\n', '')
    s = s.replace('    const val SETTINGS_DESTINATION = "settings?backupUri={backupUri}"', '    const val SETTINGS_DESTINATION = "settings"')
    s = re.sub(r'fun settings\(backupUri: String\? = null\) = Routes\.SETTINGS_DESTINATION\.replace\("\{backupUri\}", Uri\.encode\(backupUri\)\)', 'fun settings() = Routes.SETTINGS_DESTINATION', s)
    s = s.replace('            AppLandingDestination.DOWNLOADS -> Routes.DOWNLOADS\n', '')
    s = s.replace('            AppTopLevelDestination.DOWNLOADS -> Routes.DOWNLOADS\n', '')
    p.write_text(s)

# Remove obsolete app-level services/manifest entries.
p = ROOT / 'app/src/main/AndroidManifest.xml'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^\s*android:supportsPictureInPicture="true"\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<activity[^>]*CastRouteChooserActivity[^>]*/>\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<service[^>]*DownloadForegroundService[^>]*/>\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<meta-data[^>]*CAST\.framework\.OPTIONS_PROVIDER_CLASS_NAME[^>]*/>\s*\n', '', s, flags=re.M)
    p.write_text(s)

# Remove Cast dependencies/references from Gradle.
for p in [ROOT / 'app/build.gradle.kts', ROOT / 'build.gradle.kts', ROOT / 'gradle/libs.versions.toml']:
    if not p.exists():
        continue
    s = p.read_text()
    s = re.sub(r'^.*com\.google\.android\.gms:play-services-cast-framework.*\n', '', s, flags=re.M)
    s = re.sub(r'^.*play-services-cast.*\n', '', s, flags=re.M)
    s = re.sub(r'^.*libs\.play\.services\.cast\.framework.*\n', '', s, flags=re.M)
    p.write_text(s)

# Remove internal audit artifact from final branch.
audit = ROOT / 'feature-audit.txt'
if audit.exists():
    audit.unlink()
