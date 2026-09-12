from pathlib import Path
import re

ROOTS = [Path('app/src/main'), Path('app/src/test'), Path('app/src/androidTest'), Path('data/src/main'), Path('data/src/test'), Path('domain/src/main'), Path('domain/src/test'), Path('player/src/main')]


def brace_delta(s):
    return s.count('{') - s.count('}')


def remove_block(text, marker):
    while marker in text:
        pos = text.find(marker)
        start = text.rfind('\n', 0, pos) + 1
        lines = text[start:].splitlines(True)
        depth = 0
        started = False
        end = start
        for line in lines:
            depth += brace_delta(line)
            end += len(line)
            if '{' in line:
                started = True
            if started and depth == 0:
                break
        else:
            return text
        text = text[:start] + text[end:]
    return text


def extract_block(text, marker):
    pos = text.find(marker)
    if pos < 0:
        raise RuntimeError(f'missing marker: {marker}')
    start = text.rfind('\n', 0, pos) + 1
    lines = text[start:].splitlines(True)
    out = []
    depth = 0
    started = False
    for line in lines:
        out.append(line)
        depth += brace_delta(line)
        if '{' in line:
            started = True
        if started and depth == 0:
            break
    return ''.join(out)


def header(text, marker):
    pos = text.find(marker)
    if pos < 0:
        raise RuntimeError(f'missing marker: {marker}')
    lines = text[:pos].splitlines(True)
    keep = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('package ') or stripped.startswith('import '):
            keep.append(line)
    return ''.join(keep) + '\n'


def remove_feature_lines(text):
    out = []
    for line in text.splitlines(True):
        if re.search(r'^(\s*import\s+).*(cast|recording|backup|downloads?)', line, re.I):
            continue
        if re.search(r'\b(?:PlayerCastCoordinator|PlayerRecordingCoordinator|RecordingRunDao|RecordingScheduleDao|RecordingStorageDao|RecordingAlarmScheduler|PendingBackupRestoreCoordinator|CastMediaRequestFactory|CastPlaybackCoordinator|CastRouteChooserActivity|DownloadDao|DownloadEntity|DownloadStatus|DownloadItem|DownloadRequest|BackupManagerImpl|BackupFileBridge|GoogleDriveBackupSyncManager|DriveBackupSyncManager)\b', line):
            continue
        if re.search(r'\b(?:recordingAlarmScheduler|recordingRunDao|pendingBackupRestoreCoordinator|playerRecordingCoordinator|playerCastCoordinator)\b', line):
            continue
        out.append(line)
    return ''.join(out)


# Preserve only Program Reminder from combined recording files.
dao = Path('data/src/main/java/com/streamvault/data/local/dao/RecordingDaos.kt')
if dao.exists():
    original = dao.read_text()
    dao.write_text(header(original, '@Dao\ninterface ProgramReminderDao') + extract_block(original, '@Dao\ninterface ProgramReminderDao'))

entities = Path('data/src/main/java/com/streamvault/data/local/entity/RecordingEntities.kt')
if entities.exists():
    original = entities.read_text()
    entities.write_text(header(original, '@Entity(\n    tableName = "program_reminders"') + extract_block(original, '@Entity(\n    tableName = "program_reminders"'))

