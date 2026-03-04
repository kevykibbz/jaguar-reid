import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Activity,
  TrendingUp,
  Camera,
  MapPin,
  Calendar,
  Clock,
  ChevronLeft,
  ChevronRight,
  Eye,
  Cpu,
} from "lucide-react";
import {
  fetchStatistics,
  fetchRecentActivity,
  fetchJaguars,
} from "@/services/api";
import type { Statistics, Activity as ActivityType, Jaguar } from "@/types";

export function DashboardPage() {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [recentActivity, setRecentActivity] = useState<ActivityType[]>([]);
  const [jaguars, setJaguars] = useState<Jaguar[]>([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const abortController = new AbortController();
    loadDashboardData(abortController.signal);
    return () => abortController.abort();
  }, []);

  const loadDashboardData = async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const [stats, activity, jaguarsData] = await Promise.all([
        fetchStatistics(signal),
        fetchRecentActivity(10, signal),
        fetchJaguars(undefined, undefined, signal),
      ]);

      setStatistics(stats);
      setRecentActivity(activity);
      setJaguars(jaguarsData.slice(0, 5)); // Show top 5 jaguars
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
        console.error("Error loading dashboard:", error);
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
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % jaguars.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + jaguars.length) % jaguars.length);
  };

  // Auto-play slider
  useEffect(() => {
    if (jaguars.length === 0) return;
    const interval = setInterval(nextSlide, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jaguars.length]);

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center gap-4 px-4">
          <SidebarTrigger />
          <div className="flex-1">
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              Wildlife monitoring overview
            </p>
          </div>
        </div>
      </header>

      <main className="container p-6 space-y-6">
        {/* Featured Jaguars Slider */}
        {!loading && jaguars.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Card className="overflow-hidden border-0 shadow-2xl">
              <div className="relative h-[400px] bg-black">
                <AnimatePresence mode="wait">
                  {jaguars[currentSlide] &&
                    jaguars[currentSlide].images?.[0] && (
                      <motion.div
                        key={currentSlide}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.5 }}
                        className="absolute inset-0"
                      >
                        <img
                          src={jaguars[currentSlide].images[0].url}
                          alt={jaguars[currentSlide].name}
                          className="w-full h-full object-cover"
                        />
                        {/* Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />

                        {/* Info Overlay */}
                        <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
                          <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                          >
                            <div className="flex items-center gap-3 mb-3">
                              <span className="px-3 py-1 bg-emerald-500/90 backdrop-blur-sm rounded-full text-xs font-semibold">
                                {jaguars[currentSlide].id}
                              </span>
                              <span className="px-3 py-1 bg-blue-500/90 backdrop-blur-sm rounded-full text-xs font-semibold flex items-center gap-1">
                                <Cpu className="h-3 w-3" />
                                AI Identified
                              </span>
                            </div>
                            <h2 className="text-3xl font-bold mb-2">
                              {jaguars[currentSlide].name}
                            </h2>
                            <div className="flex items-center gap-6 text-sm">
                              <div className="flex items-center gap-2">
                                <Eye className="h-4 w-4" />
                                <span>
                                  {jaguars[currentSlide].times_seen} sightings
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Calendar className="h-4 w-4" />
                                <span>
                                  Last seen:{" "}
                                  {new Date(
                                    jaguars[currentSlide].last_seen,
                                  ).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                          </motion.div>
                        </div>

                        {/* Navigation Arrows */}
                        <button
                          onClick={prevSlide}
                          className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-sm flex items-center justify-center transition-all"
                        >
                          <ChevronLeft className="h-6 w-6 text-white" />
                        </button>
                        <button
                          onClick={nextSlide}
                          className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-sm flex items-center justify-center transition-all"
                        >
                          <ChevronRight className="h-6 w-6 text-white" />
                        </button>

                        {/* Slide Indicators */}
                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                          {jaguars.map((_, idx) => (
                            <button
                              key={idx}
                              onClick={() => setCurrentSlide(idx)}
                              className={`h-2 rounded-full transition-all ${
                                idx === currentSlide
                                  ? "w-8 bg-white"
                                  : "w-2 bg-white/50 hover:bg-white/70"
                              }`}
                            />
                          ))}
                        </div>
                      </motion.div>
                    )}
                </AnimatePresence>
              </div>
            </Card>
          </motion.div>
        )}

        {/* Statistics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="grid gap-4 md:grid-cols-3"
        >
          <Card className="border-emerald-200 dark:border-emerald-900 bg-gradient-to-br from-emerald-50 to-background dark:from-emerald-950/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Jaguars
              </CardTitle>
              <Activity className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-700 dark:text-emerald-400">
                {loading ? "..." : statistics?.total_jaguars || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Unique individuals identified
              </p>
            </CardContent>
          </Card>

          <Card className="border-blue-200 dark:border-blue-900 bg-gradient-to-br from-blue-50 to-background dark:from-blue-950/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Images
              </CardTitle>
              <Camera className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-700 dark:text-blue-400">
                {loading ? "..." : statistics?.total_images || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Images processed
              </p>
            </CardContent>
          </Card>

          <Card className="border-amber-200 dark:border-amber-900 bg-gradient-to-br from-amber-50 to-background dark:from-amber-950/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Sightings
              </CardTitle>
              <MapPin className="h-4 w-4 text-amber-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-amber-700 dark:text-amber-400">
                {loading ? "..." : statistics?.total_sightings || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Re-identification matches
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* System Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="grid gap-4 md:grid-cols-2"
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
                System Status
              </CardTitle>
              <CardDescription>
                AI models and database connectivity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">YOLO Detection</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Species Classifier</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground">
                    Optional
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">SAM Segmentation</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">ConvNeXt Re-ID</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Azure Storage</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground">
                    Connected
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">PostgreSQL Database</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground">
                    Connected
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-600" />
                Recent Activity
              </CardTitle>
              <CardDescription>
                Latest identifications and registrations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[240px] overflow-y-auto">
                {loading ? (
                  <p className="text-sm text-muted-foreground">Loading...</p>
                ) : recentActivity.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No activity yet
                  </p>
                ) : (
                  recentActivity.slice(0, 5).map((activity, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="flex items-start gap-3 pb-3 border-b last:border-0"
                    >
                      <div
                        className={`mt-1 h-2 w-2 rounded-full ${activity.type === "registration" ? "bg-emerald-500" : "bg-blue-500"}`}
                      />
                      <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium">
                          {activity.type === "registration" ? (
                            <>
                              New jaguar registered:{" "}
                              <span className="text-emerald-600 dark:text-emerald-400">
                                {activity.jaguar_name}
                              </span>
                            </>
                          ) : (
                            <>
                              Sighting matched:{" "}
                              <span className="text-blue-600 dark:text-blue-400">
                                {activity.jaguar_name}
                              </span>
                            </>
                          )}
                        </p>
                        {activity.similarity && (
                          <p className="text-xs text-muted-foreground">
                            Confidence: {(activity.similarity * 100).toFixed(1)}
                            %
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(activity.timestamp)}
                        </p>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common tasks and navigation</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-3">
              <a
                href="/upload"
                className="flex items-center gap-3 p-4 rounded-lg border hover:border-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 transition-colors group"
              >
                <Camera className="h-5 w-5 text-muted-foreground group-hover:text-emerald-600" />
                <div>
                  <p className="font-medium text-sm">Upload Image</p>
                  <p className="text-xs text-muted-foreground">
                    Identify new jaguar
                  </p>
                </div>
              </a>
              <a
                href="/gallery"
                className="flex items-center gap-3 p-4 rounded-lg border hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors group"
              >
                <Activity className="h-5 w-5 text-muted-foreground group-hover:text-blue-600" />
                <div>
                  <p className="font-medium text-sm">View Gallery</p>
                  <p className="text-xs text-muted-foreground">
                    Browse all jaguars
                  </p>
                </div>
              </a>
              <a
                href="/reports"
                className="flex items-center gap-3 p-4 rounded-lg border hover:border-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors group"
              >
                <TrendingUp className="h-5 w-5 text-muted-foreground group-hover:text-amber-600" />
                <div>
                  <p className="font-medium text-sm">View Reports</p>
                  <p className="text-xs text-muted-foreground">
                    Analytics & insights
                  </p>
                </div>
              </a>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  );
}
