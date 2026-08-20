package com.sia.app.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sia.app.core.UiState
import com.sia.app.data.remote.dto.StockSummaryDto
import com.sia.app.data.repo.StockRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

private val DEFAULT_SYMBOLS = listOf("RELIANCE", "TATAMOTORS", "HDFCBANK", "INFY", "SBIN")

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repo: StockRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<UiState<List<StockSummaryDto>>>(UiState.Loading)
    val state: StateFlow<UiState<List<StockSummaryDto>>> = _state.asStateFlow()

    init { load() }

    fun load() {
        _state.value = UiState.Loading
        viewModelScope.launch {
            val results = DEFAULT_SYMBOLS.map { sym ->
                async { repo.summary(sym).getOrNull() }
            }.awaitAll().filterNotNull()

            _state.value = if (results.isEmpty())
                UiState.Error("Couldn't reach the backend. Is it running at the configured URL?")
            else UiState.Success(results)
        }
    }
}
