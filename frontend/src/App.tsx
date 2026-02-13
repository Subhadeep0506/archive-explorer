import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import PaperDetail from "./pages/PaperDetail";
import ChatScreen from "./pages/ChatScreen";
import Profile from "./pages/Profile";
import SavedPapers from "./pages/SavedPapers";
import NotFound from "./pages/NotFound";
import Landing from "./pages/Landing";
import GoogleCallback from "./pages/GoogleCallback";
import { AuthProvider } from "@/context/AuthContext";
import { SearchProvider } from "@/context/SearchContext";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <SearchProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route
                path="/auth/google/callback"
                element={<GoogleCallback />}
              />
              <Route element={<ProtectedRoute />}>
                <Route path="/app" element={<Index />} />
                <Route path="/saved-papers" element={<SavedPapers />} />
                <Route path="/paper/:id" element={<PaperDetail />} />
                <Route path="/paper/:paperId/chat" element={<ChatScreen />} />
                <Route path="/profile" element={<Profile />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </SearchProvider>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
