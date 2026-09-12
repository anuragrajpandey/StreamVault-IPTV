from pathlib import Path
import re
import shutil

ROOT = Path('.')


def remove_function(text: str, name: str) -> str:
    pat = re.compile(r'(?m)^\s*(?:(?:public|private|protected|internal|override|suspend|inline)\s+)*fun\s+' + re.escape(name) + r'\s*\(')
    while True:
        m = pat.search(text)
        if not m:
            return text
        start = m.start()
        brace = text.find('{', m.end())
        if brace < 0:
            return text[:start] + text[m.end():]
        depth = 0
        i = brace
        in_string = False
        escaped = False
        while i < len(text):
            c = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == '"':
                    in_string = False
            else:
                if c == '"':
                    in_string = True
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return text[:start] + text[i + 1:]
            i += 1
        return text[:start]


def remove_class_or_interface(text: str, name: str) -> str:
    pat = re.compile(r'(?m)^\s*(?:(?:public|private|protected|internal|data|sealed|abstract|open|final)\s+)*(?:class|interface|object)\s+' + re.escape(name) + r'\b')
    while True:
        m = pat.search(text)
        if not m:
            return text
        start = m.start()
        brace = text.find('{', m.end())
        if brace < 0:
            return text[:start] + text[m.end():]
        depth = 0
        i = brace
        in_string = False
        escaped = False
        while i < len(text):
            c = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == '"':
                    in_string = False
            else:
                if c == '"':
                    in_string = True
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return text[:start] + text[i + 1:]
            i += 1
        return text[:start]


def rm(rel):
    p = ROOT / rel
    if p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()


roots = [
    ROOT / 'app/src/main', ROOT / 'app/src/test', ROOT / 'app/src/androidTest',
    ROOT / 'data/src/main', ROOT / 'data/src/test',
    ROOT / 'domain/src/main', ROOT / 'domain/src/test', ROOT / 'player/src/main'
]

# These files are feature-owned. Do NOT infer ownership from arbitrary filenames.
delete_names = {
    # Cast
    'CastManager.kt','CastMediaRequestFactory.kt','CastModels.kt','CastPlaybackCoordinator.kt',
    'CastRouteChooserActivity.kt','CastUiMessages.kt','StreamVaultCastOptionsProvider.kt','CastModule.kt','PlayerCastCoordinator.kt',
    # Downloads
    'DownloadForegroundService.kt','DownloadManagerImpl.kt','DownloadManager.kt','DownloadsScreen.kt','DownloadsUiState.kt','DownloadsViewModel.kt',
    'DownloadDao.kt','DownloadEntity.kt','DownloadStatus.kt','DownloadItem.kt','DownloadRequest.kt',
    # Recording/DVR
    'PlayerRecordingCoordinator.kt','RecordingManager.kt','RecordingManagerImpl.kt','RecordingModels.kt','RecordingConflictDetector.kt',
    'RecordingAlarmScheduler.kt','RecordingAlarmReceiver.kt','RecordingCaptureEngine.kt','RecordingForegroundIdleGate.kt',
    'RecordingForegroundService.kt','RecordingReconcileWorker.kt','RecordingRestoreReceiver.kt','RecordingServiceLauncher.kt',
    'RecordingSourceResolver.kt','RecordingSupport.kt','ScheduleRecording.kt','RecordingRecurrence.kt','RecordingStatus.kt','RecordingItem.kt',
    # Backup/restore
    'BackupFileBridge.kt','BackupManager.kt','BackupManagerImpl.kt','BackupRestoreStatusStoreImpl.kt','PendingBackupRestoreCoordinator.kt',
    'ExportBackup.kt','ImportBackup.kt','BackupRestoreCheckpointDao.kt','BackupRestoreLedgerDao.kt','BackupRestoreLedgerEntities.kt',
    'DriveBackupSyncManager.kt'
}

for root in roots:
    if root.exists():
        for p in list(root.rglob('*.kt')):
            if p.name in delete_names:
                p.unlink()

for rel in [
    'app/src/main/java/com/streamvault/app/cast',
    'app/src/main/java/com/streamvault/app/backup',
    'app/src/main/java/com/streamvault/app/ui/screens/downloads'
]:
    rm(rel)

