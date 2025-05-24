import React, { useEffect, useState } from "react";
import {
  Box, Paper, Typography, Button, Grid, Tooltip, Chip, Avatar, Divider, CircularProgress
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import TerminalIcon from "@mui/icons-material/Terminal";
import ChatIcon from "@mui/icons-material/Chat";
import HistoryIcon from "@mui/icons-material/History";
import { useNavigate } from "react-router-dom";
import { getModelConfigs } from "../api/llmApi";

const CARD_STYLE = { borderRadius: 4, p: 3, minHeight: 130, display: "flex", flexDirection: "column", alignItems: "flex-start" };

export default function HomePage() {
  const navigate = useNavigate();
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getModelConfigs().then(cfgs => {
      setModels(Object.values(cfgs));
      setLoading(false);
    });
  }, []);

  return (
    <Box sx={{ maxWidth: 900, mx: "auto", my: 4, px: { xs: 1, sm: 3 } }}>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Avatar sx={{ width: 52, height: 52, bgcolor: "#524cfc" }}>
          <AutoAwesomeIcon sx={{ fontSize: 36, color: "#fff" }} />
        </Avatar>
        <Box>
          <Typography variant="h4" fontWeight={800} letterSpacing={-1}>
            LLM Playground
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" mt={0.5}>
            Интерактивный конфигуратор и генератор Jenkins pipeline с поддержкой DeepSeek, Mistral, Llama2, StarCoder и др.
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={CARD_STYLE}>
            <TerminalIcon fontSize="large" color="primary" sx={{ mb: 1 }} />
            <Typography variant="h6" fontWeight={600}>Playground</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Тестируйте любые промпты и пайплайны в один клик.
            </Typography>
            <Button variant="contained" onClick={() => navigate("/playground")}>Открыть Playground</Button>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={CARD_STYLE}>
            <ChatIcon fontSize="large" color="primary" sx={{ mb: 1 }} />
            <Typography variant="h6" fontWeight={600}>Chat</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Общайтесь с LLM в режиме диалога. Поддержка стриминга и истории.
            </Typography>
            <Button variant="contained" onClick={() => navigate("/chat")}>Чат-режим</Button>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={CARD_STYLE}>
            <HistoryIcon fontSize="large" color="primary" sx={{ mb: 1 }} />
            <Typography variant="h6" fontWeight={600}>История</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Просматривайте запросы и ответы, копируйте или сохраняйте избранное.
            </Typography>
            <Button variant="contained" onClick={() => navigate("/history")}>К истории</Button>
          </Paper>
        </Grid>
      </Grid>

      <Divider sx={{ my: 5 }} />
      <Typography variant="h6" fontWeight={700} mb={2}>
        Доступные модели
      </Typography>
      {loading ? (
        <CircularProgress sx={{ my: 3 }} />
      ) : (
        <Grid container spacing={2}>
          {models.map((m: any, idx) => (
            <Grid item key={m.name} xs={12} sm={6} md={4}>
              <Paper elevation={2} sx={{ p: 2, borderRadius: 3, mb: 1 }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    label={m.name}
                    color="primary"
                    size="small"
                    sx={{ fontWeight: 600, mr: 1 }}
                  />
                  <Tooltip title={m.type}>
                    <Chip
                      label={m.type}
                      variant="outlined"
                      size="small"
                      sx={{ ml: 1, textTransform: "capitalize" }}
                    />
                  </Tooltip>
                </Box>
                <Typography variant="body2" color="text.secondary" mt={1} mb={0.5}>
                  {m.model_path}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Температура: <b>{m.temperature}</b>, Top-p: <b>{m.top_p}</b>
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      )}

      <Box mt={6} mb={1} textAlign="center" color="text.secondary">
        <Typography variant="body2">
          Open-source проект (<a href="https://github.com/your-org/llm-playground" target="_blank" rel="noopener noreferrer">GitHub</a>).
          — Powered by FastAPI, React 18, Material UI 5, DeepSeek, Mistral, Llama2, StarCoder, llama.cpp.
        </Typography>
      </Box>
    </Box>
  );
}
