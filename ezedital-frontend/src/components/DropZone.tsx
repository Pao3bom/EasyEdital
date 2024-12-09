import { Box, Typography } from "@mui/material";
import React, { useState } from "react";

interface DropZoneProps {
  onDropped: (filePath: string) => void; // Function prop
}

const DropZone: React.FC<DropZoneProps> = ({ onDropped }) => {
  const [isDragging, setIsDragging] = useState(false);

  // const dataPath = '/home/pedrohenrique/Documents/GitHub/EasyEdital/data';
  const dataPath = 'data';

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

    // Retrieve the first file
    const file = event.dataTransfer.files[0];

    if (file) {
      const filePath = `${dataPath}/${file.name}`;
      console.log(filePath);
      onDropped(filePath); // Call the prop function with the first file's path
    }
  };

  return (
    <Box
      sx={{
        border: "2px dashed",
        borderColor: isDragging ? "primary.light" : "primary.main",
        borderRadius: "12px",
        padding: "32px",
        textAlign: "center",
        cursor: "pointer",
        backgroundColor: isDragging ? "background.default" : "background.paper",
        height: "100%",
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
          fontSize: "1.2rem",
        }}
      >
        {isDragging
          ? "Solte seu arquivo aqui"
          : "Ou simplesmente arraste seu arquivo aqui"}
      </Typography>
    </Box>
  );
};

export default DropZone;
