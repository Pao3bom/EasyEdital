import { Box, TextField, InputAdornment, IconButton } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import React from "react";

interface SearchBarProps {
  onSearch: (query: string) => void,
}

const SearchBar: React.FC<SearchBarProps> = ({onSearch}) => {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); // Prevent the default form submission behavior
    const input = new FormData(event.currentTarget).get("search") as string;

    onSearch(input);

    console.log("Search submitted:", input);
  };

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
      }}
    >
      <form
        style={{ display: "flex", width: "100%" }}
        onSubmit={handleSubmit}
      >
        <TextField
          name="search"
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
                  type="submit"
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
      </form>
    </Box>
  );
};

export default SearchBar;
