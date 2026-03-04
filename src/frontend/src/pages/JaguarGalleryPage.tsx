import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  Image as ImageIcon,
  Activity as ActivityIcon,
  TrendingUp,
  Eye,
  Sparkles,
  Cpu,
  Zap,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  fetchJaguars,
  fetchStatistics,
  fetchRecentActivity,
  API_BASE_URL,
  type JaguarImage,
  type Activity,
} from "@/services/api";

const JaguarGalleryPage = () => {
  const navigate = useNavigate();
  const [jaguars, setJaguars] = useState<JaguarImage[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [statistics, setStatistics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const abortController = new AbortController();
    loadData(abortController.signal);
    return () => abortController.abort();
  }, []);

  const loadData = async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const [jaguarsData, activityData, statsData] = await Promise.all([
        fetchJaguars(undefined, undefined, signal),
        fetchRecentActivity(20, signal),
        fetchStatistics(signal),
      ]);

      setJaguars(jaguarsData);
      setActivity(activityData);
      setStatistics(statsData);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const truncateName = (name: string, maxLength: number = 20) => {
    if (name.length <= maxLength) return name;

    // Try to extract meaningful parts from jaguar_YYYYMMDD_HHMMSS_micro_filenum format
    const parts = name.split("_");
    if (parts.length >= 2 && parts[0] === "jaguar") {
      const date = parts[1]; // YYYYMMDD
      const fileId = parts[parts.length - 1]; // file number
      return `Jaguar-${date.slice(4, 8)}-${fileId}`; // Show MMDD-filenum
    }

    // Fallback: truncate with ellipsis
    return name.slice(0, maxLength) + "...";
  };

  const getImageUrl = (jaguar: JaguarImage): string | null => {
    // Priority 1: images array
    if (jaguar.images && jaguar.images.length > 0) {
      return jaguar.images[0].url || jaguar.images[0].path;
    }

    // Priority 2: image_url (Azure Blob Storage)
    if (jaguar.image_url) {
      return jaguar.image_url;
    }

    // Priority 3: file_name (local path)
    if (jaguar.file_name) {
      return `${API_BASE_URL}/${jaguar.file_name.replace(/\\/g, "/")}`;
    }

    return null;
  };

  const getConfidenceLevel = (timesSeen: number) => {
    // Calculate confidence based on sightings (higher = more confident identification)
    if (timesSeen >= 5)
      return {
        level: "High",
        color: "text-emerald-500",
        bg: "bg-emerald-500/10",
        percent: 95,
      };
    if (timesSeen >= 3)
      return {
        level: "Good",
        color: "text-blue-500",
        bg: "bg-blue-500/10",
        percent: 85,
      };
    if (timesSeen >= 2)
      return {
        level: "Fair",
        color: "text-yellow-500",
        bg: "bg-yellow-500/10",
        percent: 75,
      };
    return {
      level: "Initial",
      color: "text-purple-500",
      bg: "bg-purple-500/10",
      percent: 65,
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
      {/* Header */}
      <div className="sticky top-0 z-10 backdrop-blur-lg bg-background/80 border-b border-border">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center gap-4">
            <SidebarTrigger />
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <Sparkles className="h-8 w-8 text-emerald-500" />
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-500 to-blue-500 bg-clip-text text-transparent">
                  Jaguar Gallery
                </h1>
                <p className="text-sm text-muted-foreground">
                  Wildlife tracking & identification
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-8">
        {/* Statistics Cards */}
        {!loading ? (
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
            initial="hidden"
            animate="visible"
            variants={{
              visible: { transition: { staggerChildren: 0.1 } },
            }}
          >
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 },
              }}
            >
              <Card className="backdrop-blur-sm hover:shadow-lg transition-all hover:border-emerald-500/30">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Total Jaguars
                  </CardTitle>
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                </CardHeader>
                <CardContent>
                  <motion.div
                    className="text-4xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-600 bg-clip-text text-transparent"
                    initial={{ scale: 0.5 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 200 }}
                  >
                    {statistics?.total_jaguars || 0}
                  </motion.div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Registered individuals
                  </p>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 },
              }}
            >
              <Card className="backdrop-blur-sm hover:shadow-lg transition-all hover:border-blue-500/30">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Total Images
                  </CardTitle>
                  <ImageIcon className="h-4 w-4 text-blue-500" />
                </CardHeader>
                <CardContent>
                  <motion.div
                    className="text-4xl font-bold bg-gradient-to-r from-blue-500 to-blue-600 bg-clip-text text-transparent"
                    initial={{ scale: 0.5 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
                  >
                    {statistics?.total_images || 0}
                  </motion.div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Captured photos
                  </p>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 },
              }}
            >
              <Card className="backdrop-blur-sm hover:shadow-lg transition-all hover:border-purple-500/30">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Total Sightings
                  </CardTitle>
                  <Eye className="h-4 w-4 text-purple-500" />
                </CardHeader>
                <CardContent>
                  <motion.div
                    className="text-4xl font-bold bg-gradient-to-r from-purple-500 to-purple-600 bg-clip-text text-transparent"
                    initial={{ scale: 0.5 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                  >
                    {statistics?.total_sightings || 0}
                  </motion.div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Confirmed matches
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Jaguars Grid */}
        {!loading ? (
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8"
            initial="hidden"
            animate="visible"
            variants={{
              visible: { transition: { staggerChildren: 0.08 } },
            }}
          >
            {jaguars.map((jaguar) => (
              <motion.div
                key={jaguar.id}
                variants={{
                  hidden: { opacity: 0, scale: 0.8 },
                  visible: { opacity: 1, scale: 1 },
                }}
                whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
              >
                <Card className="backdrop-blur-sm overflow-hidden hover:border-emerald-500/50 hover:shadow-lg transition-all group">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle
                          className="text-xl group-hover:text-emerald-500 transition-colors"
                          title={jaguar.name}
                        >
                          {truncateName(jaguar.name)}
                        </CardTitle>
                        <CardDescription>{jaguar.id}</CardDescription>
                      </div>
                      <div
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceLevel(jaguar.times_seen).bg} ${getConfidenceLevel(jaguar.times_seen).color}`}
                      >
                        {getConfidenceLevel(jaguar.times_seen).percent}%
                      </div>
                    </div>
                    {/* AI Model Badges */}
                    <div className="flex gap-2 mt-2 flex-wrap">
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-500/10 text-blue-500 rounded-md text-xs font-medium">
                        <Cpu className="h-3 w-3" />
                        ConvNeXt
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-500/10 text-purple-500 rounded-md text-xs font-medium">
                        <Zap className="h-3 w-3" />
                        YOLOv8
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/10 text-emerald-500 rounded-md text-xs font-medium">
                        {getConfidenceLevel(jaguar.times_seen).level}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {getImageUrl(jaguar) ? (
                      <div
                        className="relative aspect-video bg-muted rounded-lg mb-4 overflow-hidden cursor-pointer hover:opacity-95 transition-opacity"
                        onClick={() => navigate(`/image/${jaguar.id}`)}
                      >
                        <img
                          src={getImageUrl(jaguar)!}
                          alt={jaguar.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = `https://via.placeholder.com/400x200?text=${encodeURIComponent(jaguar.name)}`;
                          }}
                        />
                      </div>
                    ) : (
                      <div className="relative aspect-video bg-muted rounded-lg mb-4 flex items-center justify-center">
                        <ImageIcon className="h-12 w-12 text-muted-foreground" />
                      </div>
                    )}
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <motion.div
                        className="flex items-center gap-2"
                        whileHover={{ x: 2 }}
                      >
                        <Eye className="h-4 w-4 text-purple-500" />
                        <span>{jaguar.times_seen} sightings</span>
                      </motion.div>
                      <motion.div
                        className="flex items-center gap-2"
                        whileHover={{ x: -2 }}
                      >
                        <Calendar className="h-4 w-4 text-blue-500" />
                        <span>
                          {new Date(jaguar.last_seen).toLocaleDateString()}
                        </span>
                      </motion.div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {[...Array(6)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-32" />
                  <Skeleton className="h-4 w-20" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-40 w-full mb-4" />
                  <div className="flex justify-between">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ActivityIcon className="h-5 w-5 text-emerald-500" />
                Recent Activity
              </CardTitle>
              <CardDescription>
                Latest registrations and sightings
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!loading && activity.length > 0 ? (
                <div className="space-y-2">
                  <AnimatePresence mode="popLayout">
                    {activity.map((item, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ delay: index * 0.05 }}
                        className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                        whileHover={{ x: 4 }}
                      >
                        <motion.div
                          className={`p-2 rounded-full ${
                            item.type === "registration"
                              ? "bg-emerald-500/20 text-emerald-500"
                              : "bg-blue-500/20 text-blue-500"
                          }`}
                          whileHover={{ scale: 1.1, rotate: 5 }}
                        >
                          {item.type === "registration" ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </motion.div>
                        <div className="flex-1">
                          <p className="text-sm">
                            {item.type === "registration"
                              ? `New jaguar registered: ${item.jaguar_name}`
                              : `Sighting of ${item.jaguar_name} ${item.similarity ? `(${(item.similarity * 100).toFixed(1)}% match)` : ""}`}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(item.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              ) : loading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No recent activity
                </p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default JaguarGalleryPage;
