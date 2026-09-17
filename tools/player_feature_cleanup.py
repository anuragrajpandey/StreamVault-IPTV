from pathlib import Path
import re

ROOT = Path('.')


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')


def replace_function_body(source, signature, body):
    start = source.find(signature)
    if start < 0:
        return source
    brace = source.find('{', start)
    if brace < 0:
        raise RuntimeError(f'Function body not found: {signature}')
    depth = 0
    quote = False
    triple = False
    escaped = False
    i = brace
    while i < len(source):
        if not triple and source.startswith('"""', i):
            triple = True
            i += 3
            continue
        if triple:
            if source.startswith('"""', i):
                triple = False
                i += 3
                continue
            i += 1
            continue
        c = source[i]
        if quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                quote = False
        else:
            if c == '"':
                quote = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return source[:brace] + '{\n' + body.rstrip() + '\n    }' + source[i + 1:]
        i += 1
    raise RuntimeError(f'Unbalanced function: {signature}')


# PiP is intentionally disabled in the shipped player. Keep the activity API
# source-compatible, but never advertise or enter PiP.
p = ROOT / 'app/src/main/java/com/streamvault/app/MainActivity.kt'
if p.exists():
    s = read(p)
    s = replace_function_body(
        s,
        'fun updatePlayerPictureInPictureState(',
        'playerPictureInPictureState = PlayerPictureInPictureState()\n'
        '        _pictureInPictureModeFlow.value = false'
    )
    s = replace_function_body(
        s,
        'fun clearPlayerPictureInPictureState()',
        'playerPictureInPictureState = PlayerPictureInPictureState()\n'
        '        _pictureInPictureModeFlow.value = false'
    )
    s = replace_function_body(
        s,
        'fun enterPlayerPictureInPictureModeFromPlayer()',
        'return false'
    )
    s = replace_function_body(
        s,
        'private fun enterPlayerPictureInPictureModeIfEligible(',
        'return false'
    )
    s = s.replace(
        '        enterPlayerPictureInPictureModeIfEligible()\n',
        '        // PiP intentionally disabled for the TV player.\n'
    )
    write(p, s)

# Remove PiP, Cast, and recording actions from the player surface while keeping
# playback/history code intact.
p = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/PlayerScreen.kt'
if p.exists():
    s = read(p)
    s = re.sub(
        r'\n    val isInPictureInPictureMode = mainActivity.*?\n        \?: false',
        '\n    val isInPictureInPictureMode = false',
        s,
        count=1,
        flags=re.S,
    )
    s = re.sub(
        r'\n    val currentPictureInPictureMode by rememberUpdatedState\(isInPictureInPictureMode\)\n    val enterPictureInPicture = remember\(mainActivity\) \{.*?\n    \}',
        '\n    val currentPictureInPictureMode = false\n    val enterPictureInPicture: () -> Unit = {}',
        s,
        count=1,
        flags=re.S,
    )
    s = re.sub(
        r'\n    LaunchedEffect\(mainActivity, streamUrl, playbackState, isPlaying, videoFormat\.width, videoFormat\.height, videoFormat\.pixelWidthHeightRatio\) \{.*?\n    \}',
        '',
        s,
        count=1,
        flags=re.S,
    )
    s = re.sub(r'\n    LaunchedEffect\(isInPictureInPictureMode\) \{.*?\n    \}', '', s, count=1, flags=re.S)
    s = s.replace('            mainActivity?.clearPlayerPictureInPictureState()\n', '')
    s = re.sub(
        r'\n    val currentChannelRecording by viewModel\.currentChannelRecording\.collectAsStateWithLifecycle\(\)',
        '\n    val currentChannelRecording = null',
        s,
        count=1,
    )
    s = re.sub(
        r'\n    val castConnectionState by viewModel\.castConnectionState\.collectAsStateWithLifecycle\(\)',
        '\n    val castConnectionState = CastConnectionState.DISCONNECTED',
        s,
        count=1,
    )
    s = re.sub(
        r'\n        if \(currentChannelRecording\?\.status == com\.streamvault\.domain\.model\.RecordingStatus\.RECORDING\) \{.*?\n        \}\n\n        when \(val resolutionState',
        '\n        when (val resolutionState',
        s,
        count=1,
        flags=re.S,
    )
    s = re.sub(
        r'onStartRecording = \{.*?\},\n            onStopRecording = viewModel::stopCurrentRecording,\n            onScheduleRecording = \{.*?\},\n            onScheduleDailyRecording = \{.*?\},\n            onScheduleWeeklyRecording = \{.*?\},',
        'onStartRecording = {},\n            onStopRecording = {},\n            onScheduleRecording = {},\n            onScheduleDailyRecording = {},\n            onScheduleWeeklyRecording = {},',
        s,
        count=1,
        flags=re.S,
    )
    s = re.sub(
        r'isCastConnected = castConnectionState == CastConnectionState\.CONNECTED,\n            onCast = \{.*?\},\n            onStopCasting = viewModel::stopCasting,',
        'isCastConnected = false,\n            onCast = {},\n            onStopCasting = {},',
        s,
        count=1,
        flags=re.S,
    )
    s = s.replace(
        '                    castConnectionState != CastConnectionState.CONNECTED,',
        '                    true,'
    )
    write(p, s)

# Keep the already-clean control chrome source-compatible, but make all
# deprecated action callbacks inert if another caller supplies them.
p = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerCleanControls.kt'
if p.exists():
    s = read(p)
    s = s.replace('onStartRecording: () -> Unit,', 'onStartRecording: () -> Unit = {},')
    s = s.replace('onStopRecording: () -> Unit,', 'onStopRecording: () -> Unit = {},')
    s = s.replace('onScheduleRecording: () -> Unit,', 'onScheduleRecording: () -> Unit = {},')
    s = s.replace('onScheduleDailyRecording: () -> Unit,', 'onScheduleDailyRecording: () -> Unit = {},')
    s = s.replace('onScheduleWeeklyRecording: () -> Unit,', 'onScheduleWeeklyRecording: () -> Unit = {},')
    s = s.replace('onEnterPictureInPicture: () -> Unit,', 'onEnterPictureInPicture: () -> Unit = {},')
    s = s.replace('onCast: () -> Unit,', 'onCast: () -> Unit = {},')
    s = s.replace('onStopCasting: () -> Unit,', 'onStopCasting: () -> Unit = {},')
    write(p, s)

print('Release cleanup: PiP, Cast, Recording actions disabled; automatic VOD resume and playback history retained.')
