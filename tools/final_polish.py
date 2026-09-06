from pathlib import Path
import re, shutil

ROOT = Path('.')

def read(path):
    return Path(path).read_text(encoding='utf-8')

def write(path, value):
    Path(path).write_text(value, encoding='utf-8')

def replace_call(source, name, replacement):
    start = source.find(name + '(')
    if start < 0:
        return source
    p = start + len(name)
    depth = 0
    quote = False
    esc = False
    for i in range(p, len(source)):
        c = source[i]
        if quote:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': quote = False
        else:
            if c == '"': quote = True
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return source[:start] + replacement + source[i + 1:]
    raise RuntimeError(f'Unbalanced call: {name}')

src = ROOT / 'app/src/main/res/drawable/EliteStocksTV.png'
dst = ROOT / 'app/src/main/res/drawable/elitestocks_tv_logo.png'
if src.exists():
    shutil.copyfile(src, dst)
    src.unlink()
if dst.exists():
    for p in ROOT.glob('app/src/main/res/mipmap-*/ic_launcher_vault.png'):
        shutil.copyfile(dst, p)

manifest = ROOT / 'app/src/main/AndroidManifest.xml'
if manifest.exists():
    s = read(manifest)
    s = re.sub(r'android:icon="@[^"]+"', 'android:icon="@drawable/elitestocks_tv_logo"', s)
    s = re.sub(r'android:roundIcon="@[^"]+"', 'android:roundIcon="@drawable/elitestocks_tv_logo"', s)
    write(manifest, s)

