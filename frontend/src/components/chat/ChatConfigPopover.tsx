import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

export interface ChatConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  topK: number;
}

interface ChatConfigPopoverProps {
  config: ChatConfig;
  onConfigChange: (config: ChatConfig) => void;
}

const AVAILABLE_MODELS = [
  { value: "qwen/qwen3-32b", label: "Qwen 3 32B" },
  { value: "openai/gpt-oss-120b", label: "GPT OSS 120B" },
  { value: "openai/gpt-oss-20b", label: "GPT OSS 20B" },
  { value: "groq/compound", label: "Groq Compound" },
  { value: "groq/compound-mini", label: "Groq Compound Mini" },
  {
    value: "meta-llama/llama-4-scout-17b-16e-instruct",
    label: "Llama 4 Scout 17B",
  },
  { value: "moonshotai/kimi-k2-instruct-0905", label: "Kimi K2 Instruct" },
  { value: "llama-3.1-8b-instant", label: "Llama 3.1 8B Instant" },
  { value: "llama-3.3-70b-versatile", label: "Llama 3.3 70B Versatile" },
];

export function ChatConfigPopover({
  config,
  onConfigChange,
}: ChatConfigPopoverProps) {
  const handleModelChange = (value: string) => {
    onConfigChange({ ...config, model: value });
  };

  const handleTemperatureChange = (value: number[]) => {
    onConfigChange({ ...config, temperature: value[0] });
  };

  const handleMaxTokensChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    if (!isNaN(value) && value > 0) {
      onConfigChange({ ...config, maxTokens: value });
    }
  };

  const handleTopKChange = (value: number[]) => {
    onConfigChange({ ...config, topK: value[0] });
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          type="button"
          title="Configure response settings"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start" side="top">
        <div className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Response Configuration</h4>
            <p className="text-xs text-muted-foreground">
              Customize the AI model and generation parameters
            </p>
          </div>

          <div className="space-y-3">
            {/* Model Selection */}
            <div className="space-y-2">
              <Label htmlFor="model" className="text-xs">
                Model
              </Label>
              <Select value={config.model} onValueChange={handleModelChange}>
                <SelectTrigger id="model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label htmlFor="temperature" className="text-xs">
                  Temperature
                </Label>
                <span className="text-xs text-muted-foreground">
                  {config.temperature.toFixed(2)}
                </span>
              </div>
              <Slider
                id="temperature"
                min={0}
                max={2}
                step={0.1}
                value={[config.temperature]}
                onValueChange={handleTemperatureChange}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Higher values make output more random
              </p>
            </div>

            {/* Max Tokens */}
            <div className="space-y-2">
              <Label htmlFor="maxTokens" className="text-xs">
                Max Tokens
              </Label>
              <Input
                id="maxTokens"
                type="number"
                min={1}
                max={8192}
                value={config.maxTokens}
                onChange={handleMaxTokensChange}
                className="h-8"
              />
              <p className="text-xs text-muted-foreground">
                Maximum length of the response
              </p>
            </div>

            {/* Top K */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label htmlFor="topK" className="text-xs">
                  Top K (Context)
                </Label>
                <span className="text-xs text-muted-foreground">
                  {config.topK}
                </span>
              </div>
              <Slider
                id="topK"
                min={1}
                max={20}
                step={1}
                value={[config.topK]}
                onValueChange={handleTopKChange}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Number of relevant document chunks to retrieve
              </p>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
