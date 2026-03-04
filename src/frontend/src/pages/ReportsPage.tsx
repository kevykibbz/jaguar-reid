import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  Download,
  FileText,
  TrendingUp,
  Calendar,
  MapPin,
  Activity,
} from "lucide-react";
import {
  fetchJaguars,
  fetchStatistics,
  type JaguarImage,
} from "@/services/api";
import type { Statistics } from "@/types";

export function ReportsPage() {
  const [jaguars, setJaguars] = useState<JaguarImage[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const abortController = new AbortController();
    loadReportsData(abortController.signal);
    return () => abortController.abort();
  }, []);

  const loadReportsData = async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const [jaguarsData, statsData] = await Promise.all([
        fetchJaguars(undefined, undefined, signal),
        fetchStatistics(signal),
      ]);

      setJaguars(jaguarsData);
      setStatistics(statsData);
    } catch (error: any) {
      if (error.name !== "AbortError") {
        console.error("Error loading reports:", error);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const exportReport = (format: string) => {
    console.log(`Exporting report as ${format}`);
    // TODO: Implement actual export functionality
    alert(`Export as ${format} - Feature coming soon!`);
  };

  const averageSightingsPerJaguar =
    jaguars.length > 0
      ? (
          jaguars.reduce((sum, j) => sum + j.times_seen, 0) / jaguars.length
        ).toFixed(1)
      : "0.0";

  const mostActivePeriod = () => {
    if (jaguars.length === 0) return "N/A";
    const dates = jaguars.map((j) => new Date(j.last_seen).getMonth());
    const monthCounts = dates.reduce(
      (acc, month) => {
        acc[month] = (acc[month] || 0) + 1;
        return acc;
      },
      {} as Record<number, number>,
    );
    const mostActiveMonth = Object.entries(monthCounts).sort(
      (a, b) => b[1] - a[1],
    )[0];
    const monthNames = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    return monthNames[parseInt(mostActiveMonth[0])];
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center gap-4 px-4">
          <SidebarTrigger />
          <div className="flex-1">
            <h1 className="text-2xl font-bold">Reports & Analytics</h1>
            <p className="text-sm text-muted-foreground">
              Wildlife tracking insights and data export
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportReport("CSV")}
            >
              <Download className="h-4 w-4 mr-2" />
              CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportReport("PDF")}
            >
              <FileText className="h-4 w-4 mr-2" />
              PDF
            </Button>
          </div>
        </div>
      </header>

      <main className="container p-6 space-y-6">
        {/* Summary Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="grid gap-4 md:grid-cols-4"
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Population</CardTitle>
              <Activity className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? "..." : statistics?.total_jaguars || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Unique individuals
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Avg. Sightings
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? "..." : averageSightingsPerJaguar}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Per jaguar</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Most Active</CardTitle>
              <Calendar className="h-4 w-4 text-amber-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? "..." : mostActivePeriod()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Peak month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Database</CardTitle>
              <BarChart3 className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? "..." : statistics?.total_images || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Total images</p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Detailed Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Individual Tracking Report
              </CardTitle>
              <CardDescription>
                Detailed statistics for each identified jaguar
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="p-3 text-left text-sm font-medium">ID</th>
                      <th className="p-3 text-left text-sm font-medium">
                        Name
                      </th>
                      <th className="p-3 text-left text-sm font-medium">
                        First Seen
                      </th>
                      <th className="p-3 text-left text-sm font-medium">
                        Last Seen
                      </th>
                      <th className="p-3 text-right text-sm font-medium">
                        Sightings
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td
                          colSpan={5}
                          className="p-8 text-center text-muted-foreground"
                        >
                          Loading data...
                        </td>
                      </tr>
                    ) : jaguars.length === 0 ? (
                      <tr>
                        <td
                          colSpan={5}
                          className="p-8 text-center text-muted-foreground"
                        >
                          No jaguars recorded yet
                        </td>
                      </tr>
                    ) : (
                      jaguars.map((jaguar, idx) => (
                        <motion.tr
                          key={jaguar.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="border-b hover:bg-muted/30 transition-colors"
                        >
                          <td className="p-3 text-sm font-mono text-muted-foreground">
                            {jaguar.id}
                          </td>
                          <td className="p-3 text-sm font-medium">
                            {jaguar.name}
                          </td>
                          <td className="p-3 text-sm text-muted-foreground">
                            {formatDate(jaguar.first_seen)}
                          </td>
                          <td className="p-3 text-sm text-muted-foreground">
                            {formatDate(jaguar.last_seen)}
                          </td>
                          <td className="p-3 text-sm text-right font-medium">
                            <span className="inline-flex items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30 px-2.5 py-0.5 text-emerald-700 dark:text-emerald-400">
                              {jaguar.times_seen}
                            </span>
                          </td>
                        </motion.tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Insights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="grid gap-4 md:grid-cols-2"
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5 text-emerald-600" />
                Geographic Insights
              </CardTitle>
              <CardDescription>Location-based analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-muted-foreground">Coverage Areas</span>
                  <span className="font-medium">Coming Soon</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-muted-foreground">Hot Spots</span>
                  <span className="font-medium">Coming Soon</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-muted-foreground">Territory Range</span>
                  <span className="font-medium">Coming Soon</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                Behavioral Patterns
              </CardTitle>
              <CardDescription>Activity and movement analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-muted-foreground">
                    Peak Activity Times
                  </span>
                  <span className="font-medium">Coming Soon</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-muted-foreground">
                    Movement Patterns
                  </span>
                  <span className="font-medium">Coming Soon</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-muted-foreground">Seasonal Trends</span>
                  <span className="font-medium">Coming Soon</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  );
}
