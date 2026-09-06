from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path('.')


def read(path):
    return path.read_text(encoding='utf-8').replace('\r\n', '\n')


def write(path, text):
    path.write_text(text, encoding='utf-8', newline='\n')


def matching_paren(source, opening):
    depth = 0
    quote = None
    escaped = False
    i = opening
    while i < len(source):
        c = source[i]
        if quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                quote = None
        else:
            if c in ('"', "'"):
                quote = c
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise RuntimeError('PlayerControlsOverlay parameter list is unbalanced')


# Make the launcher artwork transparent and safe inside Android's adaptive-icon mask.
logo = ROOT / 'app/src/main/res/drawable/elitestocks_tv_logo.png'
if logo.exists() and shutil.which('convert'):
    tmp = logo.with_suffix('.processed.png')
    subprocess.run([
        'convert', str(logo),
        '-fuzz', '8%', '-transparent', 'white',
        '-trim', '+repage',
        '-resize', '700x700',
        '-gravity', 'center', '-background', 'none',
        '-extent', '1080x1080',
        str(tmp)
    ], check=True)
    tmp.replace(logo)
    for path in ROOT.glob('app/src/main/res/mipmap-*/ic_launcher_vault.png'):
        shutil.copyfile(logo, path)

# Replace only PlayerControlsOverlay, bounded by the next top-level overlay function.
# This avoids parsing the large old body, which contains many nested lambdas/composables.
chrome = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerControlsChrome.kt'
s = read(chrome)
start_match = re.search(r'(?m)^@Composable\s+fun PlayerControlsOverlay\s*\(', s)
next_match = re.search(r'(?m)^@Composable\s+fun PlayerZapOverlay\s*\(', s)
if not start_match or not next_match or next_match.start() <= start_match.start():
    raise RuntimeError('PlayerControlsOverlay/PlayerZapOverlay boundaries not found')
start = start_match.start()
end = next_match.start()
segment = s[start:end]
open_paren = segment.find('(')
close_paren = matching_paren(segment, open_paren)
signature = segment[:close_paren + 1].rstrip()

# Extract the original parameter names so this patch cannot drift when the signature changes.
parameter_names = re.findall(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', signature, re.MULTILINE)
parameter_names = [name for name in parameter_names if name != 'clockLabelOverride']
call = ',\n'.join(f'        {name} = {name}' for name in parameter_names)
replacement = f'''{signature} {{
    PlayerCleanControls(
{call}
    )
}}

'''
s = s[:start] + replacement + s[end:]
write(chrome, s)

# Compose semantics lambdas are not composable contexts.
clean = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerCleanControls.kt'
text = read(clean)
text = text.replace(
    'contentDescription = stringResource(R.string.player_playback_label)',
    'contentDescription = "Playback position"'
)

# The physical display can be wider than the 16:9 video surface. Constrain the transparent
# overlay to that same centered viewport so bottom controls never sit in the side letterbox.
text = text.replace(
    'import androidx.compose.foundation.layout.fillMaxWidth\n',
    'import androidx.compose.foundation.layout.fillMaxWidth\nimport androidx.compose.foundation.layout.fillMaxHeight\nimport androidx.compose.foundation.layout.aspectRatio\n'
)
text = text.replace(
    'Box(modifier = modifier.fillMaxSize().background(Color.Transparent)) {',
    '''Box(modifier = modifier.fillMaxSize().background(Color.Transparent)) {
        Box(
            modifier = Modifier
                .fillMaxHeight()
                .aspectRatio(16f / 9f, matchHeightConstraintsFirst = true)
                .align(Alignment.Center)
        ) {'''
)
text = text.replace(
    '\n    }\n}\n\n@Composable\nprivate fun CleanIconButton',
    '\n        }\n    }\n}\n\n@Composable\nprivate fun CleanIconButton',
    1
)
write(clean, text)

# The existing fast-onboarding flag is intended for first login. Enable it for the
# initial setup while leaving persisted/background refresh policy unchanged.
provider_vm = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/provider/ProviderSetupViewModel.kt'
if provider_vm.exists():
    vm = read(provider_vm)
    marker = 'xtreamFastSyncEnabled = false,'
    if marker not in vm:
        raise RuntimeError('Xtream fast-sync flag not found')
    vm = vm.replace(marker, 'xtreamFastSyncEnabled = true,', 1)
    write(provider_vm, vm)