# Preserve ProgramReminderDao inside the legacy RecordingDaos.kt container.
p = ROOT / 'data/src/main/java/com/streamvault/data/local/dao/RecordingDaos.kt'
if p.exists():
    s = p.read_text()
    marker = s.find('@Dao\ninterface ProgramReminderDao')
    if marker < 0:
        raise RuntimeError('ProgramReminderDao unexpectedly missing from RecordingDaos.kt')
    p.write_text('''package com.streamvault.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.streamvault.data.local.entity.ProgramReminderEntity
import com.streamvault.domain.model.ProgramReminderDeliveryState
import kotlinx.coroutines.flow.Flow

''' + s[marker:])

# Preserve ProgramReminderEntity inside the legacy RecordingEntities.kt container.
p = ROOT / 'data/src/main/java/com/streamvault/data/local/entity/RecordingEntities.kt'
if p.exists():
    s = p.read_text()
    marker = s.find('@Entity(\ntableName = "program_reminders"')
    if marker < 0:
        raise RuntimeError('ProgramReminderEntity unexpectedly missing from RecordingEntities.kt')
    p.write_text('''package com.streamvault.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import com.streamvault.domain.model.ProgramReminderDeliveryState

''' + s[marker:])

# Room model: remove recording/download/backup entities and DAO accessors, but retain reminders.
p = ROOT / 'data/src/main/java/com/streamvault/data/local/StreamVaultDatabase.kt'
if p.exists():
    s = p.read_text()
    for name in [
        'RecordingScheduleEntity','RecordingRunEntity','RecordingStorageEntity',
        'DownloadEntity','BackupRestoreCheckpointEntity','BackupRestoreJobEntity','BackupRestoreItemEntity'
    ]:
        s = re.sub(r'^\s*' + re.escape(name) + r'::class,\s*\n', '', s, flags=re.M)
    for name in [
        'recordingScheduleDao','recordingRunDao','recordingStorageDao',
        'downloadDao','backupRestoreCheckpointDao','backupRestoreLedgerDao'
    ]:
        s = re.sub(r'^\s*abstract fun ' + re.escape(name) + r'\([^\n]*\)\s*:\s*[^\n]+\n', '', s, flags=re.M)
    p.write_text(s)

# ProviderRepositoryImpl still had recorder-specific provider deletion plumbing.
p = ROOT / 'data/src/main/java/com/streamvault/data/repository/ProviderRepositoryImpl.kt'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^import .*RecordingAlarmScheduler.*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*private val recordingRunDao: RecordingRunDao,\n', '', s, flags=re.M)
    s = re.sub(r'^\s*private val recordingAlarmScheduler: RecordingAlarmScheduler,\n', '', s, flags=re.M)
    s = re.sub(r'^\s*val estimatedRecordingRunIds = recordingRunDao\.getIdsByProvider\(id\)\n', '', s, flags=re.M)
    s = re.sub(r'^\s*\(estimatedRecordingRunIds\.size \+ estimatedReminderIds\.size\) \* ALARM_STEP_WEIGHT \+\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*\(estimatedRecordingRunIds\.size \+ estimatedReminderIds\.size\) \* ALARM_STEP_WEIGHT\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*val recordingRunIds = recordingRunDao\.getIdsByProvider\(id\)\n', '', s, flags=re.M)
    s = re.sub(r'^\s*recordingRunIds\.map \{ ProviderDeletionCleanupEntity\([^\n]*\) \} \+\s*\n', '', s, flags=re.M)
    # Remove now-unused alarm weight constant if no longer referenced.
    s = re.sub(r'^\s*const val ALARM_STEP_WEIGHT = 5\s*\n', '', s, flags=re.M)
    p.write_text(s)

# Provider deletion cleanup now handles reminder alarms and sync runtime only.
p = ROOT / 'data/src/main/java/com/streamvault/data/repository/ProviderDeletionCleanupWorker.kt'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^import .*RecordingAlarmScheduler.*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*fun recordingAlarmScheduler\(\): RecordingAlarmScheduler\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*cancelRecordingAlarm = entry\.recordingAlarmScheduler\(\)::cancel,\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*const val RECORDING_ALARM = "RECORDING_ALARM"\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*cancelRecordingAlarm: \(String\) -> Unit,\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*ProviderDeletionCleanupWorker\.RECORDING_ALARM -> cancelRecordingAlarm\(item\.targetId\)\s*\n', '', s, flags=re.M)
    p.write_text(s)

