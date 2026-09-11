from pathlib import Path
import re, shutil

ROOT = Path('.')
APP = ROOT / 'app/src/main/java/com/streamvault/app'

for rel in [
    'cast', 'backup', 'ui/screens/downloads',
    'service/DownloadForegroundService.kt',
    'player/PlayerCastCoordinator.kt',
    'player/PlayerRecordingCoordinator.kt',
]:
    p = APP / rel
    if p.is_dir(): shutil.rmtree(p)
    elif p.exists(): p.unlink()

for rel in ['di/CastModule.kt']:
    p = APP / rel
    if p.exists(): p.unlink()

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


def remove_cast_functions(text):
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    rx = re.compile(
        r'^\s*(?:(?:public|private|protected|internal|override|suspend|inline|tailrec|operator|infix)\s+)*'
        r'fun\s+(?:cast\w*|\w*cast\w*)\s*\(', re.I
    )
    while i < len(lines):
        if rx.match(lines[i]):
            depth = lines[i].count('{') - lines[i].count('}')
            i += 1
            while i < len(lines) and depth <= 0 and '{' not in lines[i]:
                i += 1
            if i < len(lines):
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return ''.join(out)

for p in ROOT.rglob('*.kt'):
    s = p.read_text()
    old = s
    s = remove_cast_functions(s)
    s = re.sub(r'^\s*(?:private\s+|public\s+|internal\s+|protected\s+)?(?:val|var)\s+\w*(?:Cast|cast)\w*\s*[:=].*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*@Inject\s*\n\s*(?:lateinit\s+)?var\s+\w*cast\w*\s*:\s*[^\n]+\n', '', s, flags=re.I | re.M)
    s = re.sub(r'^.*\b(?:castEvents|isCasting|CastUiEvent|CastPlaybackReportMode|CastStartResult|CastMediaRequest|CastMediaRequestBuildResult|castManager|castPlaybackCoordinator|castMediaRequestFactory|castPlaybackReportMode|openCastRouteChooser|castEpisode|castResumeEpisode|startCasting|isCast(?:ing)?)\b.*\n', '', s, flags=re.I)
    if s != old:
        p.write_text(s)


def clean_detail_viewmodel(path):
    p = ROOT / path
    if not p.exists():
        return
    s = p.read_text()
    # Remove DownloadManager/Cast constructor parameters without disturbing the remaining Hilt signature.
    s = re.sub(r'^\s*private val downloadManager: DownloadManager,\n', '', s, flags=re.M)
    s = re.sub(r'^\s*private val castMediaRequestFactory: CastMediaRequestFactory,\n', '', s, flags=re.M)
    s = re.sub(r'^\s*private val castPlaybackCoordinator: CastPlaybackCoordinator\n', '', s, flags=re.M)
    # Remove the entire download and cast methods and their helper methods.
    for name in ['downloadMovie', 'downloadEpisode', 'castMovie', 'castEpisode', 'castResumeEpisode', 'observeCastPlaybackEvents', 'handleCastPlaybackEvent', 'emitCastResult']:
        pattern = rf'(?ms)^\s*(?:private\s+|public\s+|internal\s+)?(?:suspend\s+)?fun\s+{name}\s*\([^{{]*\)\s*(?::\s*[^{{]+)?\{{'
        m = re.search(pattern, s)
        while m:
            start = m.start()
            i = m.end()
            depth = 1
            while i < len(s) and depth:
                if s[i] == '{': depth += 1
                elif s[i] == '}': depth -= 1
                i += 1
            s = s[:start] + s[i:]
            m = re.search(pattern, s)
    # Remove cast/download UI state fields.
    s = re.sub(r'^\s*private val _castEvents.*\n\s*val castEvents.*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*private var castPlaybackReportMode.*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*val isCasting: Boolean = false,\n', '', s, flags=re.M)
    s = re.sub(r'^\s*val isCasting: Boolean = false\n', '', s, flags=re.M)
    # Cast observation is no longer needed in init.
    s = s.replace('        observeCastPlaybackEvents()\n', '')
    p.write_text(s)

clean_detail_viewmodel('app/src/main/java/com/streamvault/app/ui/screens/movies/MovieDetailViewModel.kt')
clean_detail_viewmodel('app/src/main/java/com/streamvault/app/ui/screens/series/SeriesDetailViewModel.kt')

# Application-level download/backup startup integrations are not part of the TV app.
p = APP / 'StreamVaultApp.kt'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^import com\.streamvault\.data\.manager\.recording\.RecordingReconcileWorker\n', '', s, flags=re.M)
    s = re.sub(r'^import com\.streamvault\.data\.manager\.PendingBackupRestoreCoordinator\n', '', s, flags=re.M)
    s = re.sub(r'^\s*@Inject\n\s*lateinit var downloadManager: DownloadManager\n', '', s, flags=re.M)
    s = re.sub(r'^\s*@Inject\n\s*lateinit var pendingBackupRestoreCoordinator: PendingBackupRestoreCoordinator\n', '', s, flags=re.M)
    s = re.sub(r'^\s*\s*StartupTask\("download-recovery"\) \{\n\s*downloadManager\.recoverInterruptedDownloads\(\)\n\s*\},\n', '', s, flags=re.M)
    s = re.sub(r'^\s*\s*StartupTask\("pending-backup-restore"\) \{\n\s*pendingBackupRestoreCoordinator\.applyAllAvailable\(\)\n\s*\},\n', '', s, flags=re.M)
    p.write_text(s)

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

p = ROOT / 'app/src/main/AndroidManifest.xml'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^\s*android:supportsPictureInPicture="true"\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<activity[^>]*CastRouteChooserActivity[^>]*/>\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<service[^>]*DownloadForegroundService[^>]*/>\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<meta-data[^>]*CAST\.framework\.OPTIONS_PROVIDER_CLASS_NAME[^>]*/>\s*\n', '', s, flags=re.M)
    p.write_text(s)

for p in [ROOT / 'app/build.gradle.kts', ROOT / 'build.gradle.kts', ROOT / 'gradle/libs.versions.toml']:
    if p.exists():
        s = p.read_text()
        s = re.sub(r'^.*com\.google\.android\.gms:play-services-cast-framework.*\n', '', s, flags=re.M)
        s = re.sub(r'^.*play-services-cast.*\n', '', s, flags=re.M)
        s = re.sub(r'^.*libs\.play\.services\.cast\.framework.*\n', '', s, flags=re.M)
        p.write_text(s)

audit = ROOT / 'feature-audit.txt'
if audit.exists():
    audit.unlink()
