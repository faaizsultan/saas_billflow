import { useState } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MessageSquare, LayoutDashboard } from "lucide-react"
import { ChatPage } from "./pages/ChatPage"
import { DashboardPage } from "./pages/DashboardPage"

const queryClient = new QueryClient()

export default function App() {
  const [view, setView] = useState<'chat' | 'dashboard'>('chat')

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background text-foreground flex flex-col">
        {/* Simple Navigation */}
        <header className="border-b bg-card shadow-sm sticky top-0 z-10">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <div className="font-bold text-xl flex items-center gap-2 text-primary">
              <MessageSquare className="w-6 h-6" />
              SupportLens
            </div>
            <nav className="flex gap-2">
              <button
                onClick={() => setView('chat')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${view === 'chat'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted text-muted-foreground'
                  }`}
              >
                <MessageSquare className="w-4 h-4" />
                Chat
              </button>
              <button
                onClick={() => setView('dashboard')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${view === 'dashboard'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted text-muted-foreground'
                  }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </button>
            </nav>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-hidden p-4">
          {view === 'chat' ? (
            <ChatPage />
          ) : (
            <DashboardPage />
          )}
        </main>
      </div>
    </QueryClientProvider>
  )
}
