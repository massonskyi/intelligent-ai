import React, { useEffect, useState } from "react";
import {
  Box, Typography, Paper, Button, CircularProgress, Alert, MenuItem, Select, Switch, FormControlLabel, Divider, Snackbar
} from "@mui/material";
import { getAppConfig, setAppConfig, getModelConfigs, setModelParam } from "../api/llmApi";
import ModelSettings from "../components/ModelSettings"; // или встроить логику прямо здесь

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Глобальные настройки
  const [appConfig, setAppConfigState] = useState<any>({});
  const [models, setModels] = useState<any[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>("");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    async function fetchAll() {
      setLoading(true);
      try {
        const cfg = await getAppConfig();           // app_config — default_model
        const modelCfgs = await getModelConfigs();  // model_configs — список моделей
        const modelArr = Object.values(modelCfgs);
        setModels(modelArr);
  
        // если default_model нет среди моделей — выбрать первую
        const def = cfg.default_model && modelArr.some((m: any) => m.name === cfg.default_model)
          ? cfg.default_model
          : (modelArr[0]?.name || "");
        setDefaultModel(def);
        setTheme(cfg.theme || "light");
        setAppConfigState(cfg);
      } catch (e: any) {
        setError(e?.message || "Ошибка загрузки настроек");
      }
      setLoading(false);
    }
    fetchAll();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await setAppConfig({ ...appConfig, default_model: defaultModel, theme });
      setSuccess("Настройки сохранены!");
    } catch (e: any) {
      setError(e?.message || "Ошибка при сохранении");
    }
    setSaving(false);
  };

  if (loading) {
    return <Box textAlign="center" py={8}><CircularProgress /></Box>;
  }

  return (
    <Box maxWidth={600} mx="auto" mt={3} p={2}>
      <Typography variant="h4" fontWeight={700} mb={3}>Настройки приложения</Typography>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 4, mb: 4 }}>
        <Typography variant="h6" fontWeight={600} mb={2}>Глобальные параметры</Typography>
        <Box mb={2}>
          <Typography variant="body2" mb={0.5}>Дефолтная модель:</Typography>
          <Select
            fullWidth
            value={defaultModel}
            onChange={e => setDefaultModel(e.target.value)}
            size="small"
            sx={{ mb: 2 }}
            disabled={models.length === 0}
          >
            {models.map((m: any) => (
              <MenuItem key={m.name} value={m.name}>{m.name}</MenuItem>
            ))}
          </Select>
        </Box>
        <Box mb={2}>
          <FormControlLabel
            control={
              <Switch
                checked={theme === "dark"}
                onChange={() => setTheme(t => t === "dark" ? "light" : "dark")}
              />
            }
            label="Тёмная тема"
          />
        </Box>
        <Divider sx={{ my: 2 }} />
        <Button
          variant="contained"
          color="primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? <CircularProgress size={20} /> : "Сохранить"}
        </Button>
        {success && <Snackbar open={!!success} autoHideDuration={3000} onClose={() => setSuccess(null)} message={success} />}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </Paper>

      <ModelSettings />
    </Box>
  );
}
