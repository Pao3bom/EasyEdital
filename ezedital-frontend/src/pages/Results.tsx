import { Box, Typography } from "@mui/material";

const Results: React.FC = () => {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        backgroundColor: "background.default",
        color: "text.primary",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "32px",
      }}
    >
      <Typography variant="h4" sx={{ fontWeight: "bold" }}>
        Resultados da Pesquisa
      </Typography>
      <Typography variant="body1" sx={{ color: "text.secondary", marginTop: 2 }}>
        Aqui serão exibidos os resultados da sua pesquisa.
      </Typography>
    </Box>
  );
};

export default Results;
