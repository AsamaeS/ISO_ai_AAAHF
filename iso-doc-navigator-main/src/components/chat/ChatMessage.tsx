import { FileText, BookOpen, Hash, FileCode } from "lucide-react";
import { cn } from "@/lib/utils";

interface Source {
  document: string;
  section: string;
  subsection: string;
  chunk_id: number;
  page: number | null;
}

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: Source[] | null;
  isLoading?: boolean;
}

export const ChatMessage = ({ role, content, sources, isLoading }: ChatMessageProps) => {
  if (isLoading) {
    return (
      <div className="flex justify-start animate-fade-in">
        <div className="assistant-message max-w-[85%]">
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex animate-fade-in",
        role === "user" ? "justify-end" : "justify-start"
      )}
    >
      <div className={cn("max-w-[85%] space-y-3")}>
        <div className={cn(role === "user" ? "user-message" : "assistant-message")}>
          <p className="whitespace-pre-wrap leading-relaxed">{content}</p>
        </div>

        {role === "assistant" && sources && sources.length > 0 && (
          <div className="space-y-2 pl-1">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <BookOpen className="h-3.5 w-3.5" />
              <span>Sources ISO</span>
            </div>
            <div className="grid gap-2">
              {sources.map((source, index) => (
                <div
                  key={index}
                  className="source-card text-sm"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-0.5">
                      <FileText className="h-4 w-4 text-source-accent" />
                    </div>
                    <div className="flex-1 min-w-0 space-y-1">
                      <p className="font-medium text-foreground truncate">
                        {source.document}
                      </p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <FileCode className="h-3 w-3" />
                          Section {source.section}
                        </span>
                        {source.subsection !== "N/A" && (
                          <span className="flex items-center gap-1">
                            Sous-section {source.subsection}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          Chunk #{source.chunk_id}
                        </span>
                        {source.page && (
                          <span>Page {source.page}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
