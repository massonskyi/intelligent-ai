import React, { useRef, useState, useEffect } from "react";
import {
  Box, Paper, Typography, IconButton, TextField, Button, CircularProgress, Tooltip, List, ListItem, ListItemText, ListItemSecondaryAction, MenuItem, Select
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Markdown from "react-markdown";
import PromptExamples from "./PromptExamples";
import EXAMPLES from "../examples";
import { getModelConfigs } from "../api/llmApi";

type ChatMessage = { role: "user" | "assistant", text: string, ts: number };

const SESSION_KEY = "llm_chat_history";

const ChatMode: React.FC = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const stored = sessionStorage.getItem(SESSION_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    getModelConfigs().then(cfgs => {
      const arr = Object.values(cfgs).map((c: any) => c.name);
      setModels(arr);
      if (!selectedModel && arr.length) setSelectedModel(arr[0]);
    });
  }, [selectedModel]);

  // Stream-чат через fetch + ReadableStream
  const send = async () => {
    if (!input.trim() || !selectedModel) return;
    setMessages(msgs => [...msgs, { role: "user", text: input, ts: Date.now() }]);
    setLoading(true);
    setIsTyping(true);

    let fullResponse = "";
    setMessages(msgs => [...msgs, { role: "assistant", text: "", ts: Date.now() }]);
    try {
      const resp = await fetch(`/llm/stream_generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: selectedModel, prompt: input }),
      });

      if (!resp.body) throw new Error("Stream not supported");
      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        fullResponse += chunk;
        setMessages(msgs => {
          // обновляем последний assistant message по мере прихода текста
          const lastIndex = msgs.length - 1;
          if (lastIndex < 0) return msgs;
          const updated = [...msgs];
          updated[lastIndex] = { ...updated[lastIndex], text: fullResponse };
          return updated;
        });
      }
    } catch (e: any) {
      setMessages(msgs => [...msgs, { role: "assistant", text: "[Ошибка генерации]", ts: Date.now() }]);
    }
    setLoading(false);
    setIsTyping(false);
    setInput("");
  };

  const handleExample = (prompt: string) => setInput(prompt);

  const handleCopy = (text: string) => navigator.clipboard.writeText(text);

  return (
    <Paper elevation={2} sx={{ p: { xs: 1, md: 3 }, maxWidth: 700, mx: "auto", mt: 3, borderRadius: 4, display: "flex", flexDirection: "column", height: "75vh" }}>
      <Box mb={2} display="flex" gap={2} alignItems="center">
        <Typography variant="h5" fontWeight={700} flex={1}>Chat Mode</Typography>
        <Select
          value={selectedModel}
          onChange={e => setSelectedModel(e.target.value)}
          size="small"
          sx={{ minWidth: 140 }}
        >
          {models.map(m => <MenuItem value={m} key={m}>{m}</MenuItem>)}
        </Select>
      </Box>
      <PromptExamples examples={EXAMPLES} onSelect={handleExample} />
      <Box flex={1} overflow="auto" component={List} ref={listRef} sx={{ bgcolor: "#f5f6fa", borderRadius: 2, p: 1, mb: 1 }}>
        {messages.length === 0 && (
          <Box textAlign="center" color="text.secondary" mt={6}>
            <Typography variant="body2" color="text.secondary">Здесь будет история чата</Typography>
          </Box>
        )}
        {messages.map((m, idx) => (
          <ListItem
            key={m.ts + "-" + m.role + "-" + idx}
            sx={{
              flexDirection: m.role === "user" ? "row-reverse" : "row",
              alignItems: "flex-start",
              mb: 1,
              px: 0
            }}
            disableGutters
          >
            <Paper
              elevation={m.role === "user" ? 1 : 3}
              sx={{
                p: 1.3,
                bgcolor: m.role === "user" ? "#e3e1ee" : "#fff",
                borderRadius: 2,
                maxWidth: { xs: "85%", md: "70%" },
                minWidth: 0
              }}
            >
              <ListItemText
                primary={
                  <Markdown
                    children={m.text}
                    components={{
                      p: ({ children }) => <Typography component="span">{children}</Typography>
                    }}
                  />
                }
              />
            </Paper>
            <ListItemSecondaryAction sx={{ minWidth: 40 }}>
              <Tooltip title="Скопировать">
                <IconButton size="small" onClick={() => handleCopy(m.text)}>
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
        {isTyping && (
          <Box display="flex" alignItems="center" minHeight={36} py={1}>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            <Typography variant="caption" color="text.secondary">
              Модель пишет...
            </Typography>
          </Box>
        )}
      </Box>
      <Box display="flex" gap={1} mt="auto">
        <TextField
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Введите запрос или выберите пример..."
          fullWidth
          multiline
          minRows={1}
          maxRows={4}
          size="small"
          disabled={loading}
        />
        <Button
          variant="contained"
          endIcon={<SendIcon />}
          onClick={send}
          disabled={loading || !input.trim() || !selectedModel}
          sx={{ minWidth: 100 }}
        >
          {loading ? <CircularProgress size={20} /> : "Отправить"}
        </Button>
      </Box>
    </Paper>
  );
};

export default ChatMode;
