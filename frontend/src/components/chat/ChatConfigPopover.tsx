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
import { useUserData } from "@/context/UserDataContext";
import { useMemo, useEffect, useRef } from "react";

export interface ChatConfig {
  model: string;
  modelSlug?: string;
  modelProvider?: string;
  temperature: number;
  maxTokens: number;
  topK: number;
}

interface ChatConfigPopoverProps {
  config: ChatConfig;
  onConfigChange: (config: ChatConfig) => void;
}

export function ChatConfigPopover({
  config,
  onConfigChange,
}: ChatConfigPopoverProps) {
  const { resources, settings } = useUserData();
  const hasSetDefaultModel = useRef(false);

  // Get user's API key service slugs
  const userApiKeyServices = useMemo(() => {
    if (!settings?.api_keys_encrypted) return new Set<string>();
    return new Set(settings.api_keys_encrypted.map((key) => key.slug));
  }, [settings]);

  // Convert resources to model options format, filtering by available API keys
  const availableModels = useMemo(() => {
    if (!resources || resources.length === 0) {
      // If no resources loaded, return empty array
      return [];
    }

    // Filter resources to only include those with matching API keys
    const filteredResources = resources.filter((resource) => {
      // If resource has a service_slug, check if user has API key for that service
      if (resource.service_slug) {
        return userApiKeyServices.has(resource.service_slug);
      }
      // If no service_slug, include it (for backward compatibility)
      return true;
    });

    return filteredResources.map((resource) => ({
      value: resource.service_slug
        ? `${resource.service_slug}/${resource.slug}`
        : resource.slug,
      label: resource.name,
      provider: resource.service_name || "Unknown",
      slug: resource.slug,
    }));
  }, [resources, userApiKeyServices]);

  // Auto-select first model from available models when they load (only once)
  useEffect(() => {
    if (availableModels.length > 0 && !hasSetDefaultModel.current) {
      // Check if current model exists in the available models
      const currentModelExists = availableModels.some(
        (model) => model.value === config.model,
      );

      // If current model doesn't exist, select the first one
      if (!currentModelExists) {
        hasSetDefaultModel.current = true;
        const firstModel = availableModels[0];
        onConfigChange({
          ...config,
          model: firstModel.value,
          modelSlug: firstModel.slug,
          modelProvider: firstModel.provider,
        });
      }
    }
  }, [availableModels, config, onConfigChange]);

  const handleModelChange = (value: string) => {
    const selectedModel = availableModels.find(
      (model) => model.value === value,
    );
    onConfigChange({
      ...config,
      model: value,
      modelSlug: selectedModel?.slug,
      modelProvider: selectedModel?.provider,
    });
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
      <PopoverContent className="w-80" align="start" side="bottom">
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
              {availableModels.length === 0 ? (
                <div className="rounded-md border border-border bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
                  No models available. Please add API keys in Settings.
                </div>
              ) : (
                <Select value={config.model} onValueChange={handleModelChange}>
                  <SelectTrigger id="model" className="h-auto">
                    <SelectValue>
                      {(() => {
                        const selected = availableModels.find(
                          (m) => m.value === config.model,
                        );
                        if (!selected) return "Select a model";
                        return (
                          <div className="flex flex-col items-start py-[0.1rem]">
                            <span className="font-medium">
                              {selected.label}
                            </span>
                            <span className="text-[1.6vh] text-muted-foreground text-left block">
                              {selected.provider} · {selected.slug}
                            </span>
                          </div>
                        );
                      })()}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent
                    position="popper"
                    side="right"
                    align="start"
                    sideOffset={5}
                    avoidCollisions={false}
                    className="max-h-[300px]"
                  >
                    {availableModels.map((model) => (
                      <SelectItem
                        key={model.value}
                        value={model.value}
                        className="h-auto py-2"
                      >
                        <div className="flex flex-col items-start">
                          <span className="font-medium">{model.label}</span>
                          <span className="text-[1.6vh] text-muted-foreground text-left block">
                            {model.provider} · {model.slug}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
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
