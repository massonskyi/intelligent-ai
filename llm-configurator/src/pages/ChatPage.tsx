import React from "react";
import { Box, Typography, Paper } from "@mui/material";
import ChatMode from "../components/ChatMode";

export default function ChatPage() {
  return (
    <Box maxWidth={900} mx="auto" mt={4} px={{ xs: 1, md: 3 }}>
      <Paper elevation={2} sx={{ p: { xs: 1, md: 3 }, borderRadius: 4, mb: 3 }}>
        <Typography variant="h4" fontWeight={800} mb={1.5}>
          Chat Mode
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={2}>
          Общайтесь с любой выбранной LLM-моделью в режиме реального времени, поддерживается стриминг, markdown-ответы, вставка примеров промптов и выбор модели на лету.
        </Typography>
      </Paper>
      <ChatMode />
    </Box>
  );
}
