import { useState, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { mockPapers } from '@/data/mockPapers';
import { mockConversations } from '@/data/mockChats';
import { ChatConversation, ChatMessage } from '@/types/chat';
import { ChatSidebar } from '@/components/chat/ChatSidebar';
import { ChatHeader } from '@/components/chat/ChatHeader';
import { ChatArea } from '@/components/chat/ChatArea';
import { ChatInput } from '@/components/chat/ChatInput';
import { toast } from 'sonner';

export default function ChatScreen() {
  const { paperId } = useParams<{ paperId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const paper = mockPapers.find((p) => p.id === paperId);

  // Filter conversations for this paper
  const paperConversations = useMemo(
    () => mockConversations.filter((c) => c.paperId === paperId),
    [paperId]
  );

  const initialConvId = searchParams.get('conv');
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    initialConvId || null
  );

  // Local state for conversations (simulating persistence)
  const [conversations, setConversations] = useState<ChatConversation[]>(paperConversations);

  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  const handleNewChat = () => {
    const newConv: ChatConversation = {
      id: `conv-${Date.now()}`,
      paperId: paperId || '',
      paperTitle: paper?.title || 'Unknown Paper',
      title: 'New conversation',
      messages: [],
      lastUpdated: new Date().toISOString(),
      pdfUrl: paper?.pdfUrl || '',
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
  };

  const handleSendMessage = (content: string) => {
    if (!activeConversationId) {
      // Auto-create a new conversation
      const newConv: ChatConversation = {
        id: `conv-${Date.now()}`,
        paperId: paperId || '',
        paperTitle: paper?.title || 'Unknown Paper',
        title: content.slice(0, 40) + (content.length > 40 ? '...' : ''),
        messages: [],
        lastUpdated: new Date().toISOString(),
        pdfUrl: paper?.pdfUrl || '',
      };
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);

      // Add the user message
      setTimeout(() => {
        addMessageToConversation(newConv.id, content);
      }, 0);
      return;
    }

    addMessageToConversation(activeConversationId, content);
  };

  const addMessageToConversation = (convId: string, content: string) => {
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === convId
          ? {
              ...conv,
              messages: [...conv.messages, userMessage],
              lastUpdated: new Date().toISOString(),
              title:
                conv.messages.length === 0
                  ? content.slice(0, 40) + (content.length > 40 ? '...' : '')
                  : conv.title,
            }
          : conv
      )
    );

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: generateMockResponse(content),
        timestamp: new Date().toISOString(),
      };

      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === convId
            ? {
                ...conv,
                messages: [...conv.messages, aiMessage],
                lastUpdated: new Date().toISOString(),
              }
            : conv
        )
      );
    }, 1000);
  };

  const handleSummarize = () => {
    if (!activeConversation || activeConversation.messages.length === 0) {
      toast.info('No messages to summarize');
      return;
    }
    toast.success('Generating conversation summary...');
    
    const summaryMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: `**Conversation Summary**\n\nThis conversation covered ${activeConversation.messages.length} messages discussing "${activeConversation.paperTitle}". The main topics included:\n\n- Key findings and methodology\n- Practical applications\n- Technical implementation details\n\nThe discussion provided valuable insights into the paper's contributions to the field.`,
      timestamp: new Date().toISOString(),
    };

    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConversationId
          ? {
              ...conv,
              messages: [...conv.messages, summaryMessage],
              lastUpdated: new Date().toISOString(),
            }
          : conv
      )
    );
  };

  const handleOpenPdf = (url: string) => {
    window.open(url, '_blank');
  };

  const handleBack = () => {
    navigate(`/paper/${paperId}`);
  };

  if (!paper) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Paper not found</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-background">
      <ChatSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={setActiveConversationId}
        onNewChat={handleNewChat}
        onOpenPdf={handleOpenPdf}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <ChatHeader
          title={activeConversation?.title || paper.title}
          pdfUrl={paper.pdfUrl}
          onBack={handleBack}
          onSummarize={handleSummarize}
        />

        <ChatArea
          messages={activeConversation?.messages || []}
          paperTitle={paper.title}
        />

        <ChatInput onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
}

function generateMockResponse(userMessage: string): string {
  const lowerMessage = userMessage.toLowerCase();

  if (lowerMessage.includes('summary') || lowerMessage.includes('summarize')) {
    return "Based on the paper's content, here's a summary:\n\n**Main Contribution**: The paper introduces a novel approach that significantly advances the field.\n\n**Key Findings**:\n- Improved performance metrics over baseline methods\n- More efficient resource utilization\n- Broader applicability across domains\n\n**Methodology**: The authors employ rigorous experimental validation with multiple benchmarks.";
  }

  if (lowerMessage.includes('method') || lowerMessage.includes('approach')) {
    return "The methodology presented in this paper includes:\n\n1. **Data Collection**: Comprehensive dataset curation from multiple sources\n2. **Model Architecture**: Novel design choices that enable better representation learning\n3. **Training Strategy**: Efficient optimization techniques with careful hyperparameter tuning\n4. **Evaluation Protocol**: Rigorous testing on held-out datasets with statistical significance testing";
  }

  if (lowerMessage.includes('result') || lowerMessage.includes('finding')) {
    return "The paper reports several significant results:\n\n- **Accuracy**: 94.2% (+5.1% over baseline)\n- **Speed**: 3.8x faster inference time\n- **Memory**: 4x reduction in memory footprint\n\nThese improvements were consistent across all tested benchmarks and demonstrate the practical value of the proposed approach.";
  }

  return "That's an interesting question about the paper. Based on my analysis:\n\nThe paper addresses this topic by presenting a comprehensive framework that balances theoretical rigor with practical applicability. The authors provide detailed explanations and empirical evidence to support their claims.\n\nWould you like me to elaborate on any specific aspect?";
}
