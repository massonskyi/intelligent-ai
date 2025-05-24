import React, { useEffect, useState } from "react";
import {
  Box, FormControl, InputLabel, Select, MenuItem, CircularProgress,
  Typography, IconButton, Tooltip, Skeleton, Alert, ListItemText
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import InfoIcon from "@mui/icons-material/Info";
import { getModelConfigs, setDefaultModel } from "../api/llmApi";

interface ModelOption {
  name: string;
  type: string;
  model_path: string;
  temperature: number;
  top_p: number;
  params: Record<string, any>;
}

const ModelSelector: React.FC = () => {
  const [models, setModels] = useState<ModelOption[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Загрузка моделей (с автообновлением по interval)
  useEffect(() => {
    fetchModels();
  // eslint-disable-next-line
  }, []);

  // Загрузка из API
  async function fetchModels() {
    setLoading(true);
    setError(null);
    try {
      const configs = await getModelConfigs();
      const arr: ModelOption[] = Object.values(configs).map((cfg: any) => ({
        name: cfg.name,
        type: cfg.type,
        model_path: cfg.model_path,
        temperature: cfg.temperature,
        top_p: cfg.top_p,
        params: cfg.params,
      }));
      setModels(arr);
      if (arr.length && !selected) setSelected(arr[0].name);
    } catch (e: any) {
      setError(e?.message || "Ошибка загрузки моделей");
    }
    setLoading(false);
  }

  // Смена модели
  const handleChange = async (event: any) => {
    const modelName = event.target.value;
    setSelected(modelName);
    setLoading(true);
    try {
      await setDefaultModel(modelName);
    } catch (e: any) {
      setError(e?.message || "Ошибка выбора модели");
    }
    setLoading(false);
  };

  // Найти объект выбранной модели
  const current = models.find((m) => m.name === selected);

  return (
    <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
      <FormControl fullWidth size="small" variant="outlined">
        <InputLabel id="model-select-label">Модель</InputLabel>
        <Select
          labelId="model-select-label"
          value={selected}
          label="Модель"
          onChange={handleChange}
          disabled={loading || !models.length}
          MenuProps={{ PaperProps: { style: { maxHeight: 400 } } }}
        >
          {loading
            ? <MenuItem><Skeleton width={120} /></MenuItem>
            : models.map((m) => (
              <MenuItem key={m.name} value={m.name}>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={0.5}>
                      {m.name}
                      <Tooltip title={m.type === "transformers" ? "Transformers" : "llama.cpp"}>
                        <Typography variant="caption" color="secondary" fontWeight={500}>
                          [{m.type}]
                        </Typography>
                      </Tooltip>
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {m.model_path}
                    </Typography>
                  }
                />
              </MenuItem>
            ))}
        </Select>
      </FormControl>
      {/* Info о выбранной модели */}
      {current && (
        <Tooltip
          title={
            <Box>
              <Typography variant="body2"><b>{current.name}</b> [{current.type}]</Typography>
              <Typography variant="caption">Path: {current.model_path}</Typography><br />
              <Typography variant="caption">Temperature: {current.temperature} | Top-p: {current.top_p}</Typography><br />
              <Typography variant="caption">Params: {JSON.stringify(current.params)}</Typography>
            </Box>
          }
        >
          <IconButton size="small" color="primary"><InfoIcon /></IconButton>
        </Tooltip>
      )}
      {/* Skeleton/Лоадер/Ошибки */}
      {loading && <CircularProgress size={22} />}
      <IconButton onClick={fetchModels} size="small" sx={{ ml: 1 }} title="Обновить список моделей">
        <RefreshIcon fontSize="small" />
      </IconButton>
      {error && (
        <Alert severity="error" sx={{ ml: 1, fontSize: 12 }}>{error}</Alert>
      )}
    </Box>
  );
};

export default ModelSelector;
