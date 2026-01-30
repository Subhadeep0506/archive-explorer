import { useParams, Link, useNavigate } from 'react-router-dom';
import { mockPapers } from '@/data/mockPapers';
import { Navbar } from '@/components/Navbar';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ArrowLeft,
  Calendar,
  Building2,
  MapPin,
  Users,
  FileText,
  Globe,
  Github,
  Sparkles,
  Copy,
  ExternalLink,
  MessageCircle,
} from 'lucide-react';
import { toast } from 'sonner';

export default function PaperDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const paper = mockPapers.find((p) => p.id === id);

  if (!paper) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto py-12 text-center">
          <h1 className="text-2xl font-bold mb-4">Paper not found</h1>
          <Link to="/">
            <Button>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const formattedDate = new Date(paper.date).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const aiSummary = `## Key Findings

This research presents significant advancements in the field with several notable contributions:

### Main Contributions
1. **Novel Architecture**: The paper introduces a new approach that improves upon existing methods by optimizing key computational bottlenecks.
2. **Empirical Validation**: Extensive experiments demonstrate the effectiveness of the proposed method across multiple benchmark datasets.
3. **Practical Applications**: The work has direct implications for real-world deployment in production systems.

### Methodology
The authors employ a combination of theoretical analysis and empirical evaluation to validate their claims. The experimental setup includes:
- Multiple baseline comparisons
- Ablation studies to understand component contributions
- Statistical significance testing

### Results Summary
| Metric | Proposed | Baseline | Improvement |
|--------|----------|----------|-------------|
| Accuracy | 94.2% | 89.1% | +5.1% |
| Speed | 2.3ms | 8.7ms | 3.8x faster |
| Memory | 512MB | 2.1GB | 4x reduction |

### Limitations
The authors acknowledge certain limitations including dataset-specific optimizations and the need for further validation on edge cases.

### Future Directions
The paper suggests several promising research directions for future work, including scaling to larger models and exploring cross-domain applications.`;

  const handleCopyBibtex = () => {
    const bibtex = `@article{${paper.authors[0]?.split(' ')[1]?.toLowerCase() || 'author'}${paper.date.slice(0, 4)},
  title={${paper.title}},
  author={${paper.authors.join(' and ')}},
  year={${paper.date.slice(0, 4)}},
  institution={${paper.institution}}
}`;
    navigator.clipboard.writeText(bibtex);
    toast.success('BibTeX copied to clipboard!');
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto py-6 px-4">
        <Link to="/" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Paper Preview - Left Side */}
          <div className="lg:col-span-3 space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl lg:text-3xl font-bold leading-tight mb-4">
                {paper.title}
              </h1>

              <div className="flex flex-wrap gap-2 mb-4">
                {paper.topics.map((topic) => (
                  <Badge key={topic} variant="secondary">
                    {topic}
                  </Badge>
                ))}
              </div>

              <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-6">
                <span className="flex items-center gap-1.5">
                  <Users className="w-4 h-4" />
                  {paper.authors.join(', ')}
                </span>
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4" />
                  {paper.institution}
                </span>
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4" />
                  {paper.country}
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4" />
                  {formattedDate}
                </span>
              </div>

              <div className="flex flex-wrap gap-3 mb-6">
                <Button 
                  onClick={() => navigate(`/paper/${id}/chat`)}
                  className="bg-chip-violet hover:bg-chip-violet/90"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Chat with Paper
                </Button>
                <a href={paper.pdfUrl} target="_blank" rel="noopener noreferrer">
                  <Button className="bg-chip-coral hover:bg-chip-coral/90">
                    <FileText className="w-4 h-4 mr-2" />
                    View PDF
                    <ExternalLink className="w-3 h-3 ml-2" />
                  </Button>
                </a>
                {paper.htmlUrl && (
                  <a href={paper.htmlUrl} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" className="border-chip-blue text-chip-blue hover:bg-chip-blue hover:text-white">
                      <Globe className="w-4 h-4 mr-2" />
                      HTML Version
                    </Button>
                  </a>
                )}
                {paper.githubUrl && (
                  <a href={paper.githubUrl} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" className="border-chip-emerald text-chip-emerald hover:bg-chip-emerald hover:text-white">
                      <Github className="w-4 h-4 mr-2" />
                      Source Code
                    </Button>
                  </a>
                )}
                <Button variant="outline" onClick={handleCopyBibtex}>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy BibTeX
                </Button>
              </div>
            </div>

            {/* Paper Preview Embed */}
            <Card className="animate-fade-in" style={{ animationDelay: '0.1s', opacity: 0 }}>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Paper Preview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="aspect-[3/4] bg-muted rounded-lg flex items-center justify-center">
                  <div className="text-center p-8">
                    <div className="w-24 h-32 mx-auto mb-4 bg-background rounded-lg shadow-lg flex items-center justify-center border">
                      <FileText className="w-12 h-12 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground mb-4">PDF Preview</p>
                    <a href={paper.pdfUrl} target="_blank" rel="noopener noreferrer">
                      <Button size="sm">
                        Open Full PDF
                        <ExternalLink className="w-3 h-3 ml-2" />
                      </Button>
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Abstract */}
            <Card className="animate-fade-in" style={{ animationDelay: '0.15s', opacity: 0 }}>
              <CardHeader>
                <CardTitle className="text-lg">Abstract</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed">{paper.abstract}</p>
              </CardContent>
            </Card>
          </div>

          {/* AI Summary - Right Side */}
          <div className="lg:col-span-2">
            <Card className="sticky top-24 animate-slide-in-right" style={{ opacity: 0 }}>
              <CardHeader className="border-b bg-gradient-to-r from-chip-violet-bg to-chip-blue-bg">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Sparkles className="w-5 h-5 text-chip-violet" />
                  AI-Generated Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 max-h-[calc(100vh-12rem)] overflow-y-auto scrollbar-thin">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {aiSummary.split('\n').map((line, index) => {
                    if (line.startsWith('## ')) {
                      return <h2 key={index} className="text-lg font-bold mt-4 mb-2 text-foreground">{line.replace('## ', '')}</h2>;
                    }
                    if (line.startsWith('### ')) {
                      return <h3 key={index} className="text-base font-semibold mt-3 mb-1 text-foreground">{line.replace('### ', '')}</h3>;
                    }
                    if (line.startsWith('| ')) {
                      return (
                        <div key={index} className="text-sm text-muted-foreground font-mono bg-muted/50 px-2 py-0.5 rounded">
                          {line}
                        </div>
                      );
                    }
                    if (line.startsWith('1. ') || line.startsWith('2. ') || line.startsWith('3. ')) {
                      const [num, ...rest] = line.split('. ');
                      const content = rest.join('. ');
                      const boldMatch = content.match(/\*\*(.*?)\*\*(.*)/);
                      if (boldMatch) {
                        return (
                          <p key={index} className="text-sm text-muted-foreground my-1 ml-4">
                            {num}. <strong className="text-foreground">{boldMatch[1]}</strong>{boldMatch[2]}
                          </p>
                        );
                      }
                      return <p key={index} className="text-sm text-muted-foreground my-1 ml-4">{line}</p>;
                    }
                    if (line.startsWith('- ')) {
                      return <p key={index} className="text-sm text-muted-foreground my-1 ml-6">{line}</p>;
                    }
                    if (line.trim() === '') {
                      return <div key={index} className="h-2" />;
                    }
                    return <p key={index} className="text-sm text-muted-foreground my-2">{line}</p>;
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
