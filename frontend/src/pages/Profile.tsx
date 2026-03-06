import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { useUserData } from "@/context/UserDataContext";
import { createProfile, updateProfile, uploadAvatar } from "@/lib/api";
import type { Profile, ProfileUpdate } from "@/types/profile";
import { Upload, Save, X, ArrowLeft, Loader2 } from "lucide-react";

export default function Profile() {
  const { user, accessToken } = useAuth();
  const { profile, isLoading, updateProfileCache } = useUserData();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<ProfileUpdate>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (data: ProfileUpdate) => updateProfile(data, accessToken), // Since PUT might create if not exists
    onSuccess: (data) => {
      updateProfileCache(data);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Profile created successfully");
    },
    onError: (error) => {
      toast.error("Failed to create profile");
      console.error(error);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: ProfileUpdate) => {
      if (!profile) {
        return createProfile(data, accessToken);
      }
      return updateProfile(data, accessToken);
    },
    onSuccess: (data) => {
      updateProfileCache(data);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      setIsEditing(false);
      setFormData({});
      toast.success("Profile updated successfully");
    },
    onError: (error) => {
      toast.error("Failed to update profile");
      console.error(error);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadAvatar(file, accessToken),
    onSuccess: (data) => {
      updateProfileCache(data);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      setSelectedFile(null);
      setPreviewUrl(null);
      toast.success("Avatar uploaded successfully");
    },
    onError: (error) => {
      toast.error("Failed to upload avatar");
      console.error(error);
    },
  });

  const handleSave = () => {
    if (Object.keys(formData).length > 0) {
      updateMutation.mutate(formData);
    }
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormData({});
    setSelectedFile(null);
    setPreviewUrl(null);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const topicPreferences = profile?.topic_preferences
    ? profile.topic_preferences
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean)
    : [];

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((chunk) => chunk[0]?.toUpperCase())
        .join("")
    : (user?.username.slice(0, 2).toUpperCase() ?? "AR");

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
        <div className="max-w-2xl mx-auto">
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
                Profile Settings
                {!isEditing && (
                  <Button onClick={() => setIsEditing(true)}>
                    Edit Profile
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Avatar Section */}
              <div className="flex items-center space-x-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage
                    src={
                      previewUrl ||
                      profile?.avatar_url ||
                      `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username}`
                    }
                  />
                  <AvatarFallback>{initials}</AvatarFallback>
                </Avatar>
                {isEditing && (
                  <div>
                    <Label htmlFor="avatar-upload" className="cursor-pointer">
                      <div className="flex items-center space-x-2 px-4 py-2 border rounded-md hover:bg-muted">
                        <Upload className="h-4 w-4" />
                        <span>Upload Avatar</span>
                      </div>
                    </Label>
                    <Input
                      id="avatar-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </div>
                )}
              </div>

              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Full Name</Label>
                  <Input value={user?.full_name || ""} disabled />
                </div>
                <div>
                  <Label>Username</Label>
                  <Input value={user?.username || ""} disabled />
                </div>
              </div>

              <div>
                <Label>Email</Label>
                <Input value={user?.email || ""} disabled />
              </div>

              {isEditing ? (
                <>
                  <div>
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      value={formData.phone ?? profile?.phone ?? ""}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          phone: e.target.value,
                        }))
                      }
                      placeholder="Enter phone number"
                    />
                  </div>

                  <div>
                    <Label htmlFor="bio">Bio</Label>
                    <Textarea
                      id="bio"
                      value={formData.bio ?? profile?.bio ?? ""}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          bio: e.target.value,
                        }))
                      }
                      placeholder="Tell us about yourself"
                      rows={3}
                    />
                  </div>

                  <div>
                    <Label htmlFor="topics">Topic Preferences</Label>
                    <Textarea
                      id="topics"
                      value={
                        formData.topic_preferences ??
                        profile?.topic_preferences ??
                        ""
                      }
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          topic_preferences: e.target.value,
                        }))
                      }
                      placeholder="Enter topics separated by commas (e.g., cs.AI, cs.CL, stat.ML)"
                      rows={2}
                    />
                    <p className="text-sm text-muted-foreground mt-1">
                      Separate topics with commas. These will be used to
                      personalize your paper recommendations.
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <Label>Phone</Label>
                    <p className="text-sm text-muted-foreground">
                      {profile?.phone &&
                      profile.phone !== "string" &&
                      profile.phone !== "null"
                        ? profile.phone
                        : "Not provided"}
                    </p>
                  </div>

                  <div>
                    <Label>Bio</Label>
                    <p className="text-sm text-muted-foreground">
                      {profile?.bio &&
                      profile.bio !== "string" &&
                      profile.bio !== "null"
                        ? profile.bio
                        : "No bio yet"}
                    </p>
                  </div>

                  <div>
                    <Label>Topic Preferences</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {topicPreferences.length > 0 ? (
                        topicPreferences.map((topic) => (
                          <Badge key={topic} variant="secondary">
                            {topic}
                          </Badge>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No preferences set
                        </p>
                      )}
                    </div>
                  </div>
                </>
              )}

              {isEditing && (
                <div className="flex space-x-2 pt-4">
                  <Button
                    onClick={handleSave}
                    disabled={
                      updateMutation.isPending || uploadMutation.isPending
                    }
                  >
                    {updateMutation.isPending || uploadMutation.isPending ? (
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
