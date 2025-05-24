import React, { useState, useMemo } from "react";
import { ThemeProvider, createTheme, CssBaseline, useMediaQuery } from "@mui/material";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";
import SettingsPage from "./pages/SettingsPage";
import PlaygroundPage from "./pages/PlaygroundPage";
import HistoryPage from "./pages/HistoryPage";
import AppLayout from "./components/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import AboutPage from "./pages/AboutPage";

// Optional: реализуй механизм выбора темы через контекст/глобальное состояние
const getDefaultTheme = () => {
  const prefersDark = window.matchMedia("(prefers-color-scheme: light)").matches;
  return prefersDark ? "dark" : "light";
};

export const ColorModeContext = React.createContext({
  mode: getDefaultTheme(),
  toggleMode: () => {}
});

export default function App() {
  const [mode, setMode] = useState<"light" | "dark">(getDefaultTheme());
  const colorMode = useMemo(() => ({
    mode,
    toggleMode: () => setMode((prev) => (prev === "light" ? "dark" : "light"))
  }), [mode]);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: "#6750A4" },
          secondary: { main: "#03DAC6" }
        },
        shape: { borderRadius: 16 },
        components: {
          MuiPaper: { styleOverrides: { rounded: { borderRadius: 16 } } },
          MuiButton: { styleOverrides: { root: { borderRadius: 12 } } }
        }
      }),
    [mode]
  );

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <AppLayout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/playground" element={<PlaygroundPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="*" element={<HomePage />} />
            </Routes>
          </AppLayout>
        </Router>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}
