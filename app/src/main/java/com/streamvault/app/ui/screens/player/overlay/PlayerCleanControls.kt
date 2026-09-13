package com.streamvault.app.ui.screens.player.overlay

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AspectRatio
import androidx.compose.material.icons.filled.AudioFile
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Forward10
import androidx.compose.material.icons.filled.HighQuality
import androidx.compose.material.icons.filled.MoreHoriz
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PictureInPictureAlt
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Replay10
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material.icons.filled.Subtitles
import androidx.compose.material.icons.filled.VolumeOff
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusProperties
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import com.streamvault.app.R
import androidx.tv.material3.Text
import com.streamvault.app.ui.interaction.TvClickableSurface
import com.streamvault.app.ui.screens.player.SeekPreviewState
import com.streamvault.app.ui.screens.player.SleepTimerUiState
import com.streamvault.app.ui.screens.player.PlayerTimeshiftUiState
import com.streamvault.app.ui.theme.Primary
import com.streamvault.domain.model.Channel
import com.streamvault.domain.model.Program
import java.util.Locale

private val ClearWhite = Color.White
private val Glass = Color.Black.copy(alpha = 0.34f)
private val GlassStrong = Color.Black.copy(alpha = 0.58f)
private val DockGlass = Color.Black.copy(alpha = 0.66f)
private val SecondaryDockGlass = Color.Black.copy(alpha = 0.52f)

