from pathlib import Path
import re


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


def strip_lines(text: str, patterns) -> str:
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.M | re.I)
    return text


roots = [
    Path('app/src/main'), Path('app/src/test'), Path('app/src/androidTest'),
    Path('data/src/main'), Path('data/src/test'),
    Path('domain/src/main'), Path('domain/src/test'), Path('player/src/main')
]

# Only feature-owned files. Shared infrastructure is intentionally not selected by keyword.
delete_names = {
    'DownloadDao.kt','DownloadEntity.kt','DownloadStatus.kt','DownloadItem.kt','DownloadRequest.kt',
    'DownloadForegroundService.kt','DownloadManagerImpl.kt','DownloadManager.kt',
    'RecordingManager.kt','RecordingManagerImpl.kt','RecordingModels.kt','RecordingConflictDetector.kt',
    'RecordingAlarmScheduler.kt','RecordingAlarmReceiver.kt','RecordingCaptureEngine.kt',
    'RecordingForegroundIdleGate.kt','RecordingForegroundService.kt','RecordingReconcileWorker.kt',
    'RecordingRestoreReceiver.kt','RecordingServiceLauncher.kt','RecordingSourceResolver.kt','RecordingSupport.kt',
    'PlayerRecordingCoordinator.kt','ScheduleRecording.kt','RecordingRecurrence.kt','RecordingStatus.kt','RecordingItem.kt',
    'BackupFileBridge.kt','BackupManager.kt','BackupManagerImpl.kt','BackupRestoreStatusStoreImpl.kt',
    'PendingBackupRestoreCoordinator.kt','ExportBackup.kt','ImportBackup.kt',
    'BackupRestoreCheckpointDao.kt','BackupRestoreLedgerDao.kt','BackupRestoreLedgerEntities.kt',
    'DriveBackupSyncManager.kt','CastManager.kt','CastMediaRequestFactory.kt','CastModels.kt',
    'CastPlaybackCoordinator.kt','CastRouteChooserActivity.kt','CastUiMessages.kt',
    'StreamVaultCastOptionsProvider.kt','CastModule.kt','PlayerCastCoordinator.kt'
}

for root in roots:
    if root.exists():
        for p in root.rglob('*.kt'):
            if p.name in delete_names:
                p.unlink()

for d in [
    Path('app/src/main/java/com/streamvault/app/cast'),
    Path('app/src/main/java/com/streamvault/app/backup'),
    Path('app/src/main/java/com/streamvault/app/ui/screens/downloads')
]:
    if d.exists():
        for p in sorted(d.rglob('*'), reverse=True):
            if p.is_file(): p.unlink()
            elif p.is_dir(): p.rmdir()
        d.rmdir()

# RecordingDaos.kt also contained ProgramReminderDao. Keep only that unrelated reminder DAO.
dao = Path('data/src/main/java/com/streamvault/data/local/dao/RecordingDaos.kt')
if dao.exists():
    s = dao.read_text()
    marker = s.find('@Dao\ninterface ProgramReminderDao')
    if marker >= 0:
        dao.write_text('''package com.streamvault.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.streamvault.data.local.entity.ProgramReminderEntity
import com.streamvault.domain.model.ProgramReminderDeliveryState
import kotlinx.coroutines.flow.Flow

''' + s[marker:])
    else:
        dao.unlink()

# RecordingEntities.kt also contained ProgramReminderEntity. Keep only that entity.
ent = Path('data/src/main/java/com/streamvault/data/local/entity/RecordingEntities.kt')
if ent.exists():
    s = ent.read_text()
    marker = s.find('@Entity(\ntableName = "program_reminders"')
    if marker >= 0:
        ent.write_text('''package com.streamvault.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import com.streamvault.domain.model.ProgramReminderDeliveryState

''' + s[marker:])
    else:
        ent.unlink()

# SyncManager no longer needs the deleted backup-restore coordinator.
sync = Path('data/src/main/java/com/streamvault/data/sync/SyncManager.kt')
if sync.exists():
    s = sync.read_text()
    s = re.sub(r'^import com\.streamvault\.data\.manager\.PendingBackupRestoreCoordinator\n', '', s, flags=re.M)
    s = re.sub(r'^\s*private val pendingBackupRestoreCoordinator: PendingBackupRestoreCoordinator\? = null\n', '', s, flags=re.M)
    s = re.sub(r'^.*\bpendingBackupRestoreCoordinator\b.*\n', '', s, flags=re.M)
    sync.write_text(s)

