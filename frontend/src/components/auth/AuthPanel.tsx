import { useState } from "react";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Loader2, Mail, UserRound, Lock, Eye, EyeOff } from "lucide-react";
import { LoginPayload, RegisterPayload } from "@/types/auth";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginValues = z.infer<typeof loginSchema>;

const registerSchema = loginSchema.extend({
  full_name: z.string().min(2, "Full name is required"),
  username: z.string().min(3, "Username must be at least 3 characters"),
});

type RegisterValues = z.infer<typeof registerSchema>;

type Mode = "login" | "register";

interface AuthPanelProps {
  onSuccess?: () => void;
}

export const AuthPanel = ({ onSuccess }: AuthPanelProps) => {
  const { login, register: registerUser, loginWithGoogle } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const loginForm = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const registerForm = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "", full_name: "", username: "" },
  });

  const handleModeChange = (nextMode: Mode) => {
    setMode(nextMode);
  };

  const handleLoginSubmit = async (values: LoginValues) => {
    setLoading(true);
    try {
      await login(values as LoginPayload);
      toast.success("Welcome back", { description: "You're signed in." });
      onSuccess?.();
    } catch (error) {
      toast.error("Unable to login", {
        description: error instanceof Error ? error.message : "Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (values: RegisterValues) => {
    setLoading(true);
    try {
      await registerUser(values as RegisterPayload);
      toast.success("Account created", { description: "You're all set!" });
      onSuccess?.();
    } catch (error) {
      toast.error("Registration failed", {
        description: error instanceof Error ? error.message : "Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 shadow-[0_25px_60px_rgba(15,23,42,0.35)]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/70">
            Access
          </p>
          <h3 className="text-2xl font-semibold text-white">Workspace</h3>
        </div>
        <div className="flex rounded-full bg-white/10 p-1">
          <button
            className={`px-3 py-1 text-xs font-semibold rounded-full transition ${
              mode === "login" ? "bg-white text-slate-900" : "text-white/70"
            }`}
            onClick={() => handleModeChange("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={`px-3 py-1 text-xs font-semibold rounded-full transition ${
              mode === "register" ? "bg-white text-slate-900" : "text-white/70"
            }`}
            onClick={() => handleModeChange("register")}
            type="button"
          >
            Join
          </button>
        </div>
      </div>

      {mode === "login" ? (
        <Form {...loginForm}>
          <form
            onSubmit={loginForm.handleSubmit(handleLoginSubmit)}
            className="space-y-4"
          >
            <FormField
              control={loginForm.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs text-white/80">Email</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                      <Input
                        {...field}
                        type="email"
                        className="bg-white/10 border-white/10 text-white placeholder:text-white/40 pl-9"
                      />
                    </div>
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />
            <FormField
              control={loginForm.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs text-white/80">
                    Password
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                      <Input
                        {...field}
                        type={showPassword ? "text" : "password"}
                        className="bg-white/10 border-white/10 text-white placeholder:text-white/40 pl-9 pr-9"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              className="w-full bg-white text-slate-900"
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Enter workspace"
              )}
            </Button>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-white/20" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white/5 px-2 text-white/60">Or</span>
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              className="w-full border-white/20 bg-white/5 text-white hover:bg-white/10"
              onClick={loginWithGoogle}
              disabled={loading}
            >
              Continue with Google
            </Button>
          </form>
        </Form>
      ) : (
        <Form {...registerForm}>
          <form
            onSubmit={registerForm.handleSubmit(handleRegisterSubmit)}
            className="space-y-4"
          >
            <FormField
              control={registerForm.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs text-white/80">
                    Full name
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <UserRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                      <Input
                        {...field}
                        className="bg-white/10 border-white/10 text-white placeholder:text-white/40 pl-9"
                      />
                    </div>
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />
            <FormField
              control={registerForm.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs text-white/80">
                    Username
                  </FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      className="bg-white/10 border-white/10 text-white placeholder:text-white/40"
                    />
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />
            <FormField
              control={registerForm.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs text-white/80">Email</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                      <Input
                        {...field}
                        type="email"
                        className="bg-white/10 border-white/10 text-white placeholder:text-white/40 pl-9"
                      />
                    </div>
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />
            <FormField
              control={registerForm.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs text-white/80">
                    Password
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                      <Input
                        {...field}
                        type={showPassword ? "text" : "password"}
                        className="bg-white/10 border-white/10 text-white placeholder:text-white/40 pl-9 pr-9"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              className="w-full bg-white text-slate-900"
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Create account"
              )}
            </Button>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-white/20" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white/5 px-2 text-white/60">Or</span>
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              className="w-full border-white/20 bg-white/5 text-white hover:bg-white/10"
              onClick={loginWithGoogle}
              disabled={loading}
            >
              Continue with Google
            </Button>
          </form>
        </Form>
      )}
    </div>
  );
};
