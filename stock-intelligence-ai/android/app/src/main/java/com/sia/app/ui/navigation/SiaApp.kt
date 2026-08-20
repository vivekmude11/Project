package com.sia.app.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.sia.app.ui.chat.ChatScreen
import com.sia.app.ui.discover.DiscoverScreen
import com.sia.app.ui.home.HomeScreen
import com.sia.app.ui.markets.MarketsScreen
import com.sia.app.ui.portfolio.PortfolioScreen
import com.sia.app.ui.stock.StockScreen

@Composable
fun SiaApp() {
    val nav = rememberNavController()
    Scaffold(bottomBar = { SiaBottomBar(nav) }) { padding ->
        NavHost(
            navController = nav,
            startDestination = TopDest.Home.route,
            modifier = Modifier.padding(padding)
        ) {
            composable(TopDest.Home.route) {
                HomeScreen(onOpenStock = { nav.navigate(Routes.stock(it)) })
            }
            composable(TopDest.Markets.route) { MarketsScreen() }
            composable(TopDest.Discover.route) { DiscoverScreen() }
            composable(TopDest.Portfolio.route) { PortfolioScreen() }
            composable(TopDest.Chat.route) { ChatScreen() }

            composable(
                route = Routes.STOCK,
                arguments = listOf(navArgument("symbol") { type = NavType.StringType })
            ) { entry ->
                val symbol = entry.arguments?.getString("symbol").orEmpty()
                StockScreen(symbol = symbol, onBack = { nav.popBackStack() })
            }
        }
    }
}
