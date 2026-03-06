import { Outlet } from "react-router-dom";
import { Navbar } from "@/components/Navbar";

/**
 * Main layout component that wraps pages with a persistent navbar.
 * The navbar remains visible during page transitions for a consistent UX.
 */
export const MainLayout = () => {
  return (
    <>
      <Navbar />
      <Outlet />
    </>
  );
};
