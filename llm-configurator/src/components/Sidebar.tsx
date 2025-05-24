import React from "react";
import {
  Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Divider, Box, useTheme, useMediaQuery
} from "@mui/material";
import HomeIcon from "@mui/icons-material/PlayCircleFilled";
import SettingsIcon from "@mui/icons-material/Tune";
import ChatIcon from "@mui/icons-material/Chat";
import HistoryIcon from "@mui/icons-material/History";
import DashboardIcon from "@mui/icons-material/Dashboard";
import InfoIcon from "@mui/icons-material/InfoOutlined";
import ModelSelector from "./ModelSelector";
import { useNavigate, useLocation } from "react-router-dom";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  mobile: boolean;
}

const drawerWidth = 270;

// Добавлены новые пункты
const navItems = [
  { label: "Playground", path: "/", icon: <HomeIcon /> },
  { label: "Chat", path: "/chat", icon: <ChatIcon /> },
  { label: "History", path: "/history", icon: <HistoryIcon /> },
  { label: "Dashboard", path: "/dashboard", icon: <DashboardIcon /> }, // NEW
  { label: "Settings", path: "/settings", icon: <SettingsIcon /> },
  { label: "About", path: "/about", icon: <InfoIcon /> }, // NEW
];

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, mobile }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const content = (
    <Box display="flex" flexDirection="column" height="100%">
      {/* Модуль выбора модели */}
      <Box p={2} bgcolor="background.paper">
        <ModelSelector />
      </Box>
      <Divider />
      {/* Навигация */}
      <List>
        {navItems.map(item => (
          <ListItemButton
              key={item.label}
              selected={location.pathname === item.path}
              onClick={() => { navigate(item.path); if (mobile) onClose(); }}
              sx={{
                borderRadius: 3,
                m: 1,
                transition: "background 0.25s",
                ...(location.pathname === item.path && {
                  bgcolor: theme.palette.action.selected,
                  fontWeight: 600
                })
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      <Box flexGrow={1} />
      <Divider />
      {/* Credits / логотип/футер */}
      <Box p={2} textAlign="center" color="text.secondary" fontSize={13}>
        <span>
          <b>LLM Playground</b> · v1.0<br />
          <a href="https://github.com/massonskyi/intelligent-ai" target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "underline" }}>GitHub</a>
        </span>
      </Box>
    </Box>
  );

  // На мобильных используем временный Drawer, на desktop — постоянный
  return mobile ? (
    <Drawer
      variant="temporary"
      open={open}
      onClose={onClose}
      ModalProps={{ keepMounted: true }}
      sx={{
        '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' }
      }}
    >
      {content}
    </Drawer>
  ) : (
    <Drawer
      variant="permanent"
      open
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: 'border-box',
          background: theme.palette.background.paper,
          borderRight: `1px solid ${theme.palette.divider}`
        }
      }}
    >
      {content}
    </Drawer>
  );
};

export default Sidebar;
