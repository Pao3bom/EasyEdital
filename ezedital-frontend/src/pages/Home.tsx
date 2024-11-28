import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  CircularProgress,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import SearchBar from "../components/SearchBar";
import DropZone from "../components/DropZone";
import AdvancedOptions from "../components/AdvancedOptions";
import { useEffect, useState } from "react";

const Home: React.FC = () => {
  const [openOptions, setOpenOptions] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          threshold: 80,
          top_k: 5,
          use_fuzzy: true,
          use_embeddings: true,
          use_tfidf: true,
          combine_results: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      setSearchResults(data.results.combined || []);
    } catch (error) {
      console.error("Failed to fetch search results:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {console.log(searchResults)}, [searchResults]);

  return (
    <Box
      sx={{
        height: "100vh",
        overflow: "hidden",
        backgroundColor: "background.default",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "16px",
        padding: "16px",
      }}
    >
      <Typography
        variant="h3"
        sx={{
          fontWeight: "bold",
          color: "primary.main",
          textAlign: "center",
        }}
      >
        Ezedital: Pesquisa Jurídica com IA
      </Typography>
      <Typography
        variant="h6"
        sx={{
          maxWidth: "600px",
          color: "text.secondary",
          textAlign: "center",
        }}
      >
        Descubra insights jurídicos, documentos e dicas de forma eficiente com o
        poder da IA.
      </Typography>
      <Box sx={{ width: "100%", maxWidth: "800px" }}>
        <SearchBar onSearch={handleSearch} />
      </Box>
      <Button
        variant="outlined"
        size="small"
        sx={{
          color: "primary.main",
          borderColor: "primary.main",
          marginTop: "16px",
          "&:hover": { borderColor: "primary.light" },
        }}
        onClick={() => setOpenOptions(true)}
      >
        Mostrar Opções Avançadas
      </Button>
      {loading && <CircularProgress sx={{ marginTop: "16px" }} />}
      <Box sx={{ width: "100%", maxWidth: "800px", marginTop: "24px" }}>
        {searchResults.length > 0 ? (
          <Typography variant="h6" sx={{ color: "text.primary" }}>
            Resultados:
          </Typography>
        ) : (
          !loading && (
            <Typography variant="body1" sx={{ color: "text.secondary" }}>
              {/* Sem resultados para exibir. */}
            </Typography>
          )
        )}
        <ol>
          {searchResults.map((result, index) => (
            <li key={index}>{result.file_path}</li>
          ))}
        </ol>
      </Box>
      <Box
        sx={{
          width: "100%",
          maxWidth: "800px",
          height: "250px",
          marginTop: "24px",
        }}
      >
        <DropZone />
      </Box>
      <Dialog
        open={openOptions}
        onClose={() => setOpenOptions(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: "background.default",
            color: "text.primary",
            borderRadius: "12px",
            border: "1px solid",
            borderColor: "primary.main",
            boxShadow: "0 8px 24px rgba(0, 0, 0, 0.8)",
          },
        }}
      >
        <DialogTitle
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            color: "text.primary",
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: "bold" }}>
            Opções Avançadas
          </Typography>
          <IconButton
            onClick={() => setOpenOptions(false)}
            sx={{ color: "primary.main" }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <AdvancedOptions />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Home;