adaptive = ROOT / 'app/src/main/res/mipmap-anydpi-v26/ic_launcher_vault.xml'
if adaptive.exists():
    write(adaptive, '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@android:color/black"/>
    <foreground android:drawable="@drawable/elitestocks_tv_logo"/>
</adaptive-icon>
''')

p = ROOT / 'app/src/debug/res/values/strings.xml'
if p.exists():
    write(p, read(p).replace('EliteStocks TV Debug', 'EliteStocks TV'))
p = ROOT / 'app/build.gradle.kts'
write(p, read(p).replace('            versionNameSuffix = "-debug"\n', ''))

# PlayerControlsChrome already contains the intended PlayerModernVodInfo call in source.
# Do not use replace_call here: its first match is the PlayerVodInfo declaration itself,
# which would turn a valid Kotlin function declaration into invalid call syntax.

p = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/provider/ProviderSetupScreen.kt'
s = read(p)
start = s.find('@Composable\nprivate fun SourceTypeSelectorPanel(')
end = s.find('@Composable\nprivate fun SourceTypeCard', start)
if start >= 0 and end > start:
    panel = '''@Composable
private fun SourceTypeSelectorPanel(
    sourceType: SourceType,
    isEditing: Boolean,
    isEditLabel: String,
    onSelect: (SourceType) -> Unit,
    onImportClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(modifier = modifier, shape = RoundedCornerShape(20.dp), colors = SurfaceDefaults.colors(containerColor = Surface.copy(alpha = 0.92f))) {
        Column(modifier = Modifier.fillMaxSize().padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(text = isEditLabel, style = MaterialTheme.typography.titleMedium, color = TextPrimary)
            Text(text = stringResource(R.string.setup_shell_subtitle), style = MaterialTheme.typography.bodySmall, color = OnSurfaceDim)
            Text(text = stringResource(R.string.setup_source_type_label), style = MaterialTheme.typography.labelSmall, color = TextTertiary)
            if (!isEditing || sourceType == SourceType.XTREAM) {
                SourceTypeCard(title = stringResource(R.string.setup_xtream), subtitle = stringResource(R.string.setup_info_xtream_body), selected = sourceType == SourceType.XTREAM, enabled = !isEditing, onClick = { onSelect(SourceType.XTREAM) })
            }
            if (!isEditing || sourceType == SourceType.M3U_URL) {
                SourceTypeCard(title = stringResource(R.string.setup_tab_url), subtitle = stringResource(R.string.setup_info_m3u_body), selected = sourceType == SourceType.M3U_URL, enabled = !isEditing, onClick = { onSelect(SourceType.M3U_URL) })
            }
            if (!isEditing) {
                ImportOptionsButton(text = stringResource(R.string.settings_restore_data), onClick = onImportClick, compact = true, modifier = Modifier.fillMaxWidth())
            }
            Spacer(modifier = Modifier.weight(1f))
            Text(text = stringResource(R.string.setup_info_manage_title), style = MaterialTheme.typography.bodySmall, color = OnSurfaceDim)
            Text(text = stringResource(R.string.setup_info_manage_body), style = MaterialTheme.typography.bodySmall, color = OnSurfaceDim.copy(alpha = 0.55f))
        }
    }
}

'''
    s = s[:start] + panel + s[end:]
start = s.find('@Composable\nprivate fun SourceTypeTabRow(')
end = s.find('// ??? ProviderTextField', start)
if start >= 0 and end > start:
    tabs = '''@Composable
private fun SourceTypeTabRow(
    sourceType: SourceType,
    isEditing: Boolean,
    onSelect: (SourceType) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(modifier = modifier, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        if (!isEditing || sourceType == SourceType.XTREAM) {
            TabButton(text = stringResource(R.string.setup_xtream), isSelected = sourceType == SourceType.XTREAM, onClick = { if (!isEditing) onSelect(SourceType.XTREAM) })
        }
        if (!isEditing || sourceType == SourceType.M3U_URL) {
            TabButton(text = stringResource(R.string.setup_tab_url), isSelected = sourceType == SourceType.M3U_URL, onClick = { if (!isEditing) onSelect(SourceType.M3U_URL) })
        }
    }
}

'''
    s = s[:start] + tabs + s[end:]
write(p, s)

p = ROOT / 'app/src/main/java/com/streamvault/app/ui/components/shell/AppShell.kt'
s = read(p)
s = s.replace('AppTopLevelDestination.defaultOrder.map { it.toDestinationItem() }', 'AppTopLevelDestination.defaultOrder.filterNot { it == AppTopLevelDestination.GUIDE || it == AppTopLevelDestination.PLUGINS }.map { it.toDestinationItem() }')
s = s.replace('configured.map { it.toDestinationItem() }', 'configured.filterNot { it == AppTopLevelDestination.GUIDE || it == AppTopLevelDestination.PLUGINS }.map { it.toDestinationItem() }')
write(p, s)

p = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/settings/SettingsBackupAboutSections.kt'
s = read(p)
start = s.find('internal fun LazyListScope.settingsAboutSection(')
if start >= 0:
    s = s[:start] + '''internal fun LazyListScope.settingsAboutSection(
    uiState: SettingsUiState,
    context: Context,
    buildVerificationLabel: String,
    onOpenUri: (String) -> Unit,
    onCheckForUpdates: () -> Unit,
    onInstallDownloadedUpdate: () -> Unit,
    onDownloadLatestUpdate: () -> Unit,
    onSetAutoCheckAppUpdates: (Boolean) -> Unit,
    onSetAutoDownloadAppUpdates: (Boolean) -> Unit,
    onRefreshDownloadState: () -> Unit,
    onViewCrashReport: () -> Unit,
    onShareCrashReport: () -> Unit,
    onDeleteCrashReport: () -> Unit
) {
    item {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
            SettingsSectionHeader(title = stringResource(R.string.settings_about), subtitle = "EliteStocks TV")
            SettingsRow(label = stringResource(R.string.settings_app_version), value = "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
            SettingsRow(label = stringResource(R.string.settings_developed_by), value = "EliteStocks")
        }
    }
}
'''
write(p, s)

p = ROOT / 'app/src/main/java/com/streamvault/app/StartupWorkRegistry.kt'
s = read(p).replace('import com.streamvault.app.update.AppUpdateCheckWorker\n', '')
s = s.replace('        AppUpdateCheckWorker.enqueue(context)', '        WorkManager.getInstance(context).cancelUniqueWork("app-update-check")')
write(p, s)

p = ROOT / 'app/src/main/java/com/streamvault/app/StreamVaultApp.kt'
s = read(p).replace('import com.streamvault.app.diagnostics.CrashReportStore\n', '').replace('        CrashReportStore.install(this)\n', '').replace('.crossfade(!isReducedMotionEnabled(context))', '.crossfade(false)')
write(p, s)
p = ROOT / 'app/src/main/java/com/streamvault/app/MainActivity.kt'
s = read(p).replace('import com.streamvault.app.diagnostics.CrashReportStore\n', '')
s = re.sub(r'\n    private fun shareLatestFailureReport\(\) \{.*?\n    \}\n', '\n', s, flags=re.S)
s = s.replace('                            onShareReport = ::shareLatestFailureReport\n', '').replace('    onShareReport: () -> Unit = {}\n', '')
s = re.sub(r'\n\s*Button\(onClick = onShareReport\) \{ Text\("Share report"\) \}', '', s)
write(p, s)

p = ROOT / 'app/build.gradle.kts'
write(p, read(p).replace('    debugImplementation(libs.leakcanary.android)\n', ''))
p = ROOT / 'gradle/libs.versions.toml'
s = read(p)
s = re.sub(r'leakcanary = "[^"]+"\n', '', s)
s = re.sub(r'leakcanary-android = \{[^\n]+\}\n', '', s)
write(p, s)

p = ROOT / 'app/src/main/java/com/streamvault/app/ui/screens/settings/SettingsScreen.kt'
s = read(p).replace('import com.streamvault.app.diagnostics.CrashReportStore\n', '')
s = re.sub(r'\n    fun shareCrashReport\(\) \{.*?\n    \}\n', '\n', s, flags=re.S)
s = s.replace('onViewCrashReport = viewModel::viewCrashReport,', 'onViewCrashReport = {},')
s = s.replace('onShareCrashReport = ::shareCrashReport,', 'onShareCrashReport = {},')
s = s.replace('onDeleteCrashReport = viewModel::deleteCrashReport,', 'onDeleteCrashReport = {},')
write(p, s)

p = ROOT / 'app/src/main/res/values/strings.xml'
s = read(p)
s = re.sub(r'<string name="settings_developer_name">.*?</string>', '<string name="settings_developer_name">EliteStocks</string>', s)
write(p, s)
