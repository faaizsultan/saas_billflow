import { useState, useRef, useEffect } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Send, Bot, User } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { createTrace, generateChat } from "@/api/client"

interface ChatMessage {
    id: string
    role: "user" | "bot"
    content: string
    category?: string
}

export function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([{
        id: 'initial',
        role: 'bot',
        content: "Hello! I'm the BillFlow Support Assistant. How can I help you today?"
    }])
    const [input, setInput] = useState("")
    const scrollRef = useRef<HTMLDivElement>(null)
    const queryClient = useQueryClient()

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [messages])

    const mutation = useMutation({
        mutationFn: async (userMsg: string) => {
            const chatResponse = await generateChat(userMsg)
            return await createTrace(userMsg, chatResponse.bot_response, chatResponse.response_time_ms)
        },
        onSuccess: (data) => {
            setMessages((prev) => [
                ...prev,
                {
                    id: data.id,
                    role: "bot",
                    content: data.bot_response,
                    category: data.category,
                },
            ])
            // Invalidate queries so dashboard data refreshes
            queryClient.invalidateQueries({ queryKey: ["traces"] })
            queryClient.invalidateQueries({ queryKey: ["analytics"] })
        },
        onError: () => {
            setMessages((prev) => [
                ...prev,
                {
                    id: Date.now().toString(),
                    role: "bot",
                    content: "Sorry, I encountered an error connecting to the server.",
                    category: "Error",
                },
            ])
        }
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || mutation.isPending) return

        const userMsg = input.trim()

        // Optimistically add user message
        setMessages((prev) => [
            ...prev,
            { id: Date.now().toString(), role: "user", content: userMsg },
        ])
        setInput("")

        mutation.mutate(userMsg)
    }

    return (
        <div className="container mx-auto max-w-4xl py-8">
            <Card className="flex flex-col h-[80vh] shadow-xl border-muted">
                <CardHeader className="border-b bg-muted/30">
                    <CardTitle className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-primary" />
                        SupportLens Chat
                    </CardTitle>
                </CardHeader>

                <CardContent className="flex-1 p-0 overflow-hidden">
                    <ScrollArea className="h-full p-4">
                        <div className="flex flex-col gap-4">
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={cn(
                                        "flex flex-col max-w-[80%] rounded-xl p-4 shadow-sm",
                                        msg.role === "user"
                                            ? "bg-primary text-primary-foreground self-end"
                                            : "bg-muted self-start"
                                    )}
                                >
                                    <div className="flex items-center gap-2 mb-1 opacity-80 text-xs font-medium">
                                        {msg.role === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                                        {msg.role === "user" ? "You" : "BillFlow Support"}
                                        {msg.category && (
                                            <span className="ml-auto bg-background/50 text-foreground px-2 py-0.5 rounded-full text-[10px]">
                                                {msg.category}
                                            </span>
                                        )}
                                    </div>
                                    <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                                </div>
                            ))}

                            {mutation.isPending && (
                                <div className="bg-muted self-start max-w-[80%] rounded-xl p-4 shadow-sm animate-pulse flex items-center gap-2">
                                    <Bot className="w-4 h-4" />
                                    <span className="text-sm">Bot is thinking...</span>
                                </div>
                            )}
                            <div ref={scrollRef} />
                        </div>
                    </ScrollArea>
                </CardContent>

                <CardFooter className="p-4 border-t bg-muted/10">
                    <form onSubmit={handleSubmit} className="flex w-full gap-2">
                        <Input
                            placeholder="Type your message..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={mutation.isPending}
                            className="flex-1"
                        />
                        <Button type="submit" disabled={!input.trim() || mutation.isPending}>
                            <Send className="w-4 h-4 mr-2" />
                            Send
                        </Button>
                    </form>
                </CardFooter>
            </Card>
        </div>
    )
}
