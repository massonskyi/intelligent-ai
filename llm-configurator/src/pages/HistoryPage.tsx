// src/pages/HistoryPage.tsx
import React, { useRef } from "react";
import { Box, Typography, Paper, Button } from "@mui/material";
import HistoryList from "../components/HistoryList";

export default function HistoryPage() {
  const historyListRef = useRef<any>(null);

  function saveAs(blob: Blob, arg1: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = arg1;
    a.click();
    URL.revokeObjectURL(url);
    console.log("saved", arg1);
  }

  return (
    <Box maxWidth={900} mx="auto" mt={4} px={{ xs: 1, md: 3 }}>
      <Paper elevation={2} sx={{ p: { xs: 1, md: 3 }, borderRadius: 4, mb: 3 }}>
        <Typography variant="h4" fontWeight={800} mb={1.5}>
          История запросов
        </Typography>
        <Typography variant="body1" color="text.secondary" mb={2}>
          Просматривайте свои запросы к LLM, копируйте пайплайны, добавляйте в избранное, удаляйте лишнее.
        </Typography>
      </Paper>
      <HistoryList ref={historyListRef} limit={50} />
      <Button
          variant="outlined"
          onClick={() => {
            const items = historyListRef.current?.getItems() || [];
            const data = JSON.stringify(items, null, 2);
            const blob = new Blob([data], { type: "application/json" });
            saveAs(blob, `llm_history_${Date.now()}.json`);
          }}
          sx={{ mb: 2 }}
        >
          Экспортировать историю
      </Button>
    </Box>
  );
}
