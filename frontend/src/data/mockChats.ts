import { ChatConversation } from '@/types/chat';

export const mockConversations: ChatConversation[] = [
  {
    id: 'conv-1',
    paperId: '1',
    paperTitle: 'Scaling Laws for Neural Language Models',
    title: 'Understanding scaling laws',
    pdfUrl: 'https://arxiv.org/pdf/2001.08361',
    lastUpdated: '2024-01-15T10:30:00Z',
    messages: [
      {
        id: 'msg-1',
        role: 'user',
        content: 'What are the main findings about scaling laws in this paper?',
        timestamp: '2024-01-15T10:25:00Z',
      },
      {
        id: 'msg-2',
        role: 'assistant',
        content: 'The paper identifies three key factors that determine model performance:\n\n1. **Model Size (N)**: The number of parameters\n2. **Dataset Size (D)**: The amount of training data\n3. **Compute Budget (C)**: The computational resources used\n\nThe key finding is that performance scales as a power-law with each factor, with smooth and predictable relationships.',
        timestamp: '2024-01-15T10:25:30Z',
      },
      {
        id: 'msg-3',
        role: 'user',
        content: 'How does this apply to practical training decisions?',
        timestamp: '2024-01-15T10:28:00Z',
      },
      {
        id: 'msg-4',
        role: 'assistant',
        content: 'For practical applications, the scaling laws suggest:\n\n- **Fixed compute budget**: Balance model size and data size optimally\n- **Larger models are more sample-efficient**: They learn more from less data\n- **Predictable returns**: You can estimate performance gains before training\n\nThis helps researchers make informed decisions about resource allocation.',
        timestamp: '2024-01-15T10:30:00Z',
      },
    ],
  },
  {
    id: 'conv-2',
    paperId: '1',
    paperTitle: 'Scaling Laws for Neural Language Models',
    title: 'Compute efficiency discussion',
    pdfUrl: 'https://arxiv.org/pdf/2001.08361',
    lastUpdated: '2024-01-14T15:45:00Z',
    messages: [
      {
        id: 'msg-5',
        role: 'user',
        content: 'Is it more efficient to train a larger model for fewer steps or a smaller model for more steps?',
        timestamp: '2024-01-14T15:40:00Z',
      },
      {
        id: 'msg-6',
        role: 'assistant',
        content: 'According to the scaling laws, **larger models are more compute-efficient** when you have a fixed compute budget. Here\'s why:\n\n- Larger models achieve better performance per unit of compute\n- They converge faster to a given loss level\n- The optimal strategy is to train larger models for fewer steps\n\nHowever, this assumes you can afford the memory requirements of larger models.',
        timestamp: '2024-01-14T15:45:00Z',
      },
    ],
  },
  {
    id: 'conv-3',
    paperId: '2',
    paperTitle: 'Attention Is All You Need',
    title: 'Transformer architecture basics',
    pdfUrl: 'https://arxiv.org/pdf/1706.03762',
    lastUpdated: '2024-01-13T09:20:00Z',
    messages: [
      {
        id: 'msg-7',
        role: 'user',
        content: 'Can you explain the self-attention mechanism?',
        timestamp: '2024-01-13T09:15:00Z',
      },
      {
        id: 'msg-8',
        role: 'assistant',
        content: 'Self-attention allows the model to weigh the importance of different positions in the input sequence:\n\n1. **Query, Key, Value**: Each token generates three vectors\n2. **Attention Scores**: Computed as dot product of Query and Key\n3. **Weighted Sum**: Output is a weighted sum of Value vectors\n\nThis enables the model to capture long-range dependencies without recurrence.',
        timestamp: '2024-01-13T09:20:00Z',
      },
    ],
  },
];
