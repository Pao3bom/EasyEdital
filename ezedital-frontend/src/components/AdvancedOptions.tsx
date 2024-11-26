import { Box, Typography, TextField, MenuItem, Button, Switch, FormControlLabel } from "@mui/material";
import { useState } from "react";

const AdvancedOptions: React.FC = () => {
  const [dateRange, setDateRange] = useState<string>("");
  const [category, setCategory] = useState<string>("");
  const [enableAI, setEnableAI] = useState(true);

  const handleApplyOptions = () => {
    console.log("Opções aplicadas:", { dateRange, category, enableAI });
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        color: "text.primary", // Ensure text matches app theme
      }}
    >
      <TextField
        label="Intervalo de Datas"
        select
        value={dateRange}
        onChange={(e) => setDateRange(e.target.value)}
        sx={{
          backgroundColor: "background.paper", // Slightly lighter for fields
          "& .MuiOutlinedInput-root": {
            color: "text.primary",
            "& fieldset": { borderColor: "primary.main" },
            "&:hover fieldset": { borderColor: "primary.light" },
          },
        }}
      >
        <MenuItem value="last_week">Última Semana</MenuItem>
        <MenuItem value="last_month">Último Mês</MenuItem>
        <MenuItem value="last_year">Último Ano</MenuItem>
      </TextField>
      <TextField
        label="Categoria"
        select
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        sx={{
          backgroundColor: "background.paper",
          "& .MuiOutlinedInput-root": {
            color: "text.primary",
            "& fieldset": { borderColor: "primary.main" },
            "&:hover fieldset": { borderColor: "primary.light" },
          },
        }}
      >
        <MenuItem value="contracts">Contratos</MenuItem>
        <MenuItem value="case_laws">Jurisprudências</MenuItem>
        <MenuItem value="legal_tips">Dicas Jurídicas</MenuItem>
      </TextField>
      <FormControlLabel
        control={
          <Switch
            checked={enableAI}
            onChange={(e) => setEnableAI(e.target.checked)}
            sx={{
              "& .MuiSwitch-track": { backgroundColor: "primary.main" },
            }}
          />
        }
        label="Ativar Recomendações por IA"
        sx={{
          color: "text.primary",
        }}
      />
      <Button
        variant="contained"
        sx={{
          backgroundColor: "primary.main",
          "&:hover": { backgroundColor: "primary.light" },
        }}
        onClick={handleApplyOptions}
      >
        Aplicar Opções
      </Button>
    </Box>
  );
};

export default AdvancedOptions;
