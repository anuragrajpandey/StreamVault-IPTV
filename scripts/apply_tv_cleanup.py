from pathlib import Path
import re, shutil

ROOT=Path('.')
APP=ROOT/'app/src/main/java/com/streamvault/app'

# Entirely TV-irrelevant feature packages/services.
for rel in [
    'cast', 'backup', 'ui/screens/downloads', 'service/DownloadForegroundService.kt',
]:
    p=APP/rel
    if p.is_dir(): shutil.rmtree(p)
    elif p.exists(): p.unlink()

# Remove exact feature imports and obvious single-line declarations/references.
patterns=[
 r'^import com\.streamvault\.app\.cast\..*\n',
 r'^import com\.streamvault\.app\.backup\..*\n',
 r'^import com\.streamvault\.app\.service\.DownloadForegroundService\n',
 r'^import com\.streamvault\.domain\.model\.Download.*\n',
 r'^import com\.streamvault\.domain\.repository\.DownloadManager\n',
]
for p in ROOT.glob('app/src/main/**/*.kt'):
    s=p.read_text()
    old=s
    for pat in patterns: s=re.sub(pat,'',s,flags=re.M)
    if s!=old: p.write_text(s)

# Navigation: remove Downloads destination and backup URI from settings route.
p=APP/'navigation/AppNavigation.kt'
s=p.read_text()
s=re.sub(r'^import .*DownloadsScreen.*\n','',s,flags=re.M)
s=s.replace('    const val DOWNLOADS = "downloads"\n','')
s=s.replace('    const val SETTINGS_DESTINATION = "settings?backupUri={backupUri}"','    const val SETTINGS_DESTINATION = "settings"')
s=re.sub(r'fun settings\(backupUri: String\? = null\) = Routes\.SETTINGS_DESTINATION\.replace\("\{backupUri\}", Uri\.encode\(backupUri\)\)','fun settings() = Routes.SETTINGS_DESTINATION',s)
s=s.replace('            AppLandingDestination.DOWNLOADS -> Routes.DOWNLOADS\n','')
s=s.replace('            AppTopLevelDestination.DOWNLOADS -> Routes.DOWNLOADS\n','')
p.write_text(s)

# Manifest cleanup.
p=ROOT/'app/src/main/AndroidManifest.xml'
s=p.read_text()
s=re.sub(r'^\s*android:supportsPictureInPicture="true"\s*\n','',s,flags=re.M)
s=re.sub(r'^\s*<activity[^>]*CastRouteChooserActivity[^>]*/>\s*\n','',s,flags=re.M)
s=re.sub(r'^\s*<service[^>]*DownloadForegroundService[^>]*/>\s*\n','',s,flags=re.M)
s=re.sub(r'^\s*<meta-data[^>]*CAST\.framework\.OPTIONS_PROVIDER_CLASS_NAME[^>]*/>\s*\n','',s,flags=re.M)
p.write_text(s)

# Remove dedicated Cast/Recording/PiP state imports and declarations from player sources.
for p in (APP/'ui/screens/player').rglob('*.kt'):
    s=p.read_text(); old=s
    for name in ['PlayerCastCoordinator','PlayerRecordingCoordinator','CastConnectionState','CastPlaybackReportMode','RecordingItem','RecordingRecurrence','RecordingStatus']:
        s=re.sub(r'^import .*'+re.escape(name)+r'.*\n','',s,flags=re.M)
    s=re.sub(r'^\s*(private\s+)?(val|var)\s+\w*(cast|Cast|recording|Recording|pictureInPicture|PictureInPicture)\w*\s*=.*\n','',s,flags=re.M)
    if s!=old: p.write_text(s)

# Remove Cast dependencies/references from Gradle. This includes version-catalog aliases
# and the Kotlin DSL accessor that caused the previous compile failure.
for p in [ROOT/'app/build.gradle.kts', ROOT/'build.gradle.kts', ROOT/'gradle/libs.versions.toml']:
    if not p.exists(): continue
    s=p.read_text(); old=s
    s=re.sub(r'^.*com\.google\.android\.gms:play-services-cast-framework.*\n','',s,flags=re.M)
    s=re.sub(r'^.*play-services-cast.*\n','',s,flags=re.M)
    s=re.sub(r'^.*libs\.play\.services\.cast\.framework.*\n','',s,flags=re.M)
    if s!=old: p.write_text(s)

# Remove internal audit artifact from final branch.
audit=ROOT/'feature-audit.txt'
if audit.exists(): audit.unlink()
