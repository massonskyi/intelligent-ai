// src/pages/DashboardPage.tsx
import React, { useEffect, useState } from "react";
import { Box, Typography, Paper, Grid, CircularProgress } from "@mui/material";
import { getPrometheusMetrics, getModelConfigs } from "../api/llmApi";
import { parsePrometheusMetrics } from "../prometheusParser";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList } from "recharts";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<any | null>(null);
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log("📡 Fetching metrics...");
    getPrometheusMetrics()
      .then(txt => {
        console.log("✅ Raw metrics:", txt);
        setMetrics(parsePrometheusMetrics(txt));
      })
      .catch(err => {
        console.error("❌ Error loading metrics:", err);
      });
  });

  // Готовим данные для BarChart
  const chartData = React.useMemo(() => {
    if (!metrics || models.length === 0) return [];
  
    return models.map((m: any) => {
      const modelName = m.name;
      return {
        name: modelName,
        requests: metrics[`llm_model_requests_total{model="${modelName}"}`] ?? 0,
        tokens: metrics[`llm_model_tokens_total{model="${modelName}"}`] ?? 0,
        latency: metrics[`llm_model_avg_latency_ms{model="${modelName}"}`] ?? 0,
      };
    });
  }, [metrics, models]);

  return (
    <Box maxWidth={1100} mx="auto" mt={4} px={{ xs: 1, md: 3 }}>
      <Typography variant="h4" fontWeight={800} mb={3}>Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 4, minHeight: 130 }}>
            <Typography variant="h6" mb={1}>Запросы / Токены</Typography>
            {!metrics ? <CircularProgress /> :
              <Box>
                <Typography variant="body2">Всего запросов: <b>{metrics.llm_total_requests ?? "—"}</b></Typography>
                <Typography variant="body2">Всего токенов: <b>{metrics.llm_total_tokens ?? "—"}</b></Typography>
                <Typography variant="body2">Средняя задержка: <b>{metrics.llm_avg_latency_ms?.toFixed(1) ?? "—"} мс</b></Typography>
              </Box>
            }
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 4, minHeight: 200 }}>
            <Typography variant="h6" mb={2}>Топ моделей по запросам</Typography>
            {!chartData.length ? <CircularProgress /> :
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="requests" fill="#6750A4">
                    <LabelList dataKey="requests" position="top" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            }
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 4, minHeight: 180 }}>
            <Typography variant="h6" mb={2}>Топ моделей по токенам</Typography>
            {!chartData.length ? <CircularProgress /> :
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="tokens" fill="#03DAC6">
                    <LabelList dataKey="tokens" position="top" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            }
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, borderRadius: 4, minHeight: 180 }}>
            <Typography variant="h6" mb={2}>Средняя задержка (ms)</Typography>
            {!chartData.length ? <CircularProgress /> :
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="latency" fill="#FFB300">
                    <LabelList dataKey="latency" position="top" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            }
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