# Remove tests whose subject is a feature that no longer exists.
for test_root in [Path('app/src/test'), Path('app/src/androidTest'), Path('data/src/test'), Path('domain/src/test')]:
    if test_root.exists():
        for p in test_root.rglob('*.kt'):
            if any(x in p.name.lower() for x in ('download','backup','recording','cast')):
                p.unlink()

feature_functions = [
    'downloadMovie','downloadEpisode','startDownload','enqueueDownload','cancelDownload','download',
    'restoreBackup','createBackup','exportBackup','importBackup','backupNow','restoreNow',
    'startRecording','stopRecording','scheduleRecording','cancelRecording','recordChannel',
    'castMovie','castEpisode','castResumeEpisode','startCasting','openCastRouteChooser',
    'observeCastPlaybackEvents','handleCastPlaybackEvent','emitCastResult'
]
feature_types = r'(?:DownloadManager|PendingBackupRestoreCoordinator|CastMediaRequestFactory|CastPlaybackCoordinator|PlayerCastCoordinator|PlayerRecordingCoordinator|RecordingManager|RecordingItem|RecordingRecurrence|RecordingStatus|BackupManager|BackupRepository|BackupRestore|CastConnectionState|CastPlaybackReportMode|CastMediaRequest|CastStartResult)'

for root in roots:
    if not root.exists():
        continue
    for p in root.rglob('*.kt'):
        s = p.read_text(errors='ignore')
        s = re.sub(r'^import .*\b(?:cast|backup|download|recording)\w*.*\n', '', s, flags=re.M | re.I)
        for fn in feature_functions:
            s = remove_function(s, fn)
        s = re.sub(r'^\s*(?:@Inject\s*)?(?:(?:private|public|internal|protected)\s+)?(?:val|var)\s+\w+\s*:\s*[^\n]*\b' + feature_types + r'\b[^\n]*\n', '', s, flags=re.M | re.I)
        s = re.sub(r'^.*\b(?:recordingItems|currentChannelRecording|notifiedRecordingFailureIds|downloadManager|pendingBackupRestoreCoordinator|castEvents|castConnectionState|castPlaybackReportMode)\b.*\n', '', s, flags=re.M | re.I)
        p.write_text(s)

# PlayerViewModel: delete remaining legacy feature state and the malformed recording block.
p = Path('app/src/main/java/com/streamvault/app/ui/screens/player/PlayerViewModel.kt')
if p.exists():
    s = p.read_text()
    s = strip_lines(s, [
        r'^\s*internal val _resumePrompt.*\n',
        r'^\s*observeCastPlaybackEvents\(\)\s*\n',
        r'^\s*private var downloadPlaybackSlotActive.*\n',
        r'^\s*private var currentPlaybackUsesDownloadSlot.*\n',
        r'^\s*private var externalProviderPlaybackHold.*\n',
        r'^\s*internal val _recordingItems.*\n',
        r'^\s*val recordingItems.*\n',
        r'^\s*internal val currentChannelFlowRecording.*\n'
    ])
    s = re.sub(r'\n\s*viewModelScope\.launch \{\n\s*playerRecordingCoordinator\.observeRecordingItems\(\).*?\n\s*\}\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*val channelId = currentChannelFlow\.value\?\.id \?: -1L.*?\n\s*val playerError:', '\n\n    val playerError:', s, flags=re.S)
    s = re.sub(r'(?ms)\n\s*// Check for resume position after the player is fully prepared \(VOD only\)\..*?\n\s*}\n\s*}\n\s*}\n', '''\n                // Automatically restore saved VOD/series playback after preparation.\n                if (currentContentType != ContentType.LIVE && currentContentId != -1L && currentProviderId != -1L) {\n                    val history = playbackHistoryCoordinator.getPlaybackHistory(\n                        contentId = currentContentId,\n                        contentType = currentContentType,\n                        providerId = currentProviderId,\n                        seriesId = currentSeriesId,\n                        seasonNumber = currentSeasonNumber,\n                        episodeNumber = currentEpisodeNumber\n                    )\n                    if (isActivePlaybackSession(requestVersion, playbackLogicalUrl) &&\n                        history != null &&\n                        history.resumePositionMs > 5000L &&\n                        !isPlaybackComplete(history.resumePositionMs, history.totalDurationMs)\n                    ) {\n                        playerEngine.seekTo(history.resumePositionMs)\n                    }\n                }\n            }\n        }\n''', s, count=1)
    s = s.replace('        showResumePrompt: Boolean = true\n', '')
    s = re.sub(r',\s*showResumePrompt\s*=\s*true', '', s)
    p.write_text(s)

