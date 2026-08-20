package com.sia.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sia.app.ui.theme.Border
import com.sia.app.ui.theme.Surface
import com.sia.app.ui.theme.TextSecondary
import com.sia.app.ui.theme.Warn
import com.sia.app.ui.theme.WarnBg
import com.sia.app.ui.theme.signalColors

@Composable
fun SignalBadge(label: String, modifier: Modifier = Modifier) {
    val (fg, bg) = signalColors(label)
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(bg)
            .padding(horizontal = 12.dp, vertical = 5.dp)
    ) {
        Text(label.replace('_', ' '), color = fg, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun ConfidenceBar(confidence: Double, accent: androidx.compose.ui.graphics.Color, modifier: Modifier = Modifier) {
    val frac = (confidence / 100.0).coerceIn(0.0, 1.0).toFloat()
    Box(
        modifier
            .fillMaxWidth()
            .height(6.dp)
            .clip(RoundedCornerShape(3.dp))
            .background(Border)
    ) {
        Box(
            Modifier
                .fillMaxWidth(frac)
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp))
                .background(accent)
        )
    }
}

@Composable
fun StatCard(label: String, value: String, valueColor: androidx.compose.ui.graphics.Color, modifier: Modifier = Modifier) {
    Column(
        modifier
            .clip(RoundedCornerShape(10.dp))
            .background(Surface)
            .padding(10.dp)
    ) {
        Text(label, color = TextSecondary, fontSize = 10.sp)
        Text(value, color = valueColor, fontSize = 14.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun SectionHeader(text: String) {
    Text(text, color = TextSecondary, fontSize = 12.sp, modifier = Modifier.padding(top = 12.dp, bottom = 6.dp))
}

@Composable
fun DisclaimerBanner(text: String, modifier: Modifier = Modifier) {
    Row(
        modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(WarnBg)
            .padding(10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Text(text, color = Warn, fontSize = 11.sp)
    }
}
