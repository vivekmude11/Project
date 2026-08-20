package com.sia.app.data.remote.dto

import com.google.gson.annotations.SerializedName

// GET /stock/{symbol}/analysis
data class AnalysisDto(
    val symbol: String?,
    val exchange: String?,
    val indicators: IndicatorsDto?,
    val signal: SignalDto?,
    @SerializedName("data_source") val dataSource: String?,
    @SerializedName("data_timestamp") val dataTimestamp: String?,
    val disclaimer: String?,
    val error: String?,
)

data class IndicatorsDto(
    val price: Double?,
    val ema20: Double?,
    val ema50: Double?,
    val ema200: Double?,
    val rsi: Double?,
    val macd: Double?,
    @SerializedName("macd_signal") val macdSignal: Double?,
    @SerializedName("bb_upper") val bbUpper: Double?,
    @SerializedName("bb_lower") val bbLower: Double?,
    val vwap: Double?,
    val support: Double?,
    val resistance: Double?,
    val atr: Double?,
    val trend: String?,
)

data class SignalDto(
    val label: String?,
    @SerializedName("final_score") val finalScore: Double?,
    val confidence: Double?,
    val subscores: Map<String, Double>?,
    val reasons: List<String>?,
    @SerializedName("entry_price") val entryPrice: Double?,
    val target1: Double?,
    val target2: Double?,
    @SerializedName("stop_loss") val stopLoss: Double?,
    @SerializedName("risk_reward") val riskReward: Double?,
    @SerializedName("weights_version") val weightsVersion: String?,
    @SerializedName("model_version") val modelVersion: String?,
)

// GET /stock/{symbol}
data class StockSummaryDto(
    val symbol: String?,
    val exchange: String?,
    val price: Double?,
    val label: String?,
    val confidence: Double?,
    @SerializedName("data_timestamp") val dataTimestamp: String?,
    val disclaimer: String?,
)