# SyncManager no longer owns the backup/restore coordinator.
p = ROOT / 'data/src/main/java/com/streamvault/data/sync/SyncManager.kt'
if p.exists():
    s = p.read_text()
    s = re.sub(r'^import .*PendingBackupRestoreCoordinator.*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*private val pendingBackupRestoreCoordinator: PendingBackupRestoreCoordinator(?:\? = null)?\s*,?\s*\n', '', s, flags=re.M)
    p.write_text(s)

# Remove obsolete feature tests. Historical migration tests are intentionally not selected.
for test_root in [ROOT/'app/src/test', ROOT/'app/src/androidTest', ROOT/'data/src/test', ROOT/'domain/src/test']:
    if test_root.exists():
        for p in test_root.rglob('*.kt'):
            if any(x in p.name.lower() for x in ('download','backup','recording','cast')):
                p.unlink()

# Remove stale imports and obvious direct calls after the dependency surgery.
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob('*.kt'):
        s = p.read_text(errors='ignore')
        s = re.sub(r'^import .*\b(?:CastManager|CastMediaRequestFactory|CastPlaybackCoordinator|PlayerCastCoordinator|PlayerRecordingCoordinator|RecordingManager|RecordingItem|RecordingRecurrence|RecordingStatus|DownloadManager|PendingBackupRestoreCoordinator|BackupManager|BackupRepository|BackupRestore)\b.*\n', '', s, flags=re.M)
        s = re.sub(r'^import .*\.(?:cast|backup|downloads)\..*\n', '', s, flags=re.M)
        p.write_text(s)

# PlayerViewModel cleanup.
p = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/PlayerViewModel.kt'
if p.exists():
    s = p.read_text()
    for name in ['CastConnectionState','CastPlaybackReportMode','RecordingItem','RecordingRecurrence','RecordingStatus']:
        s = re.sub(r'^import .*\b'+name+r'\b.*\n','',s,flags=re.M)
    for line in [
        r'^\s*internal val playerRecordingCoordinator: PlayerRecordingCoordinator,\s*\n',
        r'^\s*internal val playerCastCoordinator: PlayerCastCoordinator,\s*\n',
        r'^\s*private var downloadPlaybackSlotActive.*\n',
        r'^\s*private var currentPlaybackUsesDownloadSlot.*\n',
        r'^\s*private var externalProviderPlaybackHold.*\n',
        r'^\s*internal val _recordingItems.*\n',
        r'^\s*val recordingItems.*\n',
        r'^\s*internal val currentChannelFlowRecording.*\n',
        r'^\s*internal val _resumePrompt.*\n',
        r'^\s*val resumePrompt.*\n',
        r'^\s*observeCastPlaybackEvents\(\)\s*\n'
    ]:
        s = re.sub(line,'',s,flags=re.M)
    for fn in ['refreshCurrentChannelRecording','handleRecordingStateChanges']:
        s = remove_function(s,fn)
    # Remove observer coroutine using its unique feature call, preserving neighboring collectors.
    while 'playerRecordingCoordinator.observeRecordingItems()' in s:
        marker=s.find('playerRecordingCoordinator.observeRecordingItems()')
        start=s.rfind('viewModelScope.launch',0,marker)
        if start<0: break
        brace=s.find('{',start); depth=0; i=brace
        while i<len(s):
            if s[i]=='{': depth+=1
            elif s[i]=='}':
                depth-=1
                if depth==0:
                    s=s[:start]+s[i+1:]
                    break
            i+=1
    # Replace old resume prompt block using its stable comment marker.
    old_marker='// Check for resume position after the player is fully prepared (VOD only).'
    if old_marker in s:
        start=s.find(old_marker)
        # Find the end of the enclosing if/blocks by starting at the line's preceding indentation.
        start=s.rfind('\n',0,start)+1
        brace=s.find('{',start); depth=0; i=brace
        while i<len(s):
            if s[i]=='{': depth+=1
            elif s[i]=='}':
                depth-=1
                if depth==0:
                    # This is the inner if body. Continue through the outer content guard,
                    # whose closing braces are the next two balanced closures.
                    i+=1
                    break
            i+=1
        # Remove the complete legacy section conservatively by matching from comment through
        # the closing brace immediately before the launch block ends.
        end=i
        for _ in range(2):
            while end<len(s) and s[end].isspace(): end+=1
            if end<len(s) and s[end]=='}': end+=1
        replacement='''                // Automatically restore saved VOD/series progress after preparation.\n                if (currentContentType != ContentType.LIVE && currentContentId != -1L && currentProviderId != -1L) {\n                    val history = playbackHistoryCoordinator.getPlaybackHistory(\n                        contentId = currentContentId,\n                        contentType = currentContentType,\n                        providerId = currentProviderId,\n                        seriesId = currentSeriesId,\n                        seasonNumber = currentSeasonNumber,\n                        episodeNumber = currentEpisodeNumber\n                    )\n                    if (isActivePlaybackSession(requestVersion, playbackLogicalUrl) &&\n                        history != null && history.resumePositionMs > 5000L &&\n                        !isPlaybackComplete(history.resumePositionMs, history.totalDurationMs)) {\n                        playerEngine.seekTo(history.resumePositionMs)\n                    }\n                }\n'''
        s=s[:start]+replacement+s[end:]
    s=s.replace('        showResumePrompt: Boolean = true\n','')
    s=re.sub(r',\s*showResumePrompt\s*=\s*true','',s)
    p.write_text(s)

