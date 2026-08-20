package com.sia.app.ui.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
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
import com.sia.app.data.remote.dto.StockSummaryDto
import com.sia.app.ui.components.DisclaimerBanner
import com.sia.app.ui.components.SectionHeader
import com.sia.app.ui.components.SignalBadge
import com.sia.app.ui.components.StatCard
import com.sia.app.ui.theme.Bear
import com.sia.app.ui.theme.Bull
import com.sia.app.ui.theme.Surface
import com.sia.app.ui.theme.TextPrimary
import com.sia.app.ui.theme.TextSecondary
import com.sia.app.ui.theme.Warn

@Composable
fun HomeScreen(onOpenStock: (String) -> Unit, vm: HomeViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        item {
            Column(Modifier.padding(top = 12.dp)) {
                Text("Stock Intelligence AI", color = TextPrimary, fontSize = 20.sp, fontWeight = FontWeight.Medium)
                Text("AI research tool · not investment advice", color = TextSecondary, fontSize = 11.sp)
            }
        }

        // Sentiment gauges (illustrative until the market endpoints are wired)
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                SentimentTile("Global sentiment", 38, Bull, Modifier.weight(1f))
                SentimentTile("India sentiment", 12, Warn, Modifier.weight(1f))
            }
        }

        // Index cards
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatCard("NIFTY 50", "24,812  +0.6%", Bull, Modifier.weight(1f))
                StatCard("BANK NIFTY", "54,120  -0.3%", Bear, Modifier.weight(1f))
            }
        }

        item { SectionHeader("Top AI signals") }

        when (val s = state) {
            is UiState.Loading -> item {
                Row(Modifier.fillMaxWidth().padding(24.dp), horizontalArrangement = Arrangement.Center) {
                    CircularProgressIndicator()
                }
            }
            is UiState.Error -> item {
                Text(s.message, color = Bear, fontSize = 13.sp, modifier = Modifier.padding(8.dp))
            }
            is UiState.Success -> items(s.data) { stock ->
                SignalRow(stock, onClick = { stock.symbol?.let(onOpenStock) })
            }
        }

        item {
            DisclaimerBanner(
                "AI analysis for research only. Not investment advice. No guaranteed returns.",
                Modifier.padding(vertical = 12.dp)
            )
        }
    }
}

@Composable
private fun SentimentTile(label: String, score: Int, color: androidx.compose.ui.graphics.Color, modifier: Modifier) {
    Column(
        modifier
            .clip(RoundedCornerShape(12.dp))
            .background(Surface)
            .padding(12.dp)
    ) {
        Text(label, color = TextSecondary, fontSize = 10.sp)
        Text((if (score >= 0) "+" else "") + score, color = color, fontSize = 20.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun SignalRow(stock: StockSummaryDto, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Surface)
            .clickable(onClick = onClick)
            .padding(12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column {
            Text(stock.symbol ?: "—", color = TextPrimary, fontSize = 14.sp, fontWeight = FontWeight.Medium)
            val price = stock.price?.let { "₹%,.2f".format(it) } ?: "—"
            val conf = stock.confidence?.let { " · conf ${it.toInt()}%" } ?: ""
            Text("$price$conf", color = TextSecondary, fontSize = 11.sp)
        }
        SignalBadge(stock.label ?: "HOLD")
    }
}