@Composable
fun PlayerCleanControls(
    visible: Boolean,
    title: String,
    contentType: String,
    isCatchUpPlayback: Boolean,
    isPlaying: Boolean,
    currentProgram: Program?,
    currentChannel: Channel?,
    currentChannelName: String?,
    displayChannelNumber: Int,
    currentPosition: Long,
    duration: Long,
    aspectRatioLabel: String,
    subtitleTrackCount: Int,
    liveTranslationAvailable: Boolean,
    audioTrackCount: Int,
    videoQualityCount: Int,
    isMuted: Boolean,
    playbackSpeed: Float,
    mediaTitle: String?,
    sleepTimerUiState: SleepTimerUiState,
    timeshiftUiState: PlayerTimeshiftUiState,
    playButtonFocusRequester: FocusRequester,
    quickActionsFocusRequester: FocusRequester,
    onClose: () -> Unit,
    onTogglePlayPause: () -> Unit,
    onSeekBackward: () -> Unit,
    onSeekForward: () -> Unit,
    onRestartProgram: () -> Unit,
    onOpenArchive: () -> Unit,
    onStartRecording: () -> Unit,
    onStopRecording: () -> Unit,
    onScheduleRecording: () -> Unit,
    onScheduleDailyRecording: () -> Unit,
    onScheduleWeeklyRecording: () -> Unit,
    onToggleAspectRatio: () -> Unit,
    onOpenSubtitleTracks: () -> Unit,
    onOpenAudioTracks: () -> Unit,
    onOpenVideoTracks: () -> Unit,
    onOpenPlaybackSpeed: () -> Unit,
    onOpenStopPlaybackTimer: () -> Unit,
    onOpenIdleStandbyTimer: () -> Unit,
    onOpenAudioVideoSync: () -> Unit,
    audioVideoSyncEnabled: Boolean,
    showEpisodesAction: Boolean,
    onOpenEpisodes: () -> Unit,
    onOpenSplitScreen: () -> Unit,
    onEnterPictureInPicture: () -> Unit,
    onToggleMute: () -> Unit,
    isCastConnected: Boolean,
    onCast: () -> Unit,
    onStopCasting: () -> Unit,
    onSeekToLiveEdge: () -> Unit,
    onSeekToPosition: (Long) -> Unit,
    onSetScrubbingMode: (Boolean) -> Unit,
    showExternalPlayerAction: Boolean,
    onOpenExternalPlayer: () -> Unit,
    seekPreview: SeekPreviewState,
    onSeekPreviewPositionChanged: (Long?) -> Unit,
    onUserInteraction: () -> Unit,
    modifier: Modifier = Modifier
) {
    if (!visible) return

    var sliderValue by remember(duration, currentPosition) {
        mutableStateOf(if (duration > 0) currentPosition.toFloat() / duration else 0f)
    }
    var scrubbing by remember { mutableStateOf(false) }

    LaunchedEffect(duration, currentPosition, scrubbing) {
        if (!scrubbing) sliderValue = if (duration > 0) currentPosition.toFloat() / duration else 0f
    }

    val live = contentType == "LIVE"
    val hasProgress = duration > 0L
    val primaryControlSize = 52.dp
    val playControlSize = 68.dp

    Box(modifier = modifier.fillMaxSize().background(Color.Transparent)) {
        Box(
            modifier = Modifier
                .fillMaxHeight()
                .aspectRatio(16f / 9f, matchHeightConstraintsFirst = true)
                .align(Alignment.Center)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .align(Alignment.TopCenter)
                    .padding(horizontal = 32.dp, vertical = 24.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = title.ifBlank { mediaTitle.orEmpty() },
                        color = ClearWhite,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    if (live && !currentChannelName.isNullOrBlank()) {
                        Text(
                            text = if (displayChannelNumber > 0) "$displayChannelNumber  •  $currentChannelName" else currentChannelName,
                            color = ClearWhite.copy(alpha = 0.68f),
                            style = MaterialTheme.typography.bodySmall,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
                CleanIconButton(Icons.Default.Close, stringResource(R.string.settings_close_app), onClose)
            }

            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(horizontal = 32.dp, vertical = 22.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                if (seekPreview.visible) {
                    Text(
                        text = "${formatCleanDuration(seekPreview.positionMs)}  •  ${seekPreview.title}",
                        color = ClearWhite,
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.Medium,
                        modifier = Modifier.align(Alignment.CenterHorizontally)
                    )
                }

                if (hasProgress) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = formatCleanDuration(if (scrubbing) (sliderValue * duration).toLong() else currentPosition),
                            color = ClearWhite,
                            style = MaterialTheme.typography.labelSmall
                        )
                        Slider(
                            value = sliderValue.coerceIn(0f, 1f),
                            onValueChange = {
                                if (!scrubbing) {
                                    scrubbing = true
                                    onSetScrubbingMode(true)
                                }
                                sliderValue = it.coerceIn(0f, 1f)
                                onSeekPreviewPositionChanged((sliderValue * duration).toLong())
                            },
                            onValueChangeFinished = {
                                onSeekToPosition((sliderValue * duration).toLong())
                                onSetScrubbingMode(false)
                                onSeekPreviewPositionChanged(null)
                                scrubbing = false
                            },
                            modifier = Modifier
                                .weight(1f)
                                .padding(horizontal = 10.dp)
                                .semantics { contentDescription = "Playback position" },
                            colors = SliderDefaults.colors(
                                activeTrackColor = Primary,
                                inactiveTrackColor = ClearWhite.copy(alpha = 0.26f),
                                thumbColor = Primary
                            )
                        )
                        Text(
                            text = formatCleanDuration(duration),
                            color = ClearWhite.copy(alpha = 0.72f),
                            style = MaterialTheme.typography.labelSmall
                        )
                    }
                }

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(DockGlass, RoundedCornerShape(20.dp))
                        .padding(horizontal = 10.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    CleanIconButton(
                        if (isMuted) Icons.Default.VolumeOff else Icons.Default.VolumeUp,
                        if (isMuted) stringResource(R.string.player_unmute) else stringResource(R.string.player_mute),
                        onToggleMute,
                        primaryControlSize
                    )
                    CleanIconButton(
                        Icons.Default.Replay10,
                        stringResource(R.string.player_rewind),
                        onSeekBackward,
                        primaryControlSize,
                        focusDown = quickActionsFocusRequester
                    )
                    TvClickableSurface(
                        onClick = { onUserInteraction(); onTogglePlayPause() },
                        shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
                        colors = ClickableSurfaceDefaults.colors(
                            containerColor = Primary.copy(alpha = 0.92f),
                            focusedContainerColor = Primary
                        ),
                        modifier = Modifier
                            .size(playControlSize)
                            .focusRequester(playButtonFocusRequester)
                            .focusProperties { down = quickActionsFocusRequester }
                            .semantics { contentDescription = if (isPlaying) "Pause" else "Play" }
                    ) {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                                contentDescription = null,
                                tint = ClearWhite,
                                modifier = Modifier.size(34.dp)
                            )
                        }
                    }
                    CleanIconButton(
                        Icons.Default.Forward10,
                        stringResource(R.string.player_forward),
                        onSeekForward,
                        primaryControlSize,
                        focusDown = quickActionsFocusRequester
                    )
                    if (showEpisodesAction) {
                        CleanIconButton(Icons.Default.SkipNext, stringResource(R.string.player_episodes), onOpenEpisodes, primaryControlSize)
                    }

                    Spacer(Modifier.weight(1f))

                    if (subtitleTrackCount > 0 || liveTranslationAvailable) {
                        CleanIconButton(Icons.Default.Subtitles, stringResource(R.string.player_subs), onOpenSubtitleTracks, primaryControlSize)
                    }
                    if (audioTrackCount > 0) {
                        CleanIconButton(Icons.Default.AudioFile, stringResource(R.string.player_audio), onOpenAudioTracks, primaryControlSize)
                    }
                    if (videoQualityCount > 0) {
                        CleanIconButton(Icons.Default.HighQuality, stringResource(R.string.player_video_quality), onOpenVideoTracks, primaryControlSize)
                    }
                    CleanIconButton(Icons.Default.Settings, "Playback speed", onOpenPlaybackSpeed, primaryControlSize)
                    if (isCastConnected) {
                        CleanIconButton(Icons.Default.Cast, stringResource(R.string.player_stop_casting), onStopCasting, primaryControlSize)
                    } else {
                        CleanIconButton(Icons.Default.Cast, stringResource(R.string.player_cast), onCast, primaryControlSize)
                    }
                    CleanIconButton(Icons.Default.AspectRatio, aspectRatioLabel, onToggleAspectRatio, primaryControlSize)
                    CleanIconButton(Icons.Default.PictureInPictureAlt, "Picture in picture", onEnterPictureInPicture, primaryControlSize)
                }

                if (live || audioVideoSyncEnabled || showExternalPlayerAction || currentRecordingStatus != null) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(SecondaryDockGlass, RoundedCornerShape(18.dp))
                            .padding(horizontal = 10.dp, vertical = 6.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        if (live) {
                            CleanIconButton(Icons.Default.Replay10, stringResource(R.string.player_jump_to_live), onSeekToLiveEdge)
                            CleanIconButton(Icons.Default.Settings, stringResource(R.string.player_idle_standby_after), onOpenIdleStandbyTimer)
                            CleanIconButton(Icons.Default.Settings, "Audio/video sync", onOpenAudioVideoSync)
                            CleanIconButton(Icons.Default.Settings, stringResource(R.string.multiview_nav), onOpenSplitScreen)
                                CleanIconButton(Icons.Default.Settings, stringResource(R.string.player_stop_recording), onStopRecording)
                            } else {
                                CleanIconButton(Icons.Default.Settings, stringResource(R.string.player_record), onStartRecording)
                            }
                        } else {
                            CleanIconButton(Icons.Default.Settings, stringResource(R.string.player_idle_standby_after), onOpenIdleStandbyTimer)
                        }
                        if (audioVideoSyncEnabled && !live) {
                            CleanIconButton(Icons.Default.Settings, "Audio/video sync", onOpenAudioVideoSync)
                        }
                        if (showExternalPlayerAction) {
                            CleanIconButton(Icons.Default.MoreHoriz, stringResource(R.string.player_open_in_external_player), onOpenExternalPlayer)
                        }
                        if (live && timeshiftUiState.available) {
                            Text(
                                text = if (timeshiftUiState.canSeekToLive) stringResource(R.string.player_jump_to_live_short) else stringResource(R.string.player_live_ready),
                                color = ClearWhite.copy(alpha = 0.72f),
                                style = MaterialTheme.typography.labelSmall,
                                modifier = Modifier.padding(start = 4.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CleanIconButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    description: String,
    onClick: () -> Unit,
    size: androidx.compose.ui.unit.Dp = 46.dp,
    focusDown: FocusRequester? = null
) {
    TvClickableSurface(
        onClick = onClick,
        shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = Glass,
            focusedContainerColor = GlassStrong
        ),
        modifier = Modifier
            .size(size)
            .then(
                if (focusDown != null) Modifier.focusProperties { down = focusDown } else Modifier
            )
            .semantics { contentDescription = description }
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = ClearWhite,
                modifier = Modifier.size(size * 0.5f)
            )
        }
    }
}

private fun formatCleanDuration(ms: Long): String {
    val seconds = ms.coerceAtLeast(0L) / 1000L
    val h = seconds / 3600L
    val m = (seconds % 3600L) / 60L
    val s = seconds % 60L
    return if (h > 0) String.format(Locale.getDefault(), "%02d:%02d:%02d", h, m, s)
    else String.format(Locale.getDefault(), "%02d:%02d", m, s)
}
