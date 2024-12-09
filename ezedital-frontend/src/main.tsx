import React from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import App from "./App";

const darkTheme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#9c27b0", // Purple for accents
    },
    background: {
      default: "#121212", // Dark background
      paper: "#1c1c1c",   // Slightly lighter background for containers
    },
    text: {
      primary: "#ffffff",
      secondary: "#bdbdbd", // Light gray for secondary text
    },
  },
  typography: {
    fontFamily: "'Roboto', 'Arial', sans-serif",
    h1: { fontWeight: 600 },
    h2: { fontWeight: 600 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    body1: { lineHeight: 1.6 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: "#9c27b0 #1c1c1c",
          "&::-webkit-scrollbar, & *::-webkit-scrollbar": {
            backgroundColor: "#1c1c1c",
            width: "8px",
            height: "8px",
          },
          "&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb": {
            borderRadius: "8px",
            backgroundColor: "#9c27b0",
            minHeight: "24px",
          },
          "&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover": {
            backgroundColor: "#d500f9",
          },
        },
      },
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
