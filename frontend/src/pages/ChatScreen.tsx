import { useState, useMemo, useEffect, useRef } from "react";
import {
  useParams,
  useNavigate,
  useSearchParams,
  useLocation,
} from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ChatConversation,
  ChatMessage,
  Session,
  Message,
  SessionUpdate,
  StreamingNodeUpdate,
  StreamingState,
} from "@/types/chat";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatArea } from "@/components/chat/ChatArea";
import { ChatInput } from "@/components/chat/ChatInput";
import { Button } from "@/components/ui/button";
import { FileText, ExternalLink, X } from "lucide-react";
import type { ChatConfig } from "@/components/chat/ChatConfigPopover";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { fetchPaperById } from "@/lib/arxiv";
import { normalizeArxivEntry } from "@/lib/papers";
import { getSavedPapers } from "@/lib/api";
import type { Paper } from "@/types/paper";
import { Loader2 } from "lucide-react";
import {
  getSessions,
  createSession,
  getMessagesBySession,
  queryChatStream,
  updateSession,
  deleteSession,
  updateMessage,
} from "@/lib/api";

// Helper function to convert backend Message to UI ChatMessage
function convertMessageToChatMessage(msg: Message): ChatMessage[] {
  const messages: ChatMessage[] = [];

  // Extract generation metadata
  const metadata = msg.generation_metadata as
    | {
        completion_tokens?: number;
        prompt_tokens?: number;
        total_tokens?: number;
      }
    | null
    | undefined;

  // Handle both single content object and array of content
  if (Array.isArray(msg.content)) {
    // When content is an array (user-assistant pair from chat query)
    msg.content.forEach((item, index) => {
      messages.push({
        id: `${msg.id}-${index}`,
        role: item.role as "user" | "assistant",
        content: item.content,
        timestamp: msg.created_at,
        liked: msg.liked ?? undefined,
        feedback: msg.feedback ?? undefined,
        stars: msg.stars ?? undefined,
        generation_metadata: item.role === "assistant" ? metadata : undefined,
        sources: item.role === "assistant" ? msg.sources : undefined,
      });
    });
  } else {
    // When content is a single object
    messages.push({
      id: String(msg.id),
      role: msg.content.role as "user" | "assistant",
      content: msg.content.content,
      timestamp: msg.created_at,
      liked: msg.liked ?? undefined,
      feedback: msg.feedback ?? undefined,
      stars: msg.stars ?? undefined,
      generation_metadata:
        msg.content.role === "assistant" ? metadata : undefined,
      sources: msg.content.role === "assistant" ? msg.sources : undefined,
    });
  }

  return messages;
}

// Helper function to convert backend Session to UI ChatConversation
function convertSessionToConversation(
  session: Session,
  messages: Message[],
  paper?: Paper,
): ChatConversation {
  const chatMessages: ChatMessage[] = [];
  messages.forEach((msg) => {
    chatMessages.push(...convertMessageToChatMessage(msg));
  });

  return {
    id: String(session.id),
    paperId: String(session.paper_id),
    paperTitle: paper?.title || "Unknown Paper",
    title: session.title,
    messages: chatMessages,
    lastUpdated: session.started_at,
    pdfUrl: paper?.pdfUrl || "",
  };
}