# PlayerScreen: remove PiP, cast, recording, and resume-dialog presentation.
p=ROOT/'app/src/main/java/com/streamvault/app/ui/screens/player/PlayerScreen.kt'
if p.exists():
    s=p.read_text()
    s=re.sub(r'^import .*PlayerResumePrompt.*\n','',s,flags=re.M)
    s=re.sub(r'^import .*CastConnectionState.*\n','',s,flags=re.M)
    for n in ['castConnectionState','currentChannelRecording','resumePrompt']:
        s=re.sub(r'^\s*val '+n+r' by .*\n','',s,flags=re.M)
    s=s.replace('BackHandler(enabled = !resumePrompt.show)','BackHandler')
    # Remove prompt UI by balanced block.
    m=re.search(r'(?m)^\s*if \(resumePrompt\.show\)\s*\{',s)
    if m:
        depth=1;i=m.end()
        while i<len(s) and depth:
            if s[i]=='{': depth+=1
            elif s[i]=='}': depth-=1
            i+=1
        s=s[:m.start()]+s[i:]
    s=re.sub(r'\n\s*val notificationPermissionGate = .*?(?=\n\s*val |\n\s*LaunchedEffect|\n\s*BackHandler)', '\n', s, flags=re.S)
    s=re.sub(r'\n\s*val isInPictureInPictureMode = .*?\n\s*\?: false\n','\n',s,flags=re.S)
    s=re.sub(r'\n\s*val enterPictureInPicture = .*?\n\s*}\n','\n',s,flags=re.S)
    s=re.sub(r'\n\s*val currentPictureInPictureMode .*?\n','\n',s)
    s=re.sub(r'\n\s*LaunchedEffect\(mainActivity, streamUrl, playbackState, isPlaying, videoFormat\.width, videoFormat\.height, videoFormat\.pixelWidthHeightRatio\).*?\n\s*}\n','\n',s,flags=re.S)
    s=re.sub(r'\n\s*LaunchedEffect\(isInPictureInPictureMode\).*?\n\s*}\n','\n',s,flags=re.S)
    s=re.sub(r'\n\s*LifecycleEventEffect\(Lifecycle\.Event\.ON_STOP\).*?\n\s*}\n','\n',s,flags=re.S)
    s=re.sub(r'\n\s*DisposableEffect\(mainActivity\).*?\n\s*}\n','\n',s,flags=re.S)
    s=s.replace('!isInPictureInPictureMode && autoPlayCountdown != null','autoPlayCountdown != null')
    s=re.sub(r'^\s*(?:onCast[A-Za-z0-9_]*|onRecord[A-Za-z0-9_]*|onStartRecording|onStopRecording)\s*=.*\n','',s,flags=re.M)
    p.write_text(s)

# MainActivity: remove only player PiP and backup import-intent helpers.
p=ROOT/'app/src/main/java/com/streamvault/app/MainActivity.kt'
if p.exists():
    s=p.read_text()
    s=re.sub(r'^import android\.util\.Rational\n','',s,flags=re.M)
    s=re.sub(r'^import android\.content\.pm\.PackageManager\n','',s,flags=re.M)
    for n in ['updatePlayerPictureInPictureState','clearPlayerPictureInPictureState','enterPlayerPictureInPictureModeFromPlayer','enterPlayerPictureInPictureModeIfEligible','applyPlayerPictureInPictureParams','videoAspectRatioOrNull','supportsPictureInPicture','readImportedBackupUri','isBackupJsonCandidate','readStreamUriExtra']:
        s=remove_function(s,n)
    s=re.sub(r'\n\s*override fun onUserLeaveHint\(\).*?\n\s*}\n','\n',s,flags=re.S)
    s=re.sub(r'\n\s*override fun onPictureInPictureModeChanged\(.*?\n\s*}\n','\n',s,flags=re.S)
    p.write_text(s)

