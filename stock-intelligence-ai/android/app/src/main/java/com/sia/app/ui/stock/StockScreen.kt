package com.sia.app.ui.stock

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sia.app.core.UiState
import com.sia.app.data.remote.dto.AnalysisDto
import com.sia.app.data.remote.dto.IndicatorsDto
import com.sia.app.data.remote.dto.SignalDto
import com.sia.app.ui.components.ConfidenceBar
import com.sia.app.ui.components.DisclaimerBanner
import com.sia.app.ui.components.SectionHeader
import com.sia.app.ui.components.SignalBadge
import com.sia.app.ui.components.StatCard
import com.sia.app.ui.theme.Bear
import com.sia.app.ui.theme.Bull
import com.sia.app.ui.theme.Surface
import com.sia.app.ui.theme.TextPrimary
import com.sia.app.ui.theme.TextSecondary
import com.sia.app.ui.theme.signalColors

@Composable
fun StockScreen(symbol: String, onBack: () -> Unit, vm: StockViewModel = hiltViewModel()) {
    LaunchedEffect(symbol) { vm.load(symbol) }
    val state by vm.state.collectAsStateWithLifecycle()

    LazyColumn(
        Modifier.fillMaxSize().padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 6.dp)) {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = TextSecondary)
                }
                Text(symbol, color = TextPrimary, fontSize = 20.sp, fontWeight = FontWeight.Medium)
                Text("  NSE", color = TextSecondary, fontSize = 12.sp)
            }
        }

        when (val s = state) {
            is UiState.Loading -> item {
                Row(Modifier.fillMaxWidth().padding(32.dp), horizontalArrangement = Arrangement.Center) {
                    CircularProgressIndicator()
                }
            }
            is UiState.Error -> item {
                Text(s.message, color = Bear, fontSize = 13.sp, modifier = Modifier.padding(12.dp))
            }
            is UiState.Success -> content(s.data)
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.content(dto: AnalysisDto) {
    val sig = dto.signal
    val ind = dto.indicators

    if (sig != null) item { RecommendationCard(sig) }

    if (!sig?.reasons.isNullOrEmpty()) {
        item { SectionHeader("Why this signal?") }
        item { ReasonsCard(sig!!.reasons!!) }
    }

    if (ind != null) {
        item { SectionHeader("Technicals") }
        item { TechnicalsGrid(ind) }
    }

    dto.dataTimestamp?.let { ts ->
        item {
            Text("Data as of $ts · source ${dto.dataSource ?: "—"}",
                color = TextSecondary, fontSize = 10.sp, modifier = Modifier.padding(top = 8.dp))
        }
    }

    item {
        DisclaimerBanner(
            dto.disclaimer ?: "AI analysis for research only. Not investment advice.",
            Modifier.padding(vertical = 12.dp)
        )
    }
}

@Composable
private fun RecommendationCard(sig: SignalDto) {
    val (accent, _) = signalColors(sig.label ?: "HOLD")
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(Surface)
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            SignalBadge(sig.label ?: "HOLD")
            Text("Confidence ${sig.confidence?.toInt() ?: 0}%", color = TextSecondary, fontSize = 11.sp)
        }
        ConfidenceBar(sig.confidence ?: 0.0, accent)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Level("Entry", sig.entryPrice, TextPrimary)
            Level("Target", sig.target1, Bull)
            Level("Stop", sig.stopLoss, Bear)
            Level("R:R", sig.riskReward, TextPrimary, isRatio = true)
        }
    }
}

@Composable
private fun Level(label: String, value: Double?, color: androidx.compose.ui.graphics.Color, isRatio: Boolean = false) {
    Column {
        Text(label, color = TextSecondary, fontSize = 10.sp)
        val text = when {
            value == null -> "—"
            isRatio -> "1:%.1f".format(value)
            else -> "₹%,.0f".format(value)
        }
        Text(text, color = color, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun ReasonsCard(reasons: List<String>) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Surface)
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        reasons.forEach { r ->
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Check, contentDescription = null, tint = Bull,
                    modifier = Modifier.padding(end = 6.dp))
                Text(r, color = TextPrimary, fontSize = 12.sp)
            }
        }
    }
}

@Composable
private fun TechnicalsGrid(ind: IndicatorsDto) {
    val trendColor = when (ind.trend?.uppercase()) {
        "UP" -> Bull; "DOWN" -> Bear; else -> TextPrimary
    }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatCard("RSI", ind.rsi?.let { "%.1f".format(it) } ?: "—", TextPrimary, Modifier.weight(1f))
            StatCard("Trend", ind.trend ?: "—", trendColor, Modifier.weight(1f))
            StatCard("VWAP", ind.vwap?.let { "%,.0f".format(it) } ?: "—", TextPrimary, Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatCard("EMA 20", ind.ema20?.let { "%,.0f".format(it) } ?: "—", TextPrimary, Modifier.weight(1f))
            StatCard("EMA 50", ind.ema50?.let { "%,.0f".format(it) } ?: "—", TextPrimary, Modifier.weight(1f))
            StatCard("EMA 200", ind.ema200?.let { "%,.0f".format(it) } ?: "—", TextPrimary, Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatCard("Support", ind.support?.let { "%,.0f".format(it) } ?: "—", Bull, Modifier.weight(1f))
            StatCard("Resistance", ind.resistance?.let { "%,.0f".format(it) } ?: "—", Bear, Modifier.weight(1f))
            StatCard("MACD", ind.macd?.let { "%.2f".format(it) } ?: "—", TextPrimary, Modifier.weight(1f))
        }
    }
}
