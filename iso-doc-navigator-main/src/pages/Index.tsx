import { Header } from "@/components/layout/Header";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { useChat } from "@/hooks/useChat";

const Index = () => {
  const { messages, isLoading, error, sendMessage, newChat } = useChat();

  return (
    <div className="flex flex-col h-screen gradient-hero">
      <Header onNewChat={newChat} />
      <main className="flex-1 overflow-hidden">
        <ChatContainer
          messages={messages}
          isLoading={isLoading}
          error={error}
          onSendMessage={sendMessage}
        />
      </main>
    </div>
  );
};

export default Index;