# Navigation and obsolete settings entry points.
p=ROOT/'app/src/main/java/com/streamvault/app/navigation/AppNavigation.kt'
if p.exists():
    s=p.read_text()
    s=re.sub(r'^import .*DownloadsScreen.*\n','',s,flags=re.M)
    s=re.sub(r'^\s*const val DOWNLOADS\s*=.*\n','',s,flags=re.M)
    s=re.sub(r'^\s*AppLandingDestination\.DOWNLOADS.*\n','',s,flags=re.M)
    s=re.sub(r'^\s*AppTopLevelDestination\.DOWNLOADS.*\n','',s,flags=re.M)
    s=s.replace('settings?backupUri={backupUri}','settings')
    s=re.sub(r'fun settings\(backupUri: String\? = null\)\s*=.*\n','fun settings() = Routes.SETTINGS_DESTINATION\n',s)
    p.write_text(s)

# Obsolete settings UI files.
for rel in [
    'app/src/main/java/com/streamvault/app/ui/screens/settings/SettingsBackupActions.kt',
    'app/src/main/java/com/streamvault/app/ui/screens/settings/SettingsBackupImportPreviewDialog.kt'
]: rm(rel)
for p in (ROOT/'app/src/main/java/com/streamvault/app/ui/screens/settings').glob('SettingsRecording*.kt'):
    p.unlink()

# Startup/service/manifest/Gradle integrations.
for rel in [
    'app/src/main/java/com/streamvault/app/service/DownloadForegroundService.kt'
]: rm(rel)

p=ROOT/'app/src/main/AndroidManifest.xml'
if p.exists():
    s=p.read_text()
    s=re.sub(r'^\s*android:supportsPictureInPicture="true"\s*\n','',s,flags=re.M)
    s=re.sub(r'^\s*<activity[^>]*(?:CastRouteChooserActivity)[^>]*/>\s*\n','',s,flags=re.M|re.I)
    s=re.sub(r'^\s*<service[^>]*(?:DownloadForegroundService|RecordingForegroundService)[^>]*/>\s*\n','',s,flags=re.M|re.I)
    s=re.sub(r'^\s*<meta-data[^>]*CAST\.framework\.OPTIONS_PROVIDER_CLASS_NAME[^>]*/>\s*\n','',s,flags=re.M|re.I)
    p.write_text(s)

for p in [ROOT/'app/build.gradle.kts',ROOT/'build.gradle.kts',ROOT/'gradle/libs.versions.toml']:
    if p.exists():
        s=p.read_text()
        s=re.sub(r'^.*play-services-cast.*\n','',s,flags=re.M|re.I)
        s=re.sub(r'^.*libs\.play\.services\.cast\.framework.*\n','',s,flags=re.M)
        s=re.sub(r'^.*libs\.mediarouter.*\n','',s,flags=re.M)
        p.write_text(s)

# Application/startup stale references.
for rel in [
    'app/src/main/java/com/streamvault/app/StreamVaultApp.kt',
    'app/src/main/java/com/streamvault/app/StartupWorkRegistry.kt',
    'app/src/main/java/com/streamvault/app/plugins/StreamVaultPluginManager.kt'
]:
    p=ROOT/rel
    if p.exists():
        s=p.read_text()
        s=re.sub(r'^import .*\b(?:DownloadManager|RecordingReconcileWorker|PendingBackupRestoreCoordinator|BackupManager|CastManager)\b.*\n','',s,flags=re.M)
        s=re.sub(r'^\s*.*\b(?:downloadManager|pendingBackupRestoreCoordinator|recordingReconcileWorker)\b.*\n','',s,flags=re.M)
        p.write_text(s)

# Final source-only cleanup of exact forbidden types. Historical migration code is exempted later by audit.
for root in roots:
    if not root.exists(): continue
    for p in root.rglob('*.kt'):
        s=p.read_text(errors='ignore')
        s=re.sub(r'^import .*\b(?:Cast|Download|Recording|Backup)(?:[A-Za-z0-9_]*)\b.*\n','',s,flags=re.M)
        p.write_text(s)

# The Android platform android:allowBackup attribute is deliberately preserved.
PY

git diff --check
