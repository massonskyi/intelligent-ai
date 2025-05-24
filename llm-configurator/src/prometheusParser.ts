export function parsePrometheusMetrics(text: string): Record<string, number | object> {
    const lines = text.split("\n");
    const metrics: any = {};
    lines.forEach(line => {
      if (line.startsWith("#") || !line.trim()) return;
      const match = line.match(/^(\w+)(\{(.+?)\})?\s+(.+)$/);
      if (match) {
        const [, key, , labels, value] = match;
        if (labels) {
          const objKey = key + JSON.stringify(Object.fromEntries(
            labels.split(",").map(s => {
              const [k, v] = s.split("=");
              return [k, v.replace(/"/g, "")];
            })
          ));
          metrics[objKey] = parseFloat(value);
        } else {
          metrics[key] = parseFloat(value);
        }
      }
    });
    return metrics;
  }
  