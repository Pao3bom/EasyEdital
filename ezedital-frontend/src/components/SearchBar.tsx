import { Box, TextField, InputAdornment, IconButton } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

const SearchBar: React.FC = () => {
  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
      }}
    >
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Pesquise por documentos jurídicos, dicas ou materiais"
        sx={{
          backgroundColor: "background.paper",
          borderRadius: "12px",
          "& .MuiOutlinedInput-root": {
            height: "60px", // Keep the height consistent
            fontSize: "1.1rem", // Larger font size for emphasis
            color: "text.primary",
            "& fieldset": {
              borderColor: "primary.main",
            },
            "&:hover fieldset": {
              borderColor: "primary.light",
            },
          },
        }}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                sx={{
                  color: "primary.main",
                  "&:hover": { color: "primary.light" },
                }}
              >
                <SearchIcon />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
    </Box>
  );
};

export default SearchBar;
