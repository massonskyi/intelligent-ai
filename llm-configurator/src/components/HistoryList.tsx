import React, { useEffect, useState, useMemo, forwardRef, useImperativeHandle } from "react";
import {
  Box, Paper, Typography, IconButton, CircularProgress, TextField, InputAdornment, Alert, Tooltip, Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Divider
} from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import SearchIcon from "@mui/icons-material/Search";
import DeleteIcon from "@mui/icons-material/DeleteOutline";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import StarIcon from "@mui/icons-material/Star";
import InfoIcon from "@mui/icons-material/InfoOutlined";
import { getHistory } from "../api/llmApi";

export type HistoryItem = {
    id?: string;
    prompt?: string;
    question?: string;
    response?: string;
    answer?: string;
    timestamp?: string | number;
    favorite?: boolean;
  };
interface Props {
  userId?: string;
  model?: string;
  limit?: number;
}

const HistoryList = forwardRef<any, Props>(({ userId, model, limit = 20 }, ref) => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [favorites, setFavorites] = useState<Record<string, boolean>>({});
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailItem, setDetailItem] = useState<HistoryItem | null>(null);

  // Загрузка истории
  useEffect(() => {
    setLoading(true);
    setError(null);
    getHistory(limit, 0)
      .then((data: HistoryItem[]) => setItems(data))
      .catch(e => setError(e?.message || "Ошибка загрузки истории"))
      .finally(() => setLoading(false));
  }, [limit]);

  // Локальный поиск
  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return items.filter(it =>
      (it.prompt?.toLowerCase() || it.question?.toLowerCase() || "").includes(q) ||
      (it.response?.toLowerCase() || it.answer?.toLowerCase() || "").includes(q)
    );
  }, [search, items]);
  

  // Копирование
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  // Фавориты (можно добавить сохранение в backend)
  const toggleFavorite = (id: string | number | undefined) => {
    if (!id) return;
    setFavorites(fav => ({ ...fav, [id]: !fav[id] }));
  };

  // Удаление (можно добавить backend-метод, пока локально)
  const handleDelete = (id: string | number | undefined) => {
    if (!id) return;
    setItems(prev => prev.filter(it => it.id !== id));
  };

  // Подробнее (модальное окно)
  const openDetail = (item: HistoryItem) => {
    setDetailItem(item);
    setDetailOpen(true);
  };

  useImperativeHandle(ref, () => ({
    getItems: () => items
  }));

  if (loading) {
    return <Box textAlign="center" py={4}><CircularProgress /></Box>;
  }
  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }
  if (!filtered.length) {
    return (
      <Paper elevation={1} sx={{ p: 3, borderRadius: 3, textAlign: "center", color: "text.secondary" }}>
        Нет истории
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
      <Box display="flex" alignItems="center" mb={2} gap={1}>
        <Typography variant="h6" fontWeight={600} flex={1}>История запросов</Typography>
        <TextField
          size="small"
          placeholder="Поиск"
          value={search}
          onChange={e => setSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            )
          }}
        />
      </Box>
      <Box maxHeight={400} sx={{ overflowY: "auto" }}>
        {filtered.map((h, idx) => {
          const fav = favorites[h.id ?? idx] ?? h.favorite;
          return (
            <Paper key={h.id ?? idx} sx={{
              mb: 2, p: 2, borderRadius: 2,
              bgcolor: fav ? "#fffde7" : "#f7f8fc",
              border: fav ? "1.5px solid #ffb300" : undefined,
              boxShadow: fav ? 6 : 1,
            }}>
              <Box display="flex" alignItems="center" mb={0.5} gap={1}>
                <Typography variant="caption" color="text.secondary" flex={1}>
                  {h.timestamp
                    ? new Date(h.timestamp).toLocaleString()
                    : `#${filtered.length - idx}`}
                </Typography>
                <Tooltip title={fav ? "В избранном" : "В избранное"}>
                  <IconButton size="small" onClick={() => toggleFavorite(h.id ?? idx)}>
                    {fav ? <StarIcon color="warning" /> : <StarBorderIcon />}
                  </IconButton>
                </Tooltip>
                <Tooltip title="Подробнее">
                  <IconButton size="small" onClick={() => openDetail(h)}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Удалить из истории">
                  <IconButton size="small" color="error" onClick={() => handleDelete(h.id ?? idx)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Копировать prompt">
                <IconButton size="small" onClick={() => handleCopy(h.prompt || h.question || "")}>
                    <ContentCopyIcon fontSize="small" />
                </IconButton>
                </Tooltip>
                <Tooltip title="Копировать ответ">
                    <IconButton size="small" onClick={() => handleCopy(h.response || h.answer || "")}>
                        <ContentCopyIcon fontSize="small" />
                    </IconButton>
                </Tooltip>
              </Box>
              <Typography variant="subtitle2" color="primary" mb={0.5}>Prompt:</Typography>
<Typography component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 15, mb: 1 }}>
  {h.prompt || h.question || "<нет промпта>"}
</Typography>
<Typography variant="subtitle2" color="secondary" mb={0.5}>Ответ:</Typography>
<Typography component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 15 }}>
  {h.response || h.answer || ""}
</Typography>
            </Paper>
          );
        })}
      </Box>

      {/* Модальное окно для "Подробнее" */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Детали запроса</DialogTitle>
        <DialogContent dividers>
          {detailItem && (
            <>
              <Typography variant="caption" color="text.secondary">Дата: {detailItem.timestamp ? new Date(detailItem.timestamp).toLocaleString() : "—"}</Typography>
              <Box my={2}>
                <Typography variant="subtitle1" fontWeight={500}>Prompt:</Typography>
                <Typography component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 15 }}>
                  {detailItem.prompt}
                </Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" fontWeight={500}>Ответ:</Typography>
              <Typography component="pre" sx={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 15 }}>
                {detailItem.response}
              </Typography>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
});

export default HistoryList;
