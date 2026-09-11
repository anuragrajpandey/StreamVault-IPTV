from pathlib import Path
import re
import shutil

ROOT = Path('.')
APP = ROOT / 'app/src/main/java/com/streamvault/app'

# Remove dedicated TV-irrelevant feature implementations wherever they live.
for base in [ROOT / 'app/src/main', ROOT / 'data/src/main', ROOT / 'domain/src/main', ROOT / 'player/src/main']:
    if not base.exists():
        continue
    for p in list(base.rglob('*')):
        if not p.is_file():
            continue
        low = p.name.lower()
        rel = str(p.relative_to(base)).lower()
        if any(k in low for k in ('downloadmanager', 'downloadforegroundservice', 'downloadrepository', 'downloadworker', 'backupmanager', 'backuprepository', 'backupworker', 'backuprestore', 'pendingbackup', 'recordingmanager', 'recordingrepository', 'recordingworker', 'recordingreconcile', 'playerrecordingcoordinator', 'playercastcoordinator')):
            p.unlink()
            continue
        if '/backup/' in rel or '/downloads/' in rel or '/recording/' in rel or '/cast/' in rel:
            p.unlink()

# Known feature files/packages.
for rel in [
    'cast', 'backup', 'ui/screens/downloads',
    'service/DownloadForegroundService.kt',
    'ui/screens/player/PlayerCastCoordinator.kt',
    'ui/screens/player/PlayerRecordingCoordinator.kt',
    'player/PlayerCastCoordinator.kt',
    'player/PlayerRecordingCoordinator.kt',
    'di/CastModule.kt',
]:
    p = APP / rel
    if p.is_dir(): shutil.rmtree(p)
    elif p.exists(): p.unlink()

# Exact domain-level feature sources that do not have feature names in their filenames.
for rel in [
    'domain/src/main/java/com/streamvault/domain/model/RecordingModels.kt',
    'domain/src/main/java/com/streamvault/domain/usecase/ScheduleRecording.kt',
    'domain/src/main/java/com/streamvault/domain/usecase/ExportBackup.kt',
    'domain/src/main/java/com/streamvault/domain/usecase/ImportBackup.kt',
]:
    p = ROOT / rel
    if p.exists():
        p.unlink()

# Remove imports of deleted feature APIs.
import_patterns = [
    r'^import .*\b(?:cast|Cast[A-Za-z0-9_]*|backup|Backup[A-Za-z0-9_]*|download|Download[A-Za-z0-9_]*|recording|Recording[A-Za-z0-9_]*)\b.*\n',
    r'^import com\.streamvault\.domain\.repository\.DownloadManager\n',
]

for p in ROOT.rglob('*.kt'):
    s = p.read_text()
    old = s
    for pat in import_patterns:
        s = re.sub(pat, '', s, flags=re.I | re.M)
    if s != old:
        p.write_text(s)


def remove_functions(text, names):
    for name in names:
        rx = re.compile(r'(?ms)^\s*(?:(?:public|private|protected|internal|override|suspend|inline)\s+)*fun\s+' + re.escape(name) + r'\s*\([^\{]*\)\s*(?::\s*[^\{]+)?\{')
        while True:
            m = rx.search(text)
            if not m:
                break
            i, depth = m.end(), 1
            while i < len(text) and depth:
                if text[i] == '{': depth += 1
                elif text[i] == '}': depth -= 1
                i += 1
            text = text[:m.start()] + text[i:]
    return text

# Strip feature-specific functions before removing their fields/constructor parameters.
feature_fun_names = [
    'downloadMovie', 'downloadEpisode', 'download', 'startDownload', 'enqueueDownload', 'cancelDownload',
    'restoreBackup', 'createBackup', 'exportBackup', 'importBackup', 'backupNow', 'restoreNow',
    'startRecording', 'stopRecording', 'scheduleRecording', 'cancelRecording', 'recordChannel',
    'castMovie', 'castEpisode', 'castResumeEpisode', 'startCasting', 'openCastRouteChooser',
    'observeCastPlaybackEvents', 'handleCastPlaybackEvent', 'emitCastResult',
]

for p in ROOT.rglob('*.kt'):
    s = p.read_text()
    old = s
    s = remove_functions(s, feature_fun_names)

    # Remove constructor parameters, injected fields, and obvious feature-only state.
    for term in [
        'DownloadManager', 'PendingBackupRestoreCoordinator', 'CastMediaRequestFactory',
        'CastPlaybackCoordinator', 'PlayerCastCoordinator', 'PlayerRecordingCoordinator',
        'RecordingManager', 'RecordingItem', 'RecordingRecurrence', 'RecordingStatus',
        'BackupManager', 'BackupRepository', 'BackupRestore', 'CastConnectionState',
        'CastPlaybackReportMode', 'CastMediaRequest', 'CastStartResult',
    ]:
        s = re.sub(r'^\s*(?:@Inject\s*\n\s*)?(?:(?:private|public|internal|protected)\s+)?(?:lateinit\s+)?(?:val|var)\s+\w+\s*:\s*[^\n]*\b' + re.escape(term) + r'\b[^\n]*\n', '', s, flags=re.M)
        s = re.sub(r'^\s*(?:private\s+|public\s+|internal\s+|protected\s+)?val\s+\w+\s*:\s*' + re.escape(term) + r'[^\n]*\n', '', s, flags=re.M)
        s = re.sub(r'^\s*(?:private\s+)?val\s+\w+\s*:\s*[^\n]*\b' + re.escape(term) + r'\b[^\n]*,?\n', '', s, flags=re.M)

    # Remove feature-specific one-line state/calls left behind by the codemod.
    s = re.sub(r'^.*\b(?:castEvents|isCasting|castManager|castPlaybackCoordinator|castMediaRequestFactory|castPlaybackReportMode|recordingItems|currentChannelRecording|notifiedRecordingFailureIds|livePlaybackRecordCoordinator|resumePrompt)\b.*\n', '', s, flags=re.I | re.M)
    s = re.sub(r'^.*\b(?:downloadManager|pendingBackupRestoreCoordinator)\b.*\n', '', s, flags=re.M)
    s = re.sub(r'^.*\b(?:RecordingItem|RecordingRecurrence|RecordingStatus|BackupManagerImpl|RecordingManagerImpl|GoogleDriveBackupSyncManager)\b.*\n', '', s, flags=re.M)

    if s != old:
        p.write_text(s)

# Application startup integrations that are not needed on TV.
p = APP / 'StreamVaultApp.kt'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^import .*\b(?:RecordingReconcileWorker|PendingBackupRestoreCoordinator|DownloadManager)\b.*\n', '', s, flags=re.M)
    s = re.sub(r'^.*\b(?:downloadManager|pendingBackupRestoreCoordinator)\b.*\n', '', s, flags=re.M)
    p.write_text(s)

# Navigation: remove Downloads and backup-specific settings URI.
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

# Manifest cleanup. Keep Android platform backup support untouched.
p = ROOT / 'app/src/main/AndroidManifest.xml'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^\s*android:supportsPictureInPicture="true"\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<activity[^>]*CastRouteChooserActivity[^>]*/>\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<service[^>]*DownloadForegroundService[^>]*/>\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<meta-data[^>]*CAST\.framework\.OPTIONS_PROVIDER_CLASS_NAME[^>]*/>\s*\n', '', s, flags=re.M)
    p.write_text(s)

# Remove Cast dependencies and version-catalog aliases.
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
