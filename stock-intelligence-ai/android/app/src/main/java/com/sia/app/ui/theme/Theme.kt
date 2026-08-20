package com.sia.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val SiaDarkColors = darkColorScheme(
    primary = Teal,
    onPrimary = Bg,
    secondary = Violet,
    background = Bg,
    onBackground = TextPrimary,
    surface = Surface,
    onSurface = TextPrimary,
    surfaceVariant = SurfaceVariant,
    onSurfaceVariant = TextSecondary,
    outline = Border,
    error = Bear,
)

private val SiaTypography = Typography(
    titleLarge = TextStyle(fontSize = 20.sp, fontWeight = FontWeight.Medium, color = TextPrimary),
    titleMedium = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.Medium, color = TextPrimary),
    bodyMedium = TextStyle(fontSize = 14.sp, fontWeight = FontWeight.Normal, color = TextPrimary),
    bodySmall = TextStyle(fontSize = 12.sp, fontWeight = FontWeight.Normal, color = TextSecondary),
    labelSmall = TextStyle(fontSize = 11.sp, fontWeight = FontWeight.Normal, color = TextSecondary),
)

/** Map a signal label to its accent + tint background. */
fun signalColors(label: String): Pair<Color, Color> = when (label.uppercase()) {
    "STRONG_BUY", "BUY" -> Bull to BullBg
    "SELL", "STRONG_SELL", "AVOID" -> Bear to BearBg
    else -> Warn to WarnBg   // HOLD / unknown
}

@Composable
fun SiaTheme(content: @Composable () -> Unit) {
    // App is dark-only by design; ignore system setting.
    MaterialTheme(
        colorScheme = SiaDarkColors,
        typography = SiaTypography,
        content = content,
    )
}