# Delete feature-owned files only. Android update/download infrastructure is intentionally untouched.
delete_names = {
    'PlayerCastCoordinator.kt','CastMediaRequestFactory.kt','CastManager.kt','CastModels.kt','CastPlaybackCoordinator.kt','CastRouteChooserActivity.kt','CastUiMessages.kt','StreamVaultCastOptionsProvider.kt','CastModule.kt',
    'DownloadForegroundService.kt','DownloadManagerImpl.kt','DownloadManager.kt','DownloadsScreen.kt','DownloadsUiState.kt','DownloadsViewModel.kt','DownloadDao.kt','DownloadEntity.kt','DownloadStatus.kt','DownloadItem.kt','DownloadRequest.kt',
    'PlayerRecordingCoordinator.kt','RecordingManager.kt','RecordingManagerImpl.kt','RecordingModels.kt','RecordingConflictDetector.kt','RecordingAlarmScheduler.kt','RecordingAlarmReceiver.kt','RecordingCaptureEngine.kt','RecordingForegroundIdleGate.kt','RecordingForegroundService.kt','RecordingReconcileWorker.kt','RecordingRestoreReceiver.kt','RecordingServiceLauncher.kt','RecordingSourceResolver.kt','RecordingSupport.kt','ScheduleRecording.kt','RecordingRecurrence.kt','RecordingStatus.kt','RecordingItem.kt',
    'BackupFileBridge.kt','BackupManager.kt','BackupManagerImpl.kt','BackupRestoreStatusStoreImpl.kt','PendingBackupRestoreCoordinator.kt','ExportBackup.kt','ImportBackup.kt','BackupRestoreCheckpointDao.kt','BackupRestoreLedgerDao.kt','BackupRestoreLedgerEntities.kt','DriveBackupSyncManager.kt','GoogleDriveBackupSyncManager.kt','PlayerResumePrompt.kt'
}
for root in ROOTS:
    if root.exists():
        for path in root.rglob('*.kt'):
            if path.name in delete_names:
                path.unlink()
for directory in [Path('app/src/main/java/com/streamvault/app/cast'), Path('app/src/main/java/com/streamvault/app/backup'), Path('app/src/main/java/com/streamvault/app/ui/screens/downloads')]:
    if directory.exists():
        for path in sorted(directory.rglob('*'), reverse=True):
            if path.is_file(): path.unlink()
            elif path.is_dir(): path.rmdir()
        directory.rmdir()

# Room registrations.
db = Path('data/src/main/java/com/streamvault/data/local/StreamVaultDatabase.kt')
s = db.read_text()
for name in ['RecordingScheduleEntity','RecordingRunEntity','RecordingStorageEntity','DownloadEntity','BackupRestoreCheckpointEntity','BackupRestoreJobEntity','BackupRestoreItemEntity']:
    s = re.sub(r'^\s*' + name + r'\s*,?\s*$', '', s, flags=re.M)
for name in ['recordingScheduleDao','recordingRunDao','recordingStorageDao','downloadDao','backupRestoreCheckpointDao','backupRestoreLedgerDao']:
    s = re.sub(r'^\s*abstract fun ' + name + r'\([^\n]*\):[^\n]*$', '', s, flags=re.M)
db.write_text(s)

# Remove deleted feature dependencies from the remaining Kotlin source.
for root in ROOTS:
    if not root.exists():
        continue
    for path in root.rglob('*.kt'):
        s = remove_feature_lines(path.read_text(errors='ignore'))
        # Remove feature-only function bodies from settings/viewmodels/repositories.
        for match in list(re.finditer(r'^\s*(?:private |internal |public |override )*(?:suspend )?fun\s+\w*(?:Backup|Restore|Recording|Cast)\w*\s*\(', s, re.M)):
            s = remove_block(s, match.group(0))
            break
        path.write_text(s)

# Provider deletion cleanup keeps reminders and sync runtime, but not DVR alarms.
f = Path('data/src/main/java/com/streamvault/data/repository/ProviderRepositoryImpl.kt')
if f.exists():
    s = f.read_text()
    s = re.sub(r'^\s*val estimatedRecordingRunIds\s*=.*$', '', s, flags=re.M)
    s = s.replace('(estimatedRecordingRunIds.size + estimatedReminderIds.size) * ALARM_STEP_WEIGHT +\n', '')
    s = re.sub(r'^\s*val recordingRunIds\s*=.*$', '', s, flags=re.M)
    s = re.sub(r'\s*recordingRunIds\.map \{.*?\n\s*\}\s*\+\s*', ' ', s, flags=re.S)
    s = re.sub(r'^\s*private const val ALARM_STEP_WEIGHT.*$', '', s, flags=re.M)
    f.write_text(s)

