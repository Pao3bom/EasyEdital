import { Box, AppBar, Toolbar, Typography } from "@mui/material";
import { Outlet } from "react-router-dom";

const Layout: React.FC = () => {
  return (
    <Box sx={{
      height: "100vh", // Ensures the layout fits within the viewport
      overflow: "hidden", // Prevents scrollbars from appearing
    }}>
      {/* <AppBar
        position="static"
        sx={{
          backgroundColor: "background.paper",
          color: "text.primary",
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: "bold",
            }}
          >
            Legal Search AI
          </Typography>
        </Toolbar>
      </AppBar> */}
      <Box sx={{
        // padding: "32px", 
        // marginTop: "16px", 
      }}>
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;
