import React, { useEffect, useState } from "react";
import { Box, Typography, Paper, Select, MenuItem } from "@mui/material";
import PromptPlayground from "../components/PromptPlayground";
import { getModelConfigs, getAppConfig } from "../api/llmApi";

export default function PlaygroundPage() {
  const [models, setModels] = useState<string[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");

  // Загружаем модели и дефолтную модель
  useEffect(() => {
    async function fetchData() {
      const cfgs = await getModelConfigs();
      const modelNames = Object.keys(cfgs);
      setModels(modelNames);

      // Пытаемся получить дефолтную модель из app config
      let appConfig;
      try {
        appConfig = await getAppConfig();
      } catch { /* ignore */ }
      const defaultM = appConfig?.default_model || modelNames[0] || "";
      setDefaultModel(defaultM);
      setSelectedModel(defaultM);
    }
    fetchData();
  }, []);

  return (
    <Box maxWidth={900} mx="auto" mt={4} px={{ xs: 1, md: 3 }}>
      <Paper elevation={2} sx={{ p: { xs: 1, md: 3 }, borderRadius: 4, mb: 3 }}>
        <Typography variant="h4" fontWeight={800} mb={1.5}>
          Playground
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={2}>
          Тестируйте промпты, генерируйте Jenkinsfile и пайплайны, экспериментируйте с настройками и разными LLM.
        </Typography>
      </Paper>
      <Select
        value={selectedModel}
        onChange={e => setSelectedModel(e.target.value)}
        sx={{ mb: 2, minWidth: 200 }}
        size="small"
      >
        {models.map(m => (
          <MenuItem key={m} value={m}>{m}</MenuItem>
        ))}
      </Select>
      <PromptPlayground defaultModel={selectedModel} />
    </Box>
  );
}
