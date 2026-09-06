package com.streamvault.app.ui.screens.player.overlay

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusProperties
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.SurfaceDefaults
import androidx.tv.material3.Text
import com.streamvault.app.R
import com.streamvault.app.ui.interaction.TvClickableSurface
import com.streamvault.app.ui.theme.Primary
import com.streamvault.app.ui.screens.player.SeekPreviewState

@Composable
fun PlayerModernVodInfo(
    title: String,
    contentType: String,
    isPlaying: Boolean,
    currentPosition: Long,
    duration: Long,
    aspectRatioLabel: String,
    subtitleTrackCount: Int,
    audioTrackCount: Int,
    videoQualityCount: Int,
    isMuted: Boolean,
    playbackSpeed: Float,
    sleepTimerUiState: com.streamvault.app.ui.screens.player.SleepTimerUiState,
    audioVideoSyncEnabled: Boolean,
    playButtonFocusRequester: FocusRequester,
    quickActionsFocusRequester: FocusRequester,
    onSeekToPosition: (Long) -> Unit,
    onSetScrubbingMode: (Boolean) -> Unit,
    onToggleAspectRatio: () -> Unit,
    onOpenSubtitleTracks: () -> Unit,
    onOpenAudioTracks: () -> Unit,
    onOpenVideoTracks: () -> Unit,
    onOpenPlaybackSpeed: () -> Unit,
    onOpenStopPlaybackTimer: () -> Unit,
    onOpenIdleStandbyTimer: () -> Unit,
    onOpenAudioVideoSync: () -> Unit,
    showEpisodesAction: Boolean,
    onOpenEpisodes: () -> Unit,
    showNextEpisodeAction: Boolean,
    onPlayNextEpisode: () -> Unit,
    onEnterPictureInPicture: () -> Unit,
    onToggleMute: () -> Unit,
    isCastConnected: Boolean,
    onCast: () -> Unit,
    onStopCasting: () -> Unit,
    onTogglePlayPause: () -> Unit,
    onSeekBackward: () -> Unit,
    onSeekForward: () -> Unit,
    seekPreview: SeekPreviewState,
    onSeekPreviewPositionChanged: (Long?) -> Unit,
    showExternalPlayerAction: Boolean,
    onOpenExternalPlayer: () -> Unit
) {
    var sliderValue by remember(duration, currentPosition) {
        mutableStateOf(if (duration > 0) currentPosition.toFloat() / duration.toFloat() else 0f)
    }
    var scrubbing by remember { mutableStateOf(false) }
    val latestSeek by rememberUpdatedState(onSeekToPosition)
    val latestScrub by rememberUpdatedState(onSetScrubbingMode)
    val latestPreview by rememberUpdatedState(onSeekPreviewPositionChanged)

    LaunchedEffect(duration, currentPosition, scrubbing) {
        if (!scrubbing) sliderValue = if (duration > 0) currentPosition.toFloat() / duration.toFloat() else 0f
    }

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            PlayerMetaPill(
                text = if (contentType == "MOVIE") stringResource(R.string.player_type_movie)
                else stringResource(R.string.player_type_series),
                accent = true
            )
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = androidx.compose.ui.graphics.Color.White,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1
            )
        }

        Surface(
            shape = RoundedCornerShape(18.dp),
            colors = SurfaceDefaults.colors(containerColor = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.055f))
        ) {
            Column(modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp)) {
                if (seekPreview.visible) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = formatDurationModern(seekPreview.positionMs),
                            style = MaterialTheme.typography.labelLarge,
                            color = androidx.compose.ui.graphics.Color.White,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = seekPreview.title,
                            style = MaterialTheme.typography.labelMedium,
                            color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.65f),
                            maxLines = 1
                        )
                    }
                    Spacer(modifier = Modifier.size(8.dp))
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = formatDurationModern(if (scrubbing && duration > 0) (sliderValue * duration).toLong() else currentPosition),
                        style = MaterialTheme.typography.labelMedium,
                        color = androidx.compose.ui.graphics.Color.White
                    )
                    Slider(
                        value = sliderValue.coerceIn(0f, 1f),
                        onValueChange = { value ->
                            if (!scrubbing) {
                                scrubbing = true
                                latestScrub(true)
                            }
                            sliderValue = value.coerceIn(0f, 1f)
                            if (duration > 0) latestPreview((sliderValue * duration).toLong())
                        },
                        onValueChangeFinished = {
                            if (duration > 0) latestSeek((sliderValue.coerceIn(0f, 1f) * duration).toLong())
                            if (scrubbing) {
                                latestScrub(false)
                                scrubbing = false
                            }
                            latestPreview(null)
                        },
                        modifier = Modifier.weight(1f).padding(horizontal = 10.dp).semantics {
                            contentDescription = stringResource(R.string.player_playback_label)
                        },
                        enabled = duration > 0,
                        colors = SliderDefaults.colors(
                            activeTrackColor = Primary,
                            inactiveTrackColor = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.20f),
                            thumbColor = Primary
                        )
                    )
                    Text(
                        text = formatDurationModern(duration),
                        style = MaterialTheme.typography.labelMedium,
                        color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.75f)
                    )
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            PlayerModernTransportButton(
                icon = R.drawable.ic_replay_10,
                description = stringResource(R.string.player_rewind),
                onClick = onSeekBackward,
                modifier = Modifier.focusProperties { down = quickActionsFocusRequester }
            )
            TvClickableSurface(
                onClick = onTogglePlayPause,
                shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
                colors = ClickableSurfaceDefaults.colors(
                    containerColor = Primary.copy(alpha = 0.90f),
                    focusedContainerColor = Primary
                ),
                modifier = Modifier.size(64.dp).focusRequester(playButtonFocusRequester).focusProperties {
                    down = quickActionsFocusRequester
                }.semantics {
                    contentDescription = if (isPlaying) "Pause" else "Play"
                }
            ) {
                Icon(
                    imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                    contentDescription = null,
                    tint = androidx.compose.ui.graphics.Color.White,
                    modifier = Modifier.size(30.dp)
                )
            }
            PlayerModernTransportButton(
                icon = R.drawable.ic_forward_10,
                description = stringResource(R.string.player_forward),
                onClick = onSeekForward,
                modifier = Modifier.focusProperties { down = quickActionsFocusRequester }
            )
            if (showNextEpisodeAction) {
                TvClickableSurface(
                    onClick = onPlayNextEpisode,
                    shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.10f),
                        focusedContainerColor = Primary.copy(alpha = 0.92f)
                    ),
                    modifier = Modifier.focusProperties { down = quickActionsFocusRequester }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 11.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(7.dp)
                    ) {
                        Icon(Icons.Default.SkipNext, contentDescription = null, tint = androidx.compose.ui.graphics.Color.White, modifier = Modifier.size(22.dp))
                        Text("Next Episode", color = androidx.compose.ui.graphics.Color.White, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (showEpisodesAction) PlayerModernActionChip(stringResource(R.string.player_episodes), onOpenEpisodes, quickActionsFocusRequester)
            if (subtitleTrackCount > 0) PlayerModernActionChip(stringResource(R.string.player_subs), onOpenSubtitleTracks, quickActionsFocusRequester)
            if (audioTrackCount > 0) PlayerModernActionChip(stringResource(R.string.player_audio), onOpenAudioTracks, quickActionsFocusRequester)
            if (videoQualityCount > 0) PlayerModernActionChip(stringResource(R.string.player_video_quality), onOpenVideoTracks, quickActionsFocusRequester)
            PlayerModernActionChip(stringResource(R.string.player_playback_speed_value, formatPlaybackSpeedLabelModern(playbackSpeed)), onOpenPlaybackSpeed, quickActionsFocusRequester)
            PlayerModernActionChip(stringResource(if (isMuted) R.string.player_unmute else R.string.player_mute), onToggleMute, quickActionsFocusRequester)
            if (isCastConnected) PlayerModernActionChip(stringResource(R.string.player_stop_casting), onStopCasting, quickActionsFocusRequester)
            else PlayerModernActionChip(stringResource(R.string.player_cast), onCast, quickActionsFocusRequester)
        }
    }
}

