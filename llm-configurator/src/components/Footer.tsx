import { Box, Typography } from "@mui/material";

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        p: 1,
        bgcolor: "background.paper",
        borderTop: 1,
        borderColor: "divider",
        textAlign: "center"
      }}
    >
      <Typography variant="caption" color="text.secondary">
        © {new Date().getFullYear()} LLM Configurator · Powered by Material Design 3
      </Typography>
    </Box>
  );
}