export default function ChatScreen() {
  const { paperId } = useParams<{ paperId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();

  const statePaper = location.state?.paper as Paper | undefined;
  const { data, isLoading: isPaperLoading } = useQuery({
    queryKey: ["paper-chat", paperId],
    queryFn: () => fetchPaperById(paperId!, accessToken),
    enabled: Boolean(paperId && accessToken && !statePaper),
  });

  const paper = statePaper || (data ? normalizeArxivEntry(data) : undefined);

  // Fetch saved papers to get the paper_id (numeric ID from database)
  const { data: savedPapers } = useQuery({
    queryKey: ["savedPapers"],
    queryFn: () => getSavedPapers(accessToken),
    enabled: Boolean(accessToken && paper),
  });

  const savedPaper = savedPapers?.find((sp) => sp.arxiv_id === paperId);
  const paperDbId = savedPaper?.id;

  // Fetch all sessions for the user
  const { data: allSessions, isLoading: isSessionsLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => getSessions(accessToken),
    enabled: Boolean(accessToken),
  });

  // Filter sessions for this specific paper
  const paperSessions = useMemo(() => {
    if (!allSessions || !paperDbId) return [];
    return allSessions.filter((s) => s.paper_id === paperDbId);
  }, [allSessions, paperDbId]);

  const initialConvId = searchParams.get("conv");

  // Initialize active session from URL, sessionStorage, or null
  const [activeSessionId, setActiveSessionId] = useState<number | null>(() => {
    if (initialConvId) return parseInt(initialConvId);
    if (paperId) {
      const stored = sessionStorage.getItem(`chat-session-${paperId}`);
      return stored ? parseInt(stored) : null;
    }
    return null;
  });

  const [renamingSessionId, setRenamingSessionId] = useState<number | null>(
    null,
  );
  const [deletingSessionId, setDeletingSessionId] = useState<number | null>(
    null,
  );

  // Track if we've attempted session initialization to prevent duplicates
  const sessionInitialized = useRef(false);

  // Fetch messages for the active session
  const { data: messages, refetch: refetchMessages } = useQuery({
    queryKey: ["messages", activeSessionId],
    queryFn: () => getMessagesBySession(activeSessionId!, accessToken),
    enabled: Boolean(activeSessionId && accessToken),
  });

  // Convert sessions and messages to UI format
  const conversations = useMemo(() => {
    if (!paperSessions) return [];

    return paperSessions.map((session) => {
      const sessionMessages =
        activeSessionId === session.id ? messages || [] : [];
      return convertSessionToConversation(session, sessionMessages, paper);
    });
  }, [paperSessions, messages, activeSessionId, paper]);

  const activeConversation = conversations.find(
    (c) => c.id === String(activeSessionId),
  );

  // Auto-create session if none exists for this paper
  const createSessionMutation = useMutation({
    mutationFn: () =>
      createSession(
        {
          title: `Chat about ${paper?.title?.slice(0, 40) || "paper"}...`,
          paper_id: paperDbId!,
          started_at: new Date().toISOString().split("T")[0],
        },
        accessToken,
      ),
    onSuccess: (newSession) => {
      toast.success("New chat session created!");
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      setActiveSessionId(newSession.id);
    },
    onError: (error) => {
      toast.error(`Failed to create session: ${error.message}`);
    },
  });

  const updateSessionMutation = useMutation({
    mutationFn: ({
      sessionId,
      data,
    }: {
      sessionId: number;
      data: SessionUpdate;
    }) => updateSession(sessionId, data, accessToken),
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: number) => deleteSession(sessionId, accessToken),
  });

  // Persist active session to sessionStorage
  useEffect(() => {
    if (activeSessionId && paperId) {
      sessionStorage.setItem(
        `chat-session-${paperId}`,
        String(activeSessionId),
      );
    }
  }, [activeSessionId, paperId]);

  // Auto-create session on mount if none exists, or auto-select first session
  useEffect(() => {
    // Don't proceed if data is not ready or already initialized
    if (
      !paperDbId ||
      !paperSessions ||
      sessionInitialized.current ||
      isSessionsLoading
    )
      return;

    // Check if stored session exists in current sessions
    const storedSessionId = paperId
      ? sessionStorage.getItem(`chat-session-${paperId}`)
      : null;
    const storedSession = storedSessionId
      ? paperSessions.find((s) => s.id === parseInt(storedSessionId))
      : null;

    if (storedSession && !activeSessionId) {
      // Restore the stored session
      setActiveSessionId(storedSession.id);
      sessionInitialized.current = true;
    } else if (paperSessions.length === 0 && !createSessionMutation.isPending) {
      // No sessions exist, create one
      sessionInitialized.current = true;
      createSessionMutation.mutate();
    } else if (paperSessions.length > 0 && !activeSessionId) {
      // Sessions exist but none selected, select the first one
      setActiveSessionId(paperSessions[0].id);
      sessionInitialized.current = true;
    } else if (activeSessionId) {
      // Already have an active session
      sessionInitialized.current = true;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paperDbId, paperSessions, isSessionsLoading]);

  // Reset initialization flag when paper changes
  useEffect(() => {
    sessionInitialized.current = false;
  }, [paperId]);

  // State for streaming response
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [optimisticUserMessage, setOptimisticUserMessage] = useState("");
  const [streamingState, setStreamingState] = useState<StreamingState>({
    nodes: [],
    finalResponse: "",
  });

  // State for chat configuration
  const [chatConfig, setChatConfig] = useState<ChatConfig>({
    model: "qwen/qwen3-32b",
    temperature: 0.7,
    maxTokens: 2048,
    topK: 5,
  });

  const [useWebSearch, setUseWebSearch] = useState(false);

  // State for PDF sheet
  const [isPdfSheetOpen, setIsPdfSheetOpen] = useState(false);
  const [pdfSheetWidth, setPdfSheetWidth] = useState(40); // percentage of viewport width
  const [isResizing, setIsResizing] = useState(false);

  // Handle mouse resizing of PDF sheet
  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);

    const handleMouseMove = (moveEvent: MouseEvent) => {
      // Calculate width based on distance from right edge
      const distanceFromRight = window.innerWidth - moveEvent.clientX;
      const newWidthPercent = (distanceFromRight / window.innerWidth) * 100;
      // Constrain between 20% and 80%
      const constrainedWidth = Math.min(Math.max(newWidthPercent, 20), 80);
      setPdfSheetWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "ew-resize";
    document.body.style.userSelect = "none";
  };

  const handleNewChat = () => {
    setStreamingState({ nodes: [], finalResponse: "" });
    createSessionMutation.mutate();
  };

  const handleSelectConversation = (id: string) => {
    setStreamingState({ nodes: [], finalResponse: "" });
    setActiveSessionId(parseInt(id));
  };

  const handleSendMessage = async (content: string) => {
    if (!activeSessionId || !paperId) {
      toast.error("No active session");
      return;
    }

    try {
      // Clear previous streaming state before starting new message
      setStreamingState({ nodes: [], finalResponse: "" });

      // Optimistically add user message to UI
      setOptimisticUserMessage(content);
      setIsStreaming(true);
      setStreamingMessage("");

      const response = await queryChatStream(
        {
          query: content,
          paper_id: paperId,
          session_id: activeSessionId,
          model_name: chatConfig.model,
          temperature: chatConfig.temperature,
          max_tokens: chatConfig.maxTokens,
          top_k: chatConfig.topK,
          use_web_search: useWebSearch,
        },
        accessToken,
      );

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalResponse = "";

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            // Process any remaining data in buffer
            if (buffer.trim()) {
              processBufferedLines(buffer);
            }
            break;
          }

          // Decode chunk and add to buffer
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          // Process complete lines (ending with \n\n for SSE)
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            processBufferedLines(line);
          }
        }

        function processBufferedLines(line: string) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith("data: ")) return;

          try {
            const jsonStr = trimmedLine.slice(6).trim();
            if (!jsonStr) return;

            const parsed = JSON.parse(jsonStr);

            // Parse the streaming format: ["type", {...payload}]
            if (!Array.isArray(parsed) || parsed.length !== 2) {
              return;
            }

            const [messageType, payload] = parsed;

            // Handle "custom" type messages (progress updates)
            if (messageType === "custom" && payload.type && payload.message) {
              setStreamingState((prev) => {
                const existingNode = prev.nodes.find(
                  (n) => n.nodeName === payload.type,
                );

                if (existingNode) {
                  // Add message to existing node
                  return {
                    ...prev,
                    nodes: prev.nodes.map((n) =>
                      n.nodeName === payload.type
                        ? {
                            ...n,
                            messages: [...n.messages, payload.message],
                            timestamp: Date.now(),
                          }
                        : n,
                    ),
                  };
                } else {
                  // Create new node
                  const now = Date.now();
                  const newNode: StreamingNodeUpdate = {
                    id: `${payload.type}-${now}`,
                    type: "custom",
                    nodeName: payload.type,
                    displayName: payload.type,
                    timestamp: now,
                    startTime: now,
                    messages: [payload.message],
                  };
                  return {
                    ...prev,
                    nodes: [...prev.nodes, newNode],
                  };
                }
              });
            }

            // Handle "updates" type messages (node results)
            if (messageType === "updates") {
              const nodeKey = Object.keys(payload)[0]; // e.g., "context_retriever_node"
              const nodeData = payload[nodeKey];

              if (!nodeKey || !nodeData) return;

              setStreamingState((prev) => {
                const displayName = nodeKey
                  .replace(/_node$/, "")
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase());

                const existingNode = prev.nodes.find(
                  (n) => n.nodeName === nodeKey,
                );

                if (existingNode) {
                  // Update existing node with data and mark end time (only if not already set)
                  return {
                    ...prev,
                    nodes: prev.nodes.map((n) =>
                      n.nodeName === nodeKey
                        ? {
                            ...n,
                            type: "updates",
                            data: nodeData,
                            timestamp: Date.now(),
                            endTime: n.endTime || Date.now(),
                          }
                        : n,
                    ),
                  };
                } else {
                  // Create new node with updates - estimate start time based on previous node or 1s ago
                  const now = Date.now();
                  const lastNode = prev.nodes[prev.nodes.length - 1];
                  const estimatedStartTime = lastNode
                    ? lastNode.endTime || lastNode.timestamp
                    : now - 1000; // Fallback: assume 1 second duration

                  const newNode: StreamingNodeUpdate = {
                    id: `${nodeKey}-${now}`,
                    type: "updates",
                    nodeName: nodeKey,
                    displayName,
                    timestamp: now,
                    startTime: estimatedStartTime,
                    endTime: now,
                    messages: [],
                    data: nodeData,
                  };
                  return {
                    ...prev,
                    nodes: [...prev.nodes, newNode],
                  };
                }
              });

              // Extract final response if present
              if (nodeKey === "generate_response_node" && nodeData.response) {
                finalResponse = nodeData.response;
                setStreamingMessage(finalResponse);
                setStreamingState((prev) => ({
                  ...prev,
                  finalResponse: nodeData.response,
                  responseMetadata: nodeData.response_metadata,
                }));
              }
            }

            // Handle error responses (could be in different formats)
            if (
              (Array.isArray(parsed) && parsed[0] === "error") ||
              (typeof parsed === "object" &&
                !Array.isArray(parsed) &&
                "error" in parsed)
            ) {
              const errorMsg = Array.isArray(parsed)
                ? parsed[1]?.message || "Unknown error"
                : (parsed as { error: string }).error;
              throw new Error(errorMsg);
            }
          } catch (e) {
            if (
              e instanceof Error &&
              e.message !== "Unexpected end of JSON input"
            ) {
              console.error("Error parsing SSE data:", e);
              throw e;
            }
          }
        }

        // Ensure we got a response
        if (!finalResponse) {
          throw new Error("No response received from server");
        }

        // Refresh messages after successful query
        await refetchMessages();
      } finally {
        // Always cleanup, even if there was an error reading the stream
        reader.releaseLock();
        setStreamingMessage("");
        setOptimisticUserMessage("");
        setIsStreaming(false);
        // Note: We intentionally DON'T clear streamingState here
        // so that the node steps remain visible after streaming completes
      }
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error(
        `Failed to send message: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
      setIsStreaming(false);
      setStreamingMessage("");
      setStreamingState({ nodes: [], finalResponse: "" });
      setOptimisticUserMessage("");
    }
  };

  const handleSummarize = () => {
    toast.info("Summary feature coming soon!");
  };

  const handleBack = () => {
    navigate(`/paper/${paperId}`, { state: { paper } });
  };

  const handleRenameConversation = async (
    conversationId: string,
    title: string,
  ) => {
    const sessionId = Number(conversationId);
    const trimmedTitle = title.trim();

    if (!sessionId || !trimmedTitle) {
      throw new Error("A valid session title is required");
    }

    try {
      setRenamingSessionId(sessionId);
      await updateSessionMutation.mutateAsync({
        sessionId,
        data: { title: trimmedTitle },
      });
      toast.success("Session title updated");
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      toast.error(`Failed to rename session: ${message}`);
      throw error;
    } finally {
      setRenamingSessionId(null);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    const sessionId = Number(conversationId);
    if (!sessionId) {
      throw new Error("Invalid session selected");
    }

    try {
      setDeletingSessionId(sessionId);
      await deleteSessionMutation.mutateAsync(sessionId);
      toast.success("Session deleted");
      queryClient.invalidateQueries({ queryKey: ["sessions"] });

      if (activeSessionId === sessionId) {
        const remainingSessions = paperSessions.filter(
          (session) => session.id !== sessionId,
        );
        setStreamingState({ nodes: [], finalResponse: "" });
        setActiveSessionId(remainingSessions[0]?.id ?? null);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      toast.error(`Failed to delete session: ${message}`);
      throw error;
    } finally {
      setDeletingSessionId(null);
    }
  };

  const handleMessageLike = async (
    messageId: string,
    liked: boolean | null,
  ) => {
    // Skip optimistic/streaming messages
    if (
      messageId === "optimistic-user" ||
      messageId === "streaming" ||
      messageId === "final-response"
    ) {
      return;
    }

    try {
      await updateMessage(parseInt(messageId), { liked: liked }, accessToken);
      // Refresh messages to show updated like status
      await refetchMessages();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      toast.error(`Failed to update message: ${message}`);
    }
  };

  const handleMessageFeedback = async (
    messageId: string,
    feedback: string,
    stars: number,
  ) => {
    // Skip optimistic/streaming messages
    if (
      messageId === "optimistic-user" ||
      messageId === "streaming" ||
      messageId === "final-response"
    ) {
      return;
    }

    try {
      await updateMessage(
        parseInt(messageId),
        { feedback, stars },
        accessToken,
      );
      toast.success("Feedback submitted successfully");
      // Refresh messages to show updated feedback
      await refetchMessages();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      toast.error(`Failed to submit feedback: ${message}`);
    }
  };

  if (isPaperLoading || isSessionsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground">Paper not found</p>
      </div>
    );
  }

  // Create messages array including optimistic user message and streaming response
  const displayMessages = [...(activeConversation?.messages || [])];

  if (optimisticUserMessage) {
    displayMessages.push({
      id: "optimistic-user",
      role: "user",
      content: optimisticUserMessage,
      timestamp: new Date().toISOString(),
    });
  }

  if (isStreaming && streamingMessage) {
    displayMessages.push({
      id: "streaming",
      role: "assistant",
      content: streamingMessage,
      timestamp: new Date().toISOString(),
    });
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Global overlay during resize to prevent iframe from capturing events */}
      {isResizing && <div className="fixed inset-0 z-50 cursor-ew-resize" />}

      <ChatSidebar
        conversations={conversations}
        activeConversationId={
          typeof activeSessionId === "number" ? String(activeSessionId) : null
        }
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        onRenameConversation={handleRenameConversation}
        deletingConversationId={
          typeof deletingSessionId === "number"
            ? String(deletingSessionId)
            : null
        }
        renamingConversationId={
          typeof renamingSessionId === "number"
            ? String(renamingSessionId)
            : null
        }
        isLoadingSessions={isSessionsLoading}
        isCreatingSession={createSessionMutation.isPending}
      />

      <div
        className={`flex-1 flex flex-col min-w-0 ${!isResizing ? "transition-all duration-300" : ""}`}
        style={
          isPdfSheetOpen ? { marginRight: `${pdfSheetWidth}vw` } : undefined
        }
      >
        <ChatHeader
          title={activeConversation?.title || paper.title}
          pdfUrl={paper.pdfUrl || paper.htmlUrl || ""}
          onBack={handleBack}
          onSummarize={handleSummarize}
          onViewPdf={() => setIsPdfSheetOpen(true)}
        />

        <div className="flex-1 overflow-hidden relative">
          <ChatArea
            messages={displayMessages}
            paperTitle={paper.title}
            paperPdfUrl={paper.pdfUrl || paper.htmlUrl || ""}
            isStreaming={isStreaming}
            streamingState={streamingState}
            onMessageLike={handleMessageLike}
            onMessageFeedback={handleMessageFeedback}
          />

          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isStreaming || !activeSessionId}
            config={chatConfig}
            onConfigChange={setChatConfig}
            useWebSearch={useWebSearch}
            onWebSearchToggle={() => setUseWebSearch(!useWebSearch)}
          />
        </div>
      </div>

      {/* Global overlay during resize to prevent iframes from capturing mouse events */}
      {isResizing && <div className="fixed inset-0 z-50 cursor-ew-resize" />}

      {/* PDF Sheet */}
      <div
        className={`fixed top-0 right-0 h-full bg-background border-l transform ease-in-out z-40 ${
          isPdfSheetOpen ? "translate-x-0" : "translate-x-full"
        } ${!isResizing ? "transition-transform duration-300" : ""}`}
        style={{ width: `${pdfSheetWidth}vw` }}
      >
        {/* Resize Handle */}
        <div
          className="absolute left-0 top-0 bottom-0 w-1 hover:w-1.5 bg-border hover:bg-primary cursor-ew-resize transition-all z-10"
          onMouseDown={handleResizeStart}
          aria-label="Resize PDF panel"
        />

        <div className="flex flex-col h-full">
          <div className="flex items-center justify-end p-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            {/* <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-chip-coral" />
              <h2 className="font-semibold text-base">PDF Viewer</h2>
            </div> */}
            <div className="flex items-center gap-2">
              <a
                href={paper.pdfUrl || paper.htmlUrl || ""}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="ghost" size="sm">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Open Full PDF
                </Button>
              </a>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsPdfSheetOpen(false)}
                aria-label="Close PDF viewer"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>
          <div className="flex-1 bg-background overflow-auto">
            <iframe
              src={paper.pdfUrl || paper.htmlUrl || ""}
              className="w-full h-full border-0"
              title="PDF Viewer"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