# PlayerScreen: remove dialog/PiP/recording/cast state and effects.
p = Path('app/src/main/java/com/streamvault/app/ui/screens/player/PlayerScreen.kt')
if p.exists():
    s = p.read_text()
    s = strip_lines(s, [
        r'^import .*PlayerResumePrompt.*\n',
        r'^\s*val notificationPermissionGate =.*\n',
        r'^\s*val castConnectionState by .*\n',
        r'^\s*val currentChannelRecording by .*\n',
        r'^\s*val resumePrompt by .*\n'
    ])
    s = re.sub(r'\n\s*if \(resumePrompt\.show\).*?\n\s*}\n', '\n', s, flags=re.S)
    s = s.replace('BackHandler(enabled = !resumePrompt.show)', 'BackHandler')
    s = re.sub(r'\n\s*val isInPictureInPictureMode = .*?\n\s*\?: false\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*val enterPictureInPicture = .*?\n\s*}\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*LaunchedEffect\(mainActivity, streamUrl, playbackState, isPlaying, videoFormat\.width, videoFormat\.height, videoFormat\.pixelWidthHeightRatio\).*?\n\s*}\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*LaunchedEffect\(isInPictureInPictureMode\).*?\n\s*}\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*LifecycleEventEffect\(Lifecycle\.Event\.ON_STOP\).*?\n\s*}\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*DisposableEffect\(mainActivity\).*?\n\s*}\n', '\n', s, flags=re.S)
    s = s.replace('!isInPictureInPictureMode && autoPlayCountdown != null', 'autoPlayCountdown != null')
    p.write_text(s)

# MainActivity: remove player-specific PiP and backup-import plumbing.
p = Path('app/src/main/java/com/streamvault/app/MainActivity.kt')
if p.exists():
    s = p.read_text()
    s = strip_lines(s, [r'^import android\.util\.Rational\n', r'^import android\.content\.pm\.PackageManager\n', r'^import android\.net\.Uri\n'])
    for fn in ['updatePlayerPictureInPictureState','clearPlayerPictureInPictureState','enterPlayerPictureInPictureModeFromPlayer','enterPlayerPictureInPictureModeIfEligible','applyPlayerPictureInPictureParams','videoAspectRatioOrNull','supportsPictureInPicture','readImportedBackupUri','isBackupJsonCandidate','readStreamUriExtra']:
        s = remove_function(s, fn)
    s = re.sub(r'\n\s*override fun onUserLeaveHint\(\).*?\n\s*}\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*override fun onPictureInPictureModeChanged\(.*?\n\s*}\n', '\n', s, flags=re.S)
    s = re.sub(r'\n\s*private object PictureInPictureCompat.*?\n\s*}\n', '\n', s, flags=re.S)
    p.write_text(s)

# Manifest/Gradle cleanup. Platform android:allowBackup is intentionally untouched.
p = Path('app/src/main/AndroidManifest.xml')
if p.exists():
    s = p.read_text()
    s = re.sub(r'^\s*android:supportsPictureInPicture="true"\s*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*<activity[^>]*(?:CastRouteChooserActivity)[^>]*/>\s*\n', '', s, flags=re.M | re.I)
    s = re.sub(r'^\s*<service[^>]*(?:DownloadForegroundService|RecordingForegroundService)[^>]*/>\s*\n', '', s, flags=re.M | re.I)
    s = re.sub(r'^\s*<meta-data[^>]*CAST\.framework\.OPTIONS_PROVIDER_CLASS_NAME[^>]*/>\s*\n', '', s, flags=re.M | re.I)
    p.write_text(s)

for p in [Path('app/build.gradle.kts'), Path('build.gradle.kts'), Path('gradle/libs.versions.toml')]:
    if p.exists():
        s = p.read_text()
        s = re.sub(r'^.*play-services-cast.*\n', '', s, flags=re.M | re.I)
        s = re.sub(r'^.*libs\.play\.services\.cast\.framework.*\n', '', s, flags=re.M | re.I)
        s = re.sub(r'^.*libs\.mediarouter.*\n', '', s, flags=re.M | re.I)
        p.write_text(s)
