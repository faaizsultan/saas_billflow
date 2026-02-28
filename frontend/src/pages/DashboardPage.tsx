import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { Activity, Clock, Layers } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { fetchAnalytics, fetchTraces } from "@/api/client"

const CATEGORIES = ["All", "Billing", "Refund", "Account Access", "Cancellation", "General Inquiry"]
const CATEGORY_COLORS: Record<string, string> = {
    "Billing": "#2563eb",
    "Refund": "#16a34a",
    "Account Access": "#d97706",
    "Cancellation": "#dc2626",
    "General Inquiry": "#9333ea",
}
const getCategoryColor = (cat: string) => CATEGORY_COLORS[cat] || "#888888"

export function DashboardPage() {
    const [selectedCategory, setSelectedCategory] = useState("All")
    const [expandedRow, setExpandedRow] = useState<string | null>(null)

    const { data: analytics, isLoading: analyticsLoading, isError: analyticsError } = useQuery({
        queryKey: ["analytics"],
        queryFn: fetchAnalytics,
        refetchInterval: 5000 // refresh every 5s for demo
    })

    const { data: traces, isLoading: tracesLoading, isError: tracesError } = useQuery({
        queryKey: ["traces", selectedCategory],
        queryFn: () => fetchTraces(selectedCategory),
        refetchInterval: 5000
    })

    return (
        <div className="container mx-auto max-w-6xl py-8 space-y-8">
            {/* Top Value Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card className="shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Traces</CardTitle>
                        <Layers className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {analyticsError ? "Error" : analyticsLoading ? "..." : analytics?.total_traces || 0}
                        </div>
                    </CardContent>
                </Card>

                <Card className="shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {analyticsError ? "Error" : analyticsLoading ? "..." : `${analytics?.average_response_time_ms || 0} ms`}
                        </div>
                    </CardContent>
                </Card>

                <Card className="shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">System Status</CardTitle>
                        <Activity className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${analyticsError ? "text-destructive" : "text-emerald-600"}`}>
                            {analyticsError ? "Degraded" : "Healthy"}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Analytics Chart */}
            <Card className="shadow-sm">
                <CardHeader>
                    <CardTitle>Trace Distribution by Category</CardTitle>
                </CardHeader>
                <CardContent className="h-[300px]">
                    {analyticsError ? (
                        <div className="h-full flex items-center justify-center text-destructive">Failed to load chart data. Ensure backend is running.</div>
                    ) : analyticsLoading ? (
                        <div className="h-full flex items-center justify-center text-muted-foreground">Loading chart...</div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={analytics?.category_breakdown || []} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                                <XAxis dataKey="category" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                                <Tooltip
                                    cursor={{ fill: 'transparent' }}
                                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                    {
                                        (analytics?.category_breakdown || []).map((_, index) => (
                                            <Cell key={`cell-${index}`} fill={getCategoryColor((analytics?.category_breakdown || [])[index].category)} />
                                        ))
                                    }
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </CardContent>
            </Card>

            {/* Traces Table with Filter */}
            <Card className="shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Recent Traces</CardTitle>
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground font-medium">Filter:</span>
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="px-3 py-1.5 bg-background border rounded-md text-sm outline-none focus:ring-2 focus:ring-primary/50"
                        >
                            {CATEGORIES.map(c => (
                                <option key={c} value={c}>{c}</option>
                            ))}
                        </select>
                    </div>
                </CardHeader>
                <CardContent>
                    {tracesError ? (
                        <div className="py-8 text-center text-destructive">Failed to load traces. Ensure backend is running.</div>
                    ) : tracesLoading ? (
                        <div className="py-8 text-center text-muted-foreground">Loading traces...</div>
                    ) : (
                        <div className="border rounded-md">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[180px]">Timestamp</TableHead>
                                        <TableHead>Category</TableHead>
                                        <TableHead className="max-w-[200px]">User Message</TableHead>
                                        <TableHead className="max-w-[200px]">Bot Response</TableHead>
                                        <TableHead className="text-right">Latency (ms)</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {traces?.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                                                No traces found for this category.
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        traces?.slice(0, 15).map((trace) => ( // Show only top 15 in this view to avoid massive scrolling
                                            <React.Fragment key={trace.id}>
                                                <TableRow className="cursor-pointer hover:bg-muted/50" onClick={() => setExpandedRow(prev => prev === trace.id ? null : trace.id)}>
                                                    <TableCell className="font-medium">
                                                        {new Date(trace.timestamp).toLocaleString()}
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant="outline" style={{ backgroundColor: getCategoryColor(trace.category), color: 'white', borderColor: getCategoryColor(trace.category) }}>
                                                            {trace.category}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="max-w-[200px] truncate text-muted-foreground" title={trace.user_message}>
                                                        {trace.user_message}
                                                    </TableCell>
                                                    <TableCell className="max-w-[200px] truncate text-muted-foreground" title={trace.bot_response}>
                                                        {trace.bot_response}
                                                    </TableCell>
                                                    <TableCell className="text-right font-mono">
                                                        {trace.response_time_ms}
                                                    </TableCell>
                                                </TableRow>
                                                {expandedRow === trace.id && (
                                                    <TableRow className="bg-muted/10">
                                                        <TableCell colSpan={5}>
                                                            <div className="p-4 space-y-4 text-sm animate-in fade-in duration-200">
                                                                <div>
                                                                    <span className="font-semibold text-primary">User Message:</span>
                                                                    <p className="mt-1 text-foreground bg-background p-3 rounded-md border shadow-sm">{trace.user_message}</p>
                                                                </div>
                                                                <div>
                                                                    <span className="font-semibold text-emerald-600">Bot Response:</span>
                                                                    <p className="mt-1 text-foreground bg-background p-3 rounded-md border shadow-sm whitespace-pre-wrap">{trace.bot_response}</p>
                                                                </div>
                                                            </div>
                                                        </TableCell>
                                                    </TableRow>
                                                )}
                                            </React.Fragment>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
