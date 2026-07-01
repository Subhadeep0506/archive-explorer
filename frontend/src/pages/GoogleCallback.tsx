import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import { apiRequest } from "@/lib/api";
import { AuthResponse } from "@/types/auth";
import { Loader2 } from "lucide-react";

export default function GoogleCallback() {
  const navigate = useNavigate();
  const { handleAuthResponse } = useAuth();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const storedState = sessionStorage.getItem("google_oauth_state");

      if (!code || !state) {
        toast.error("OAuth Error", {
          description: "Missing authorization code or state parameter.",
        });
        navigate("/", { replace: true });
        return;
      }

      if (state !== storedState) {
        toast.error("OAuth Error", {
          description: "State parameter mismatch. Please try again.",
        });
        navigate("/", { replace: true });
        return;
      }

      try {
        const response = await apiRequest<AuthResponse>(
          "/auth/google/callback",
          {
            params: { code, state },
            auth: false,
          },
        );

        handleAuthResponse(response);
        toast.success("Welcome!", {
          description: "Successfully signed in with Google.",
        });
        navigate("/app", { replace: true });
      } catch (error) {
        toast.error("Google Sign-in Failed", {
          description: error instanceof Error ? error.message : "Please try again.",
        });
        navigate("/", { replace: true });
      } finally {
        sessionStorage.removeItem("google_oauth_state");
      }
    };

    handleCallback();
  }, [searchParams, navigate, handleAuthResponse]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#05060d]">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin text-white mx-auto mb-4" />
        <p className="text-white/80">Signing you in with Google...</p>
      </div>
    </div>
  );
}
