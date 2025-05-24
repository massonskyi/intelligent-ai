import React, { useEffect, useState } from "react";
import {
  Box, Typography, TextField, Button, CircularProgress, Tooltip, IconButton, Snackbar, Alert
} from "@mui/material";
import InfoIcon from "@mui/icons-material/Info";
import { getModelConfigs, setModelParam, getModelConfigs as reloadConfigs } from "../api/llmApi";
import Grid from "@mui/material/Grid"; // Без { GridProps }, если не нужно использовать типы явно!

type ParamDef = {
  key: string;
  value: any;
  type: "string" | "number" | "boolean";
  description?: string;
};

const PARAM_HINTS: Record<string, string> = {
  "temperature": "Степень случайности (0 — детерминированно, 1 — максимально случайно)",
  "top_p": "Ядро sampling (рекомендуется 0.8–0.95 для креативности)",
  "n_ctx": "Максимальная длина контекста (в токенах)",
  "n_threads": "Число потоков для инференса",
  "n_gpu_layers": "Сколько слоев грузить в GPU (0 — CPU)",
  "device": "Выбор устройства (cuda/cpu/mps)",
  // ... можешь добавить для других параметров
};

const guessType = (value: any): "string" | "number" | "boolean" =>
  typeof value === "boolean" ? "boolean" :
  typeof value === "number" ? "number" :
  "string";

export default function ModelSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [models, setModels] = useState<any>({});
  const [selected, setSelected] = useState<string>("");
  const [params, setParams] = useState<ParamDef[]>([]);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 1. Загрузить модели и выбрать активную
  const fetchConfigs = async () => {
    setLoading(true);
    setError(null);
    try {
      const configs = await getModelConfigs();
      setModels(configs);
      // Выбрать активную модель — например, первую, или сделать отдельный API
      const modelName = Object.keys(configs)[0];
      setSelected(modelName);

      // Построить список параметров (top-level + из params)
      const cfg = configs[modelName];
      const paramArr: ParamDef[] = [
        { key: "temperature", value: cfg.temperature, type: guessType(cfg.temperature), description: PARAM_HINTS["temperature"] },
        { key: "top_p", value: cfg.top_p, type: guessType(cfg.top_p), description: PARAM_HINTS["top_p"] },
        ...Object.entries(cfg.params || {}).map(([k, v]) => ({
          key: k, value: v, type: guessType(v), description: PARAM_HINTS[k] || undefined
        }))
      ];
      setParams(paramArr);
    } catch (e: any) {
      setError(e?.message || "Ошибка загрузки конфигов моделей");
    }
    setLoading(false);
  };

  useEffect(() => { fetchConfigs(); }, []);

  // 2. Изменение значения поля
  const handleParamChange = (key: string, newValue: any) => {
    setParams(prev =>
      prev.map(p => p.key === key ? { ...p, value: newValue } : p)
    );
  };

  // 3. Сохранение изменений (batch или по одному)
  const handleSave = async () => {
    setSaving(true);
    setSuccess(null);
    setError(null);
    try {
      for (const p of params) {
        await setModelParam({ model: selected, param: p.key, value: p.value });
      }
      setSuccess("Настройки сохранены!");
      // Reload fresh configs
      await fetchConfigs();
    } catch (e: any) {
      setError(e?.message || "Ошибка при сохранении");
    }
    setSaving(false);
  };

  if (loading) {
    return <Box textAlign="center" py={6}><CircularProgress /></Box>;
  }

  if (!selected || !models[selected]) {
    return <Box textAlign="center" color="text.secondary">Нет выбранной модели.</Box>;
  }

  return (
    <Box maxWidth={520} mx="auto" mt={2} p={3} bgcolor="background.paper" borderRadius={3} boxShadow={1}>
      <Typography variant="h6" mb={2} fontWeight={600}>Настройки: <b>{selected}</b></Typography>
        <Grid container spacing={2}>
        {params.map((p) => (
            <Grid item xs={12} sm={6} key={p.key}>
            <Tooltip title={p.description || p.key}>
              <TextField
                label={p.key}
                type={p.type === "number" ? "number" : "text"}
                fullWidth
                size="small"
                variant="outlined"
                value={p.value}
                InputProps={{
                  endAdornment: p.description
                    ? <InfoIcon fontSize="small" color="action" sx={{ ml: 1 }} />
                    : null
                }}
                onChange={e => {
                  let val: any = e.target.value;
                  if (p.type === "number") val = parseFloat(val);
                  if (p.type === "boolean") val = val === "true";
                  handleParamChange(p.key, val);
                }}
                sx={{ mb: 1 }}
              />
            </Tooltip>
          </Grid>
        ))}
      </Grid>
      <Box mt={3} textAlign="right">
        <Button
          variant="contained"
          color="primary"
          onClick={handleSave}
          disabled={saving}
          endIcon={saving ? <CircularProgress size={20} /> : undefined}
        >
          Сохранить
        </Button>
      </Box>
      <Snackbar open={!!success} autoHideDuration={3000} onClose={() => setSuccess(null)}>
        <Alert severity="success" onClose={() => setSuccess(null)}>{success}</Alert>
      </Snackbar>
      <Snackbar open={!!error} autoHideDuration={4000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>
      </Snackbar>
    </Box>
  );
}
