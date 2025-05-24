// src/pages/AboutPage.tsx
import React from "react";
import { Box, Typography, Paper, Link } from "@mui/material";

export default function AboutPage() {
  return (
    <Box maxWidth={700} mx="auto" mt={4} px={{ xs: 1, md: 3 }}>
      <Paper elevation={2} sx={{ p: { xs: 2, md: 4 }, borderRadius: 4 }}>
        <Typography variant="h4" fontWeight={800} mb={2}>О проекте</Typography>
        <Typography variant="body1" mb={2}>
          <b>LLM Playground</b> — open-source платформа для генерации Jenkins pipeline и работы с современными языковыми моделями (DeepSeek, Mistral, Llama2, StarCoder и др).
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Проект поддерживает быструю интеграцию кастомных моделей, гибкую настройку через веб-интерфейс и API, а также хранение истории запросов.
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Бэкенд — FastAPI, фронтенд — React 18 + Material UI 5.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Код и инструкции:{" "}
          <Link href="https://github.com/your-org/llm-playground" target="_blank" rel="noopener noreferrer">
            GitHub: your-org/llm-playground
          </Link>
        </Typography>
        <Typography variant="caption" display="block" mt={4} color="text.secondary">
          &copy; {new Date().getFullYear()} Your Name / Your Team. MIT License.
        </Typography>
      </Paper>
    </Box>
  );
}
