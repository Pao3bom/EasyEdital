import { Box, Typography, Button, Dialog, DialogContent, DialogTitle, IconButton, CircularProgress } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import SearchBar from "../components/SearchBar";
import DropZone from "../components/DropZone";
import AdvancedOptions from "../components/AdvancedOptions";
import { useState } from "react";

const Home: React.FC = () => {
  const [openOptions, setOpenOptions] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]); // Store results
  const [loading, setLoading] = useState(false); // Track loading state

  const handleSearch = async (query: string) => {
    console.log("Sending query to backend:", query);
    setLoading(true);
    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("Search results:", data.results);
      setSearchResults(data.results); // Update results state
    } catch (error) {
      console.error("Failed to fetch search results:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        height: "100vh", // Full viewport height
        overflow: "hidden", // Prevent scrollbars
        backgroundColor: "background.default",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center", // Center all elements vertically
        gap: "16px",
        padding: "16px",
      }}
    >
      {/* App Title */}
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
      {/* Subtitle */}
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
      {/* Search Bar */}
      <Box sx={{ width: "100%", maxWidth: "800px" }}>
        <SearchBar onSearch={handleSearch} />
      </Box>
       {/* Loading Indicator */}
       {loading && <CircularProgress sx={{ marginTop: "16px" }} />}
      {/* Display Results */}
      <Box
        sx={{
          width: "100%",
          maxWidth: "800px",
          marginTop: "24px",
        }}
      >
        {searchResults.length > 0 ? (
          <Typography variant="h6" sx={{ color: "text.primary" }}>
            Resultados:
          </Typography>
        ) : (
          !loading && (
            <Typography variant="body1" sx={{ color: "text.secondary" }}>
              Sem resultados para exibir.
            </Typography>
          )
        )}
        <ul>
          {searchResults.map((result, index) => (
            <li key={index}>{result}</li>
          ))}
        </ul>
      </Box>
      {/* Advanced Options Button */}
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
      {/* DropZone */}
      <Box
        sx={{
          width: "100%",
          maxWidth: "800px",
          height: "250px", // Increase height for better balance
          marginTop: "24px",
        }}
      >
        <DropZone />
      </Box>
      {/* Advanced Options Dialog */}
      <Dialog
        open={openOptions}
        onClose={() => setOpenOptions(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: "background.default", // Match page background
            color: "text.primary", // Match text color
            borderRadius: "12px",
            border: "1px solid", // Subtle border for separation
            borderColor: "primary.main",
            boxShadow: "0 8px 24px rgba(0, 0, 0, 0.8)", // Enhanced shadow for depth
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
