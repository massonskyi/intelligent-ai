import React, { useState, useMemo } from "react";
import {
  Box, List, ListItemButton, ListItemText, Paper, Typography,
  Tooltip, TextField, InputAdornment
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import InsertCommentIcon from "@mui/icons-material/InsertComment";

export type PromptExample = {
  label: string;
  prompt: string;
  description?: string;
};

interface Props {
  examples: PromptExample[];
  onSelect: (prompt: string) => void;
}

const PromptExamples: React.FC<Props> = ({ examples, onSelect }) => {
  const [search, setSearch] = useState<string>("");

  // Поиск по label, description, prompt
  const filtered = useMemo(() => {
    if (!search.trim()) return examples;
    const q = search.toLowerCase();
    return examples.filter(ex =>
      ex.label.toLowerCase().includes(q) ||
      (ex.description && ex.description.toLowerCase().includes(q)) ||
      ex.prompt.toLowerCase().includes(q)
    );
  }, [search, examples]);

  return (
    <Paper elevation={1} sx={{ p: 2, mb: 2, borderRadius: 3 }}>
      <Box display="flex" alignItems="center" mb={1} gap={1}>
        <InsertCommentIcon color="primary" />
        <Typography variant="subtitle1" fontWeight={600}>Примеры промптов</Typography>
      </Box>
      <TextField
        placeholder="Поиск примера..."
        size="small"
        value={search}
        onChange={e => setSearch(e.target.value)}
        fullWidth
        sx={{ mb: 1 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon fontSize="small" />
            </InputAdornment>
          ),
        }}
      />
      <List dense sx={{ maxHeight: 280, overflowY: "auto" }}>
        {filtered.length === 0 && (
          <Typography variant="caption" color="text.secondary" sx={{ p: 2 }}>
            Нет совпадений
          </Typography>
        )}
        {filtered.map((ex, idx) => (
          <Tooltip key={idx} title={ex.description || ex.prompt} arrow placement="top">
            <ListItemButton
              sx={{ borderRadius: 2, mb: 0.5 }}
              onClick={() => onSelect(ex.prompt)}
            >
              <ListItemText
                primary={ex.label}
                secondary={ex.description}
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </ListItemButton>
          </Tooltip>
        ))}
      </List>
    </Paper>
  );
};

export default PromptExamples;
