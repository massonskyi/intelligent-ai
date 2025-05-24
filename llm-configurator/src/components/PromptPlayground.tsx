import React, { useEffect, useState } from "react";
import { Box, Typography, TextField, Button, Paper, CircularProgress, Alert, Divider } from "@mui/material";
import PromptExamples from "./PromptExamples";
import EXAMPLES from "../examples";
import { generatePipeline } from "../api/llmApi";

type PlaygroundHistory = {
  prompt: string;
  response: string;
  ts: number;
};
type Props = {
    defaultModel: string;
  };
  
  const PromptPlayground: React.FC<Props> = ({ defaultModel }) => {
  const [prompt, setPrompt] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<PlaygroundHistory[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>(defaultModel);

  useEffect(() => {
    setSelectedModel(defaultModel);
  }, [defaultModel]);

  const handleSend = async () => {
    if (!selectedModel) {
        setError("Сначала выберите модель!");
        return;
      }
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await generatePipeline({ model: selectedModel, prompt }); // "" - использовать дефолтную модель (можно добавить выбор)
      setResponse(res.result);
      setHistory(h => [{ prompt, response: res.result, ts: Date.now() }, ...h]);
    } catch (e: any) {
      setError(e?.message || "Ошибка генерации");
    }
    setLoading(false);
  };

  const handleExample = (examplePrompt: string) => {
    setPrompt(examplePrompt);
    setResponse(null);
    setError(null);
  };

  return (
    <Paper elevation={2} sx={{ p: 3, maxWidth: 700, mx: "auto", mt: 4, borderRadius: 4 }}>
      <Typography variant="h5" fontWeight={700} mb={2}>Playground</Typography>
      <PromptExamples examples={EXAMPLES} onSelect={handleExample} />
      <TextField
        label="Prompt / Инструкция"
        placeholder="Введите свой промпт или выберите из примеров"
        fullWidth
        multiline
        minRows={3}
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        sx={{ mb: 2 }}
      />
      <Box display="flex" gap={2} mb={2}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSend}
          disabled={loading || !prompt.trim()}
        >
          {loading ? <CircularProgress size={22} /> : "Отправить"}
        </Button>
        <Button
          variant="outlined"
          onClick={() => { setPrompt(""); setResponse(null); setError(null); }}
        >
          Очистить
        </Button>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {response !== null && (
        <Paper elevation={0} sx={{ bgcolor: "#f6f7fa", p: 2, mt: 2, borderRadius: 2 }}>
          <Typography variant="subtitle2" color="primary" mb={0.5}>Ответ модели:</Typography>
          <Typography
            component="pre"
            sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 15 }}
          >{response}</Typography>
        </Paper>
      )}
      <Divider sx={{ my: 3 }} />
      <Typography variant="h6" fontWeight={600} mb={1}>История</Typography>
      {history.length === 0 && (
        <Typography variant="body2" color="text.secondary">История пуста</Typography>
      )}
      {history.map((h, idx) => (
        <Paper key={h.ts + idx} sx={{ mb: 1, p: 2, borderRadius: 2, bgcolor: "#f7f8fc" }}>
          <Typography variant="caption" color="text.secondary">
            {new Date(h.ts).toLocaleTimeString()}
          </Typography>
          <Typography sx={{ fontWeight: 500, mt: 0.5 }}>Prompt:</Typography>
          <Typography component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", mb: 1 }}>{h.prompt}</Typography>
          <Typography sx={{ fontWeight: 500 }}>Ответ:</Typography>
          <Typography component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>{h.response}</Typography>
        </Paper>
      ))}
    </Paper>
  );
};

export default PromptPlayground;
