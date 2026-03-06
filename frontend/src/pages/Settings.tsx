import { useState, useEffect, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { useUserData } from "@/context/UserDataContext";
import { updateUserSettings } from "@/lib/api";
import type {
  UserSettingsUpdate,
  ApiKeyItem,
  ServiceCatalog,
} from "@/types/settings";
import {
  Save,
  X,
  ArrowLeft,
  Plus,
  Trash2,
  Key,
  Info,
  ExternalLink,
  Shield,
  Loader2,
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";

export default function Settings() {
  const { user, accessToken } = useAuth();
  const {
    settings,
    services,
    isLoading,
    refreshSettings,
    updateSettingsCache,
  } = useUserData();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<UserSettingsUpdate>({});
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [locationReadonly, setLocationReadonly] = useState(true);
  const locationInputRef = useRef<HTMLInputElement>(null);
  const [apiKeyReadonly, setApiKeyReadonly] = useState(true);
  const apiKeyInputRef = useRef<HTMLInputElement>(null);

  // For adding new API key
  const [selectedService, setSelectedService] = useState<ServiceCatalog | null>(
    null,
  );
  const [newApiKey, setNewApiKey] = useState("");

  // Initialize API keys from settings
  useEffect(() => {
    if (settings?.api_keys_encrypted) {
      setApiKeys(settings.api_keys_encrypted);
    }
  }, [settings]);

  // Prevent autofill by removing readonly after a short delay when editing starts
  useEffect(() => {
    if (isEditing) {
      setLocationReadonly(true);
      setApiKeyReadonly(true);
      const timer = setTimeout(() => {
        setLocationReadonly(false);
        setApiKeyReadonly(false);
        // Also focus the field to indicate it's ready
        if (locationInputRef.current) {
          locationInputRef.current.removeAttribute("readonly");
        }
        if (apiKeyInputRef.current) {
          apiKeyInputRef.current.removeAttribute("readonly");
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isEditing]);

  const updateMutation = useMutation({
    mutationFn: (data: UserSettingsUpdate) =>
      updateUserSettings(data, accessToken),
    onSuccess: (data) => {
      // Update both the cache and invalidate queries
      updateSettingsCache(data);
      queryClient.invalidateQueries({ queryKey: ["userSettings"] });
      setIsEditing(false);
      setFormData({});
      setLocationReadonly(true);
      setApiKeyReadonly(true);
      toast.success("Settings updated successfully");
    },
    onError: (error) => {
      toast.error("Failed to update settings");
      console.error(error);
    },
  });

  const handleSave = () => {
    const dataToSave: UserSettingsUpdate = {
      ...formData,
      api_keys_encrypted: apiKeys.length > 0 ? apiKeys : undefined,
    };

    updateMutation.mutate(dataToSave);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormData({});
    setLocationReadonly(true);
    setApiKeyReadonly(true);
    // Reset API keys to original
    if (settings?.api_keys_encrypted) {
      setApiKeys(settings.api_keys_encrypted);
    } else {
      setApiKeys([]);
    }
    setSelectedService(null);
    setNewApiKey("");
  };

  const handleAddApiKey = () => {
    if (!selectedService || !newApiKey.trim()) {
      toast.error("Please select a service and enter an API key");
      return;
    }

    // Check if service already exists
    const existingIndex = apiKeys.findIndex(
      (k) => k.slug === selectedService.slug,
    );

    if (existingIndex >= 0) {
      // Update existing
      const updated = [...apiKeys];
      updated[existingIndex] = {
        id: selectedService.id,
        slug: selectedService.slug,
        name: selectedService.name,
        api_key: newApiKey,
      };
      setApiKeys(updated);
      toast.success(`Updated API key for ${selectedService.name}`);
    } else {
      // Add new
      setApiKeys([
        ...apiKeys,
        {
          id: selectedService.id,
          slug: selectedService.slug,
          name: selectedService.name,
          api_key: newApiKey,
        },
      ]);
      toast.success(`Added API key for ${selectedService.name}`);
    }

    setSelectedService(null);
    setNewApiKey("");

    // Reset readonly state to prevent autofill on next entry
    setApiKeyReadonly(true);
    setTimeout(() => {
      setApiKeyReadonly(false);
      if (apiKeyInputRef.current) {
        apiKeyInputRef.current.removeAttribute("readonly");
      }
    }, 100);
  };

  const handleRemoveApiKey = (slug: string) => {
    setApiKeys(apiKeys.filter((k) => k.slug !== slug));
    toast.success("API key removed");
  };

  const maskApiKey = (key: string) => {
    // API keys are encrypted, so just show a secure representation
    return "••••••••••••••••••••••••";
  };

  // Group services by type
  const servicesByType =
    services?.reduce(
      (acc, service) => {
        if (!acc[service.service_type]) {
          acc[service.service_type] = [];
        }
        acc[service.service_type].push(service);
        return acc;
      },
      {} as Record<string, ServiceCatalog[]>,
    ) || {};

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => navigate("/app")}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                User Settings
                {!isEditing && (
                  <Button
                    onClick={() => {
                      setIsEditing(true);
                    }}
                  >
                    Edit Settings
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Location */}
              {isEditing ? (
                <div>
                  <Label htmlFor="location">Location</Label>
                  <Input
                    ref={locationInputRef}
                    id="location"
                    name="user-location-field"
                    type="text"
                    value={formData.location ?? settings?.location ?? ""}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        location: e.target.value,
                      }))
                    }
                    placeholder="e.g., San Francisco, CA"
                    autoComplete="off"
                    readOnly={locationReadonly}
                    data-lpignore="true"
                    data-form-type="other"
                  />
                </div>
              ) : (
                <div>
                  <Label htmlFor="location">Location</Label>
                  <p className="text-sm text-muted-foreground">
                    {settings?.location || "Not set"}
                  </p>
                </div>
              )}

              {/* Custom Summary Instructions */}
              {isEditing ? (
                <div>
                  <Label htmlFor="summary-instructions">
                    Custom Summary Instructions
                  </Label>
                  <Textarea
                    id="summary-instructions"
                    value={
                      formData.custom_summary_instructions ??
                      settings?.custom_summary_instructions ??
                      ""
                    }
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        custom_summary_instructions: e.target.value,
                      }))
                    }
                    placeholder="Provide custom instructions for how you want paper summaries generated..."
                    rows={3}
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    These instructions will be used when generating paper
                    summaries.
                  </p>
                </div>
              ) : (
                <div>
                  <Label htmlFor="summary-instructions">
                    Custom Summary Instructions
                  </Label>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {settings?.custom_summary_instructions ||
                      "No custom instructions set"}
                  </p>
                </div>
              )}

              {/* Usability Analysis Instructions */}
              {isEditing ? (
                <div>
                  <Label htmlFor="usability-instructions">
                    Usability Analysis Instructions
                  </Label>
                  <Textarea
                    id="usability-instructions"
                    value={
                      formData.usability_analysis_instructions ??
                      settings?.usability_analysis_instructions ??
                      ""
                    }
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        usability_analysis_instructions: e.target.value,
                      }))
                    }
                    placeholder="Provide custom instructions for usability analysis..."
                    rows={3}
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    These instructions will be used when analyzing paper
                    usability.
                  </p>
                </div>
              ) : (
                <div>
                  <Label htmlFor="usability-instructions">
                    Usability Analysis Instructions
                  </Label>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {settings?.usability_analysis_instructions ||
                      "No custom instructions set"}
                  </p>
                </div>
              )}

              {/* API Keys Section */}
              <div className="pt-6 border-t">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-1">
                      <h3 className="text-base font-medium">API Keys</h3>
                      <HoverCard>
                        <HoverCardTrigger asChild>
                          <button
                            type="button"
                            className="inline-flex items-center justify-center rounded-full p-1 hover:bg-muted transition-colors"
                          >
                            <Info className="h-4 w-4 text-muted-foreground" />
                          </button>
                        </HoverCardTrigger>
                        <HoverCardContent className="w-64 p-3" side="right">
                          <div className="space-y-1">
                            <h4 className="font-semibold text-xs mb-1.5">
                              Get Your API Keys
                            </h4>
                            <div className="space-y-0.5 text-xs">
                              <a
                                href="https://console.groq.com/keys"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between px-1.5 py-1 rounded hover:bg-muted transition-colors group"
                              >
                                <span className="font-medium">Groq</span>
                                <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-foreground" />
                              </a>
                              <a
                                href="https://langsearch.com/api-keys"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between px-1.5 py-1 rounded hover:bg-muted transition-colors group"
                              >
                                <span className="font-medium">LangSearch</span>
                                <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-foreground" />
                              </a>
                              <a
                                href="https://aistudio.google.com/api-keys"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between px-1.5 py-1 rounded hover:bg-muted transition-colors group"
                              >
                                <span className="font-medium">Gemini</span>
                                <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-foreground" />
                              </a>
                              <a
                                href="https://dashboard.cohere.com/api-keys"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between px-1.5 py-1 rounded hover:bg-muted transition-colors group"
                              >
                                <span className="font-medium">Cohere</span>
                                <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-foreground" />
                              </a>
                              <a
                                href="https://app.tavily.com/home"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between px-1.5 py-1 rounded hover:bg-muted transition-colors group"
                              >
                                <span className="font-medium">Tavily</span>
                                <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-foreground" />
                              </a>
                              <a
                                href="https://www.firecrawl.dev/app/api-keys"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center justify-between px-1.5 py-1 rounded hover:bg-muted transition-colors group"
                              >
                                <span className="font-medium">Firecrawl</span>
                                <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-foreground" />
                              </a>
                            </div>
                          </div>
                        </HoverCardContent>
                      </HoverCard>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Manage your API keys for external services
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="secondary"
                      className="flex items-center gap-1"
                    >
                      <Shield className="h-3 w-3" />
                      Encrypted
                    </Badge>
                    <Badge
                      variant="secondary"
                      className="flex items-center gap-1"
                    >
                      <Key className="h-3 w-3" />
                      {apiKeys.length} {apiKeys.length === 1 ? "key" : "keys"}
                    </Badge>
                  </div>
                </div>

                {isEditing && (
                  <div className="mb-4 p-4 border rounded-lg bg-muted/50">
                    <Label
                      htmlFor="service-select"
                      className="text-sm font-medium mb-2 block"
                    >
                      Add New API Key
                    </Label>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <Select
                        value={selectedService?.slug || ""}
                        onValueChange={(value) => {
                          const service = services?.find(
                            (s) => s.slug === value,
                          );
                          setSelectedService(service || null);
                        }}
                      >
                        <SelectTrigger id="service-select">
                          <SelectValue placeholder="Select service" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(servicesByType).map(
                            ([type, typeServices]) => (
                              <div key={type}>
                                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                                  {type.replace(/_/g, " ").toUpperCase()}
                                </div>
                                {typeServices.map((service) => (
                                  <SelectItem
                                    key={service.slug}
                                    value={service.slug}
                                  >
                                    {service.name}
                                  </SelectItem>
                                ))}
                              </div>
                            ),
                          )}
                        </SelectContent>
                      </Select>
                      <Input
                        ref={apiKeyInputRef}
                        id="new-api-key"
                        name="api-key-input-field"
                        type="password"
                        placeholder="Enter API key"
                        value={newApiKey}
                        onChange={(e) => setNewApiKey(e.target.value)}
                        autoComplete="off"
                        readOnly={apiKeyReadonly}
                        data-lpignore="true"
                        data-form-type="other"
                        data-1p-ignore="true"
                      />
                      <Button onClick={handleAddApiKey} className="w-full">
                        <Plus className="h-4 w-4 mr-2" />
                        Add
                      </Button>
                    </div>
                  </div>
                )}

                {/* API Keys List */}
                <div className="space-y-2">
                  {apiKeys.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No API keys configured yet
                    </p>
                  ) : (
                    apiKeys.map((keyItem) => (
                      <div
                        key={keyItem.slug}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{keyItem.name}</p>
                            <Badge variant="outline" className="text-xs">
                              {keyItem.slug}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <p className="text-sm text-muted-foreground font-mono">
                              {maskApiKey(keyItem.api_key)}
                            </p>
                            <Badge variant="outline" className="text-xs">
                              <Shield className="h-3 w-3 mr-1" />
                              Secured
                            </Badge>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {isEditing && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveApiKey(keyItem.slug)}
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {isEditing && (
                <div className="flex space-x-2 pt-4 border-t">
                  <Button
                    onClick={handleSave}
                    disabled={updateMutation.isPending}
                  >
                    {updateMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={handleCancel}>
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