@Composable
private fun PlayerModernTransportButton(
    icon: Int,
    description: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    TvClickableSurface(
        onClick = onClick,
        shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.10f),
            focusedContainerColor = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.28f)
        ),
        modifier = modifier.size(54.dp).semantics { contentDescription = description }
    ) {
        Icon(painterResource(icon), contentDescription = null, tint = androidx.compose.ui.graphics.Color.White, modifier = Modifier.size(28.dp))
    }
}

@Composable
private fun PlayerModernActionChip(
    label: String,
    onClick: () -> Unit,
    focusRequester: FocusRequester
) {
    TvClickableSurface(
        onClick = onClick,
        shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.075f),
            focusedContainerColor = Primary.copy(alpha = 0.86f)
        ),
        modifier = Modifier.focusProperties { down = focusRequester }
    ) {
        Text(label, color = androidx.compose.ui.graphics.Color.White, style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(horizontal = 13.dp, vertical = 8.dp))
    }
}

private fun formatPlaybackSpeedLabelModern(speed: Float): String = if (speed % 1f == 0f) "${speed.toInt()}x" else "${("%.2f".format(java.util.Locale.US, speed)).trimEnd('0').trimEnd('.')}x"

private fun formatDurationModern(ms: Long): String {
    val totalSeconds = ms.coerceAtLeast(0L) / 1000L
    val hours = totalSeconds / 3600L
    val minutes = (totalSeconds % 3600L) / 60L
    val seconds = totalSeconds % 60L
    return if (hours > 0L) String.format(java.util.Locale.getDefault(), "%02d:%02d:%02d", hours, minutes, seconds)
    else String.format(java.util.Locale.getDefault(), "%02d:%02d", minutes, seconds)
}
