import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Index from "./pages/Index";
import PaperDetail from "./pages/PaperDetail";
import ChatScreen from "./pages/ChatScreen";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import SavedPapers from "./pages/SavedPapers";
import NotFound from "./pages/NotFound";
import Landing from "./pages/Landing";
import GoogleCallback from "./pages/GoogleCallback";
import { AuthProvider } from "@/context/AuthContext";
import { UserDataProvider } from "@/context/UserDataContext";
import { SearchProvider, useSearch } from "@/context/SearchContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { MainLayout } from "@/components/layout/MainLayout";

const queryClient = new QueryClient();

// Keyboard shortcuts component
const KeyboardShortcutsHandler = () => {
  const { setIsDialogOpen } = useSearch();
  const location = useLocation();

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K for search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        // Only open search on dashboard and saved papers
        if (location.pathname === '/app' || location.pathname === '/saved-papers') {
          setIsDialogOpen(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [setIsDialogOpen, location.pathname]);

  return null;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <AuthProvider>
          <UserDataProvider>
            <SearchProvider>
              <BrowserRouter>
                <KeyboardShortcutsHandler />
                <Routes>
                  <Route path="/" element={<Landing />} />
                  <Route
                    path="/auth/google/callback"
                    element={<GoogleCallback />}
                  />
                  <Route element={<ProtectedRoute />}>
                    {/* Pages with persistent navbar */}
                    <Route element={<MainLayout />}>
                      <Route path="/app" element={<Index />} />
                      <Route path="/saved-papers" element={<SavedPapers />} />
                      <Route path="/paper/:id" element={<PaperDetail />} />
                      <Route path="/profile" element={<Profile />} />
                      <Route path="/settings" element={<Settings />} />
                    </Route>
                    {/* Chat page without navbar */}
                    <Route
                      path="/paper/:paperId/chat"
                      element={<ChatScreen />}
                    />
                  </Route>
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </BrowserRouter>
            </SearchProvider>
          </UserDataProvider>
        </AuthProvider>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
