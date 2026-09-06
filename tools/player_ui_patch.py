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


logo = ROOT / 'app/src/main/res/drawable/elitestocks_tv_logo.png'
if logo.exists() and shutil.which('convert'):
    tmp = logo.with_suffix('.trimmed.png')
    subprocess.run(['convert', str(logo), '-trim', '+repage', str(tmp)], check=True)
    tmp.replace(logo)
    for p in ROOT.glob('app/src/main/res/mipmap-*/ic_launcher_vault.png'):
        shutil.copyfile(logo, p)

chrome = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerControlsChrome.kt'
s = read(chrome)
match = re.search(r'@Composable\s+fun PlayerControlsOverlay\s*\(', s)
if not match:
    raise RuntimeError('PlayerControlsOverlay declaration not found')

# The parameter list contains default lambdas such as `= {}`. Never search for the
# first brace after the declaration. Find the declaration's closing parenthesis first.
start_paren = match.end() - 1
depth = 0
quote = None
i = start_paren
while i < len(s):
    c = s[i]
    if quote:
        if c == '\\':
            i += 2
            continue
        if c == quote:
            quote = None
    else:
        if c in ('"', "'"):
            quote = c
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                signature_end = i
                break
    i += 1
else:
    raise RuntimeError('PlayerControlsOverlay parameter list is unbalanced')

body_match = re.search(r'\s*\{', s[signature_end + 1:])
if not body_match:
    raise RuntimeError('PlayerControlsOverlay body not found')
opening = signature_end + 1 + body_match.start() + body_match.group(0).find('{')
closing = find_matching_brace(s, opening)

args = [
    'visible', 'title', 'contentType', 'isCatchUpPlayback', 'isPlaying',
    'currentProgram', 'currentChannel', 'currentChannelName', 'displayChannelNumber',
    'currentPosition', 'duration', 'aspectRatioLabel', 'subtitleTrackCount',
    'liveTranslationAvailable', 'audioTrackCount', 'videoQualityCount',
    'currentRecordingStatus', 'isMuted', 'playbackSpeed', 'mediaTitle',
    'sleepTimerUiState', 'timeshiftUiState', 'playButtonFocusRequester',
    'quickActionsFocusRequester', 'onClose', 'onTogglePlayPause', 'onSeekBackward',
    'onSeekForward', 'onRestartProgram', 'onOpenArchive', 'onStartRecording',
    'onStopRecording', 'onScheduleRecording', 'onScheduleDailyRecording',
    'onScheduleWeeklyRecording', 'onToggleAspectRatio', 'onOpenSubtitleTracks',
    'onOpenAudioTracks', 'onOpenVideoTracks', 'onOpenPlaybackSpeed',
    'onOpenStopPlaybackTimer', 'onOpenIdleStandbyTimer', 'onOpenAudioVideoSync',
    'audioVideoSyncEnabled', 'showEpisodesAction', 'onOpenEpisodes',
    'onOpenSplitScreen', 'onEnterPictureInPicture', 'onToggleMute',
    'isCastConnected', 'onCast', 'onStopCasting', 'onSeekToLiveEdge',
    'onSeekToPosition', 'onSetScrubbingMode', 'showExternalPlayerAction',
    'onOpenExternalPlayer', 'seekPreview', 'onSeekPreviewPositionChanged',
    'onUserInteraction', 'modifier'
]

call = ',\n'.join(f'        {name} = {name}' for name in args)
body = f'''{{\n    PlayerCleanControls(\n{call}\n    )\n}}'''
s = s[:opening] + body + s[closing + 1:]
write(chrome, s)

clean = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerCleanControls.kt'
clean_text = read(clean)
clean_text = clean_text.replace(
    'contentDescription = stringResource(R.string.player_playback_label)',
    'contentDescription = "Playback position"'
)
write(clean, clean_text)
