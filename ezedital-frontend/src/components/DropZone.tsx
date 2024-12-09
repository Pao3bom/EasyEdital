import { Box, Typography } from "@mui/material";
import React, { useState } from "react";

const DropZone: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);

    // Retrieve the files
    const files = event.dataTransfer.files;

    if (files && files.length > 0) {
      console.log("Files dropped:", files);

      // Process files
      Array.from(files).forEach((file) => {
        console.log(`File name: ${file.name}`);
        // You can add file upload logic here
      });
    }
  };

  return (
    <Box
      sx={{
        border: "2px dashed",
        borderColor: isDragging ? "primary.light" : "primary.main",
        borderRadius: "12px",
        padding: "32px", // Enlarged
        textAlign: "center",
        cursor: "pointer",
        backgroundColor: isDragging ? "background.default" : "background.paper",
        height: "100%", // Full height within the box
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "background-color 0.3s, border-color 0.3s",
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <Typography
        variant="body1"
        sx={{
          color: "text.secondary",
          fontSize: "1.2rem", // Larger text for emphasis
        }}
      >
        {isDragging
          ? "Solte seus arquivos aqui"
          : "Ou simplesmente arraste seus arquivos aqui"}
      </Typography>
    </Box>
  );
};

export default DropZone;