f = Path('data/src/main/java/com/streamvault/data/repository/ProviderDeletionCleanupWorker.kt')
if f.exists():
    s = f.read_text()
    s = remove_block(s, 'is ProviderDeletionCleanupEntity.RECORDING_ALARM')
    s = re.sub(r'^\s*fun recordingAlarmScheduler\(\):.*$', '', s, flags=re.M)
    s = re.sub(r'^\s*cancelRecordingAlarm\s*=.*$', '', s, flags=re.M)
    s = re.sub(r'^\s*const val RECORDING_ALARM.*$', '', s, flags=re.M)
    s = re.sub(r'^\s*cancelRecordingAlarm\s*:\s*[^,\n]+,?$', '', s, flags=re.M)
    f.write_text(s)

# SyncManager backup coordinator.
f = Path('data/src/main/java/com/streamvault/data/sync/SyncManager.kt')
if f.exists():
    s = f.read_text()
    s = re.sub(r'^\s*private val pendingBackupRestoreCoordinator\s*:[^\n]+,?$', '', s, flags=re.M)
    f.write_text(s)

# Player ViewModel: remove DVR/Cast state and automatic VOD resume.
f = Path('app/src/main/java/com/streamvault/app/ui/screens/player/PlayerViewModel.kt')
if f.exists():
    s = f.read_text()
    for marker in ['internal fun refreshCurrentChannelRecording', 'private fun handleRecordingStateChanges']:
        s = remove_block(s, marker)
    s = re.sub(r'^\s*internal val _resumePrompt.*$', '', s, flags=re.M)
    s = re.sub(r'^\s*val resumePrompt.*$', '', s, flags=re.M)
    s = re.sub(r'^\s*internal var castPlaybackReportMode.*$', '', s, flags=re.M)
    s = re.sub(r'^\s*private var (?:downloadPlaybackSlotActive|currentPlaybackUsesDownloadSlot|externalProviderPlaybackHold).*$', '', s, flags=re.M)
    old = re.compile(r'(?ms)^\s*// Check for resume position after the player is fully prepared \(VOD only\)\..*?^\s*}\s*}\s*}\s*$')
    new = '''                // Automatically restore the saved VOD/series position after preparation.\n                if (currentContentType != ContentType.LIVE && currentContentId != -1L && currentProviderId != -1L) {\n                    val history = playbackHistoryCoordinator.getPlaybackHistory(\n                        contentId = currentContentId, contentType = currentContentType, providerId = currentProviderId,\n                        seriesId = currentSeriesId, seasonNumber = currentSeasonNumber, episodeNumber = currentEpisodeNumber\n                    )\n                    if (isActivePlaybackSession(requestVersion, playbackLogicalUrl) && history != null &&\n                        history.resumePositionMs > 5000L && !isPlaybackComplete(history.resumePositionMs, history.totalDurationMs)) {\n                        playerEngine.seekTo(history.resumePositionMs)\n                    }\n                }\n            }\n        }\n'''
    s = old.sub(new, s, count=1)
    s = s.replace('        showResumePrompt: Boolean = true\n', '')
    s = re.sub(r',\s*showResumePrompt\s*=\s*true', '', s)
    f.write_text(s)

# Player Screen.
f = Path('app/src/main/java/com/streamvault/app/ui/screens/player/PlayerScreen.kt')
if f.exists():
    s = f.read_text()
    s = re.sub(r'^\s*import .*PlayerResumePrompt.*$', '', s, flags=re.M)
    for marker in ['if (resumePrompt.show)', 'val enterPictureInPicture = remember(mainActivity)', 'DisposableEffect(mainActivity)', 'LaunchedEffect(isInPictureInPictureMode)', 'LifecycleEventEffect(Lifecycle.Event.ON_STOP)']:
        s = remove_block(s, marker)
    s = re.sub(r'^\s*val resumePrompt by .*$', '', s, flags=re.M)
    s = re.sub(r'^\s*val castConnectionState by .*$', '', s, flags=re.M)
    s = re.sub(r'^\s*(?:castConnectionState|currentChannelRecording)\s*=.*$', '', s, flags=re.M)
    s = re.sub(r'^\s*on(?:Cast|Record|StartRecording|StopRecording)[^\n]*$', '', s, flags=re.M)
    s = s.replace('BackHandler(enabled = !resumePrompt.show)', 'BackHandler')
    s = s.replace('!isInPictureInPictureMode && autoPlayCountdown != null', 'autoPlayCountdown != null')
    f.write_text(s)

