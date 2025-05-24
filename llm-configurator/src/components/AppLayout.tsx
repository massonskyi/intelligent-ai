import React, { Suspense } from "react";
import { Box, AppBar, Toolbar, Typography, IconButton, CircularProgress, useTheme, useMediaQuery } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import Sidebar from "./Sidebar";
import Footer from "./Footer";

interface Props {
  children: React.ReactNode;
}

const AppLayout: React.FC<Props> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const [sidebarOpen, setSidebarOpen] = React.useState(!isMobile);

  React.useEffect(() => {
    setSidebarOpen(!isMobile);
  }, [isMobile]);

  return (
    <Box display="flex" flexDirection="column" minHeight="100vh" bgcolor="background.default">
      {/* AppBar */}
      <AppBar
        position="static"
        color="primary"
        elevation={3}
        sx={{ borderRadius: 0, mb: 1 }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton edge="start" color="inherit" onClick={() => setSidebarOpen(o => !o)} aria-label="menu" sx={{ mr: 2 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            LLM Configurator
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Layout: Sidebar + Content */}
      <Box display="flex" flex={1} minHeight={0} bgcolor="background.default">
        {/* Sidebar (Permanent/Drawer for mobile) */}
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} mobile={isMobile} />

        {/* Main content */}
        <Box flex={1} p={isMobile ? 1 : 3} minHeight={0} overflow="auto" bgcolor="background.default">
          <Suspense fallback={
            <Box display="flex" justifyContent="center" alignItems="center" height="80vh">
              <CircularProgress />
            </Box>
          }>
            {children}
          </Suspense>
        </Box>
      </Box>

      {/* Footer */}
      <Footer />
    </Box>
  );
};

export default AppLayout;
