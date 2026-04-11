import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Globe,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AuthPanel } from "@/components/auth/AuthPanel";
import { useAuth } from "@/context/AuthContext";

const featureCards = [
  {
    title: "Intelligent paper discovery",
    description:
      "Subscribe to cross-domain feeds spanning CS, physics, mathematics, and beyond. New submissions surface automatically, ranked by relevance to your research profile.",
    icon: Globe,
  },
  {
    title: "AI-accelerated comprehension",
    description:
      "Generate structured summaries, extract key contributions, and surface related work — without opening a single PDF manually.",
    icon: Sparkles,
  },
  {
    title: "Secure personal library",
    description:
      "Annotations, conversation history, and uploaded manuscripts are stored privately and tied exclusively to your account.",
    icon: ShieldCheck,
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      navigate("/app", { replace: true });
    }
  }, [user, navigate]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#05060d] text-white">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-32 -left-16 h-72 w-72 rounded-full bg-[#7f5dff]/40 blur-[140px]" />
        <div className="absolute top-12 right-0 h-96 w-96 rounded-full bg-[#1dd1a1]/30 blur-[160px]" />
        <div className="absolute bottom-0 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-[#00d6ff]/20 blur-[140px]" />
      </div>

      <div className="relative z-10">
        <header className="flex items-center justify-between px-6 py-6 max-w-6xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-white/60">
                The Arxplorer
              </p>
              <h1 className="font-display text-xl tracking-tight">
                AI Powered Research Explorer
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              className="text-white/80 hover:text-white"
              onClick={() =>
                document
                  .getElementById("features")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Explore features
            </Button>
            <Button
              className="bg-white text-slate-900"
              onClick={() =>
                document
                  .getElementById("auth-panel")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Launch app
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-6 pb-24">
          <div className="grid gap-12 lg:grid-cols-[1.15fr_0.85fr] items-center">
            <div className="space-y-8">
              <h2 className="font-display text-4xl md:text-6xl leading-tight text-balance">
                Stay at the frontier without drowning in it.
              </h2>
              <p className="text-lg text-white/80 max-w-2xl">
                Arxplorer unifies paper discovery, structured summarisation, and
                document-grounded Q&amp;A into a single research environment —
                so you spend less time triaging and more time thinking.
              </p>
              <div className="flex flex-wrap gap-4">
                <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-4">
                  <p className="text-xs uppercase tracking-[0.3em] text-white/60">
                    Coverage
                  </p>
                  <p className="text-3xl font-semibold">1k+</p>
                  <p className="text-sm text-white/70">papers indexed monthly</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-4">
                  <p className="text-xs uppercase tracking-[0.3em] text-white/60">
                    Time to insight
                  </p>
                  <p className="text-3xl font-semibold">&lt; 30 s</p>
                  <p className="text-sm text-white/70">per structured summary</p>
                </div>
              </div>
            </div>
            <div
              id="auth-panel"
              className="lg:justify-self-end w-full max-w-md"
            >
              <AuthPanel
                onSuccess={() => navigate("/app", { replace: true })}
              />
            </div>
          </div>

          <section id="features" className="mt-24 space-y-8">
            <div className="flex items-center gap-4">
              <span className="h-px flex-1 bg-linear-to-r from-white/40 to-transparent" />
              <p className="text-xs uppercase tracking-[0.4em] text-white/60">
                Designed for rigorous research
              </p>
              <span className="h-px flex-1 bg-linear-to-l from-white/40 to-transparent" />
            </div>
            <div className="grid gap-6 md:grid-cols-3">
              {featureCards.map(({ title, description, icon: Icon }) => (
                <div
                  key={title}
                  className="group rounded-3xl border border-white/10 bg-white/5 p-6 transition hover:border-white/30 hover:bg-white/10"
                >
                  <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-white">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-display text-xl mb-3">{title}</h3>
                  <p className="text-sm text-white/80 leading-relaxed">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