# MainActivity player PiP helpers.
f = Path('app/src/main/java/com/streamvault/app/MainActivity.kt')
if f.exists():
    s = f.read_text()
    for marker in ['updatePlayerPictureInPictureState','clearPlayerPictureInPictureState','enterPlayerPictureInPictureModeFromPlayer','enterPlayerPictureInPictureModeIfEligible','applyPlayerPictureInPictureParams','videoAspectRatioOrNull','supportsPictureInPicture','private fun Intent.readImportedBackupUri','private fun Intent.isBackupJsonCandidate']:
        s = remove_block(s, marker)
    s = re.sub(r'^\s*import android\.util\.Rational\s*$', '', s, flags=re.M)
    s = re.sub(r'^\s*import android\.content\.pm\.PackageManager\s*$', '', s, flags=re.M)
    f.write_text(s)

# UI feature sections and callbacks.
ui = Path('app/src/main/java/com/streamvault/app/ui')
if ui.exists():
    for path in ui.rglob('*.kt'):
        s = path.read_text(errors='ignore')
        for marker in ['if (showLocalBackupManager)', 'if (showBackupRestore)', 'if (showRecording', 'if (recording', 'if (currentChannelRecording', 'if (resumePrompt.show)', 'RecordingControls(', 'CastControls(']:
            s = remove_block(s, marker)
        s = re.sub(r'^\s*.*(?:BackupRestore|backupRestore|recordingManager|recordingItems|currentChannelRecording|onStartRecording|onStopRecording|onRecord|onCast|castConnectionState|downloadsScreen|DownloadItem|RecordingItem).*$', '', s, flags=re.I|re.M)
        path.write_text(s)

# DI/startup declarations.
for name in ['app/src/main/java/com/streamvault/app/StreamVaultApp.kt','app/src/main/java/com/streamvault/app/di/DatabaseModule.kt','app/src/main/java/com/streamvault/app/di/RepositoryModule.kt']:
    f = Path(name)
    if f.exists():
        lines=[]
        for line in f.read_text().splitlines(True):
            if re.search(r'(Recording|Backup|Cast|Downloads?)', line, re.I):
                continue
            lines.append(line)
        f.write_text(''.join(lines))

# Manifest/dependencies.
f = Path('app/src/main/AndroidManifest.xml')
if f.exists():
    s = f.read_text()
    s = re.sub(r'\s*<[^>]*(?:Download|Recording|Cast)[^>]*/>', '', s, flags=re.I)
    s = re.sub(r'\s*<[^>]*(?:Download|Recording|Cast)[^>]*>.*?</[^>]+>', '', s, flags=re.I|re.S)
    f.write_text(s)
f = Path('app/build.gradle.kts')
if f.exists():
    s=f.read_text()
    s=re.sub(r'^\s*implementation\(libs\.play\.services\.cast\.framework\)\s*$', '', s, flags=re.M)
    s=re.sub(r'^\s*implementation\(libs\.mediarouter\)\s*$', '', s, flags=re.M)
    f.write_text(s)

# Feature tests.
for root in [Path('app/src/test'),Path('app/src/androidTest'),Path('data/src/test'),Path('domain/src/test')]:
    if root.exists():
        for path in root.rglob('*.kt'):
            if any(x in path.name.lower() for x in ['backup','recording','cast','downloads']):
                path.unlink()
