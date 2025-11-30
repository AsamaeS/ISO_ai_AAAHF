import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { Shield, AlertCircle } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: {
    document: string;
    section: string;
    subsection: string;
    chunk_id: number;
    page: number | null;
  }[] | null;
}

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  error?: string | null;
}

export const ChatContainer = ({ messages, isLoading, onSendMessage, error }: ChatContainerProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 px-4 py-6" ref={scrollRef}>
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-20 space-y-6 animate-fade-in">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl gradient-primary shadow-accent-glow">
                <Shield className="h-10 w-10 text-primary-foreground" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold text-foreground">
                  Assistant Conformité ISO
                </h2>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Posez vos questions sur les normes ISO. Chaque réponse inclut les sources précises pour garantir la traçabilité.
                </p>
              </div>
              <div className="grid gap-3 max-w-lg mx-auto">
                <ExamplePrompt onClick={onSendMessage}>
                  Quelles sont les exigences de la section 8.2.3 ?
                </ExamplePrompt>
                <ExamplePrompt onClick={onSendMessage}>
                  Comment documenter la revue des exigences clients ?
                </ExamplePrompt>
                <ExamplePrompt onClick={onSendMessage}>
                  Quels sont les critères d'audit interne ISO 9001 ?
                </ExamplePrompt>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              role={message.role}
              content={message.content}
              sources={message.sources}
            />
          ))}

          {isLoading && <ChatMessage role="assistant" content="" isLoading />}

          {error && (
            <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 text-destructive border border-destructive/20">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}
        </div>
      </ScrollArea>

      <ChatInput onSend={onSendMessage} isLoading={isLoading} />
    </div>
  );
};

const ExamplePrompt = ({ children, onClick }: { children: string; onClick: (msg: string) => void }) => (
  <button
    onClick={() => onClick(children)}
    className="text-left px-4 py-3 rounded-lg border border-border bg-card hover:bg-secondary/50 hover:border-accent/30 transition-all duration-200 text-sm text-muted-foreground hover:text-foreground"
  >
    {children}
  </button>
);
