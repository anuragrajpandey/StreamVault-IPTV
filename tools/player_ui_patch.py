from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path('.')


def read(path):
    return path.read_text(encoding='utf-8').replace('\r\n', '\n')


def write(path, text):
    path.write_text(text, encoding='utf-8', newline='\n')


def find_matching_brace(source, opening):
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    i = opening
    while i < len(source):
        c = source[i]
        n = source[i + 1] if i + 1 < len(source) else ''
        if line_comment:
            if c == '\n':
                line_comment = False
        elif block_comment:
            if c == '*' and n == '/':
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                quote = None
        else:
            if c == '/' and n == '/':
                line_comment = True
                i += 1
            elif c == '/' and n == '*':
                block_comment = True
                i += 1
            elif c in ('"', "'"):
                quote = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise RuntimeError('Unbalanced Kotlin braces')


# Remove the unwanted blank/white canvas around the supplied EliteStocks TV logo.
logo = ROOT / 'app/src/main/res/drawable/elitestocks_tv_logo.png'
if logo.exists() and shutil.which('convert'):
    tmp = logo.with_suffix('.trimmed.png')
    subprocess.run(['convert', str(logo), '-trim', '+repage', str(tmp)], check=True)
    tmp.replace(logo)
    for p in ROOT.glob('app/src/main/res/mipmap-*/ic_launcher_vault.png'):
        shutil.copyfile(logo, p)

# Make the transparent player overlay deterministic. The previous patch relied on an
# exact newline sequence and could silently leave the old chrome in place.
chrome = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerControlsChrome.kt'
s = read(chrome)
match = re.search(r'@Composable\s+fun PlayerControlsOverlay\s*\(', s)
if not match:
    raise RuntimeError('PlayerControlsOverlay declaration not found')
opening = s.find('{', match.end())
if opening < 0:
    raise RuntimeError('PlayerControlsOverlay body not found')
closing = find_matching_brace(s, opening)
body = '''{
    PlayerCleanControls(
        visible = visible,
        title = title,
        contentType = contentType,
        isCatchUpPlayback = isCatchUpPlayback,
        isPlaying = isPlaying,
        currentProgram = currentProgram,
        currentChannel = currentChannel,
        currentChannelName = currentChannelName,
        displayChannelNumber = displayChannelNumber,
        currentPosition = currentPosition,
        duration = duration,
        aspectRatioLabel = aspectRatioLabel,
        subtitleTrackCount = subtitleTrackCount,
        liveTranslationAvailable = liveTranslationAvailable,
        audioTrackCount = audioTrackCount,
        videoQualityCount = videoQualityCount,
        currentRecordingStatus = currentRecordingStatus,
        isMuted = isMuted,
        playbackSpeed = playbackSpeed,
        mediaTitle = mediaTitle,
        sleepTimerUiState = sleepTimerUiState,
        timeshiftUiState = timeshiftUiState,
        playButtonFocusRequester = playButtonFocusRequester,
        quickActionsFocusRequester = quickActionsFocusRequester,
        onClose = onClose,
        onTogglePlayPause = onTogglePlayPause,
        onSeekBackward = onSeekBackward,
        onSeekForward = onSeekForward,
        onRestartProgram = onRestartProgram,
        onOpenArchive = onOpenArchive,
        onStartRecording = onStartRecording,
        onStopRecording = onStopRecording,
        onScheduleRecording = onScheduleRecording,
        onScheduleDailyRecording = onScheduleDailyRecording,
        onScheduleWeeklyRecording = onScheduleWeeklyRecording,
        onToggleAspectRatio = onToggleAspectRatio,
        onOpenSubtitleTracks = onOpenSubtitleTracks,
        onOpenAudioTracks = onOpenAudioTracks,
        onOpenVideoTracks = onOpenVideoTracks,
        onOpenPlaybackSpeed = onOpenPlaybackSpeed,
        onOpenStopPlaybackTimer = onOpenStopPlaybackTimer,
        onOpenIdleStandbyTimer = onOpenIdleStandbyTimer,
        onOpenAudioVideoSync = onOpenAudioVideoSync,
        audioVideoSyncEnabled = audioVideoSyncEnabled,
        showEpisodesAction = showEpisodesAction,
        onOpenEpisodes = onOpenEpisodes,
        onOpenSplitScreen = onOpenSplitScreen,
        onEnterPictureInPicture = onEnterPictureInPicture,
        onToggleMute = onToggleMute,
        isCastConnected = isCastConnected,
        onCast = onCast,
        onStopCasting = onStopCasting,
        onSeekToLiveEdge = onSeekToLiveEdge,
        onSeekToPosition = onSeekToPosition,
        onSetScrubbingMode = onSetScrubbingMode,
        showExternalPlayerAction = showExternalPlayerAction,
        onOpenExternalPlayer = onOpenExternalPlayer,
        seekPreview = seekPreview,
        onSeekPreviewPositionChanged = onSeekPreviewPositionChanged,
        onUserInteraction = onUserInteraction,
        modifier = modifier
    )
}'''
s = s[:opening] + body + s[closing + 1:]
write(chrome, s)

# Compose semantics lambdas are not @Composable. Remove the resource lookup from
# the slider semantics while keeping the player UI accessible.
clean = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerCleanControls.kt'
clean_text = read(clean)
clean_text = clean_text.replace(
    'contentDescription = stringResource(R.string.player_playback_label)',
    'contentDescription = "Playback position"'
)
write(clean, clean_text)
