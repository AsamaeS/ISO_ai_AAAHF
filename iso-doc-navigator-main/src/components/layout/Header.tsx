import { Link } from "react-router-dom";
import { Shield, Menu, Plus, History, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

interface HeaderProps {
  onNewChat: () => void;
  conversations?: { id: string; title: string; created_at: string }[];
  onSelectConversation?: (id: string) => void;
  currentConversationId?: string;
}

export const Header = ({ 
  onNewChat, 
  conversations = [], 
  onSelectConversation,
  currentConversationId 
}: HeaderProps) => {
  return (
    <header className="sticky top-0 z-50 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="flex h-16 items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-3">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-80 bg-sidebar p-0">
              <SheetHeader className="p-4 border-b border-sidebar-border">
                <SheetTitle className="text-sidebar-foreground flex items-center gap-2">
                  <History className="h-4 w-4" />
                  Historique
                </SheetTitle>
              </SheetHeader>
              <div className="p-2 space-y-1">
                {conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => onSelectConversation?.(conv.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      currentConversationId === conv.id
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                    }`}
                  >
                    {conv.title}
                  </button>
                ))}
                {conversations.length === 0 && (
                  <p className="text-xs text-sidebar-foreground/60 px-3 py-2">
                    Aucune conversation
                  </p>
                )}
              </div>
            </SheetContent>
          </Sheet>

          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg gradient-primary">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-lg font-semibold text-foreground">ISO Compliance</h1>
              <p className="text-xs text-muted-foreground">Assistant IA</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/admin">
            <Button variant="ghost" size="icon" title="Administration">
              <Settings className="h-5 w-5" />
            </Button>
          </Link>
          <Button
            onClick={onNewChat}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">Nouvelle conversation</span>
          </Button>
        </div>
      </div>
    </header>
  );
};
