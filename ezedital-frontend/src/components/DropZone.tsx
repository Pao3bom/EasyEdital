import { Box, Typography } from "@mui/material";

const DropZone: React.FC = () => {
  return (
    <Box
      sx={{
        border: "2px dashed",
        borderColor: "primary.main",
        borderRadius: "12px",
        padding: "32px", // Enlarged
        textAlign: "center",
        cursor: "pointer",
        backgroundColor: "background.paper",
        height: "100%", // Full height within the box
        "&:hover": { backgroundColor: "background.default" },
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Typography
        variant="body1"
        sx={{
          color: "text.secondary",
          fontSize: "1.2rem", // Larger text for emphasis
        }}
      >
        Ou simplesmente arraste seus arquivos aqui
      </Typography>
    </Box>
  );
};

export default DropZone;
