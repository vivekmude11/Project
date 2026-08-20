package com.sia.app.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CandlestickChart
import androidx.compose.material.icons.outlined.Explore
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.WorkOutline
import androidx.compose.material.icons.automirrored.outlined.Chat
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.currentBackStackEntryAsState
import com.sia.app.ui.theme.Surface
import com.sia.app.ui.theme.Teal
import com.sia.app.ui.theme.TextSecondary

enum class TopDest(val route: String, val label: String, val icon: ImageVector) {
    Home("home", "Home", Icons.Outlined.Home),
    Markets("markets", "Markets", Icons.Outlined.CandlestickChart),
    Discover("discover", "Discover", Icons.Outlined.Explore),
    Portfolio("portfolio", "Portfolio", Icons.Outlined.WorkOutline),
    Chat("chat", "AI Chat", Icons.AutoMirrored.Outlined.Chat),
}

object Routes {
    const val STOCK = "stock/{symbol}"
    fun stock(symbol: String) = "stock/$symbol"
}

@Composable
fun SiaBottomBar(nav: NavHostController) {
    val backStack by nav.currentBackStackEntryAsState()
    val current = backStack?.destination
    NavigationBar(containerColor = Surface) {
        TopDest.entries.forEach { dest ->
            val selected = current?.hierarchy?.any { it.route == dest.route } == true
            NavigationBarItem(
                selected = selected,
                onClick = {
                    nav.navigate(dest.route) {
                        popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                },
                icon = { Icon(dest.icon, contentDescription = dest.label) },
                label = { Text(dest.label) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = Teal,
                    selectedTextColor = Teal,
                    unselectedIconColor = TextSecondary,
                    unselectedTextColor = TextSecondary,
                    indicatorColor = Surface,
                )
            )
        }
    }
}
