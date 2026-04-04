import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Cat,
  Calendar,
  Eye,
  Search,
  ChevronLeft,
  ChevronRight,
  ImageOff,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { fetchStatistics, API_BASE_URL, type JaguarImage } from "@/services/api";

const PAGE_SIZE = 12;

const IndividualsPage = () => {
  const navigate = useNavigate();
  const [individuals, setIndividuals] = useState<JaguarImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [statistics, setStatistics] = useState<{ total_jaguars: number; total_sightings: number } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    loadIndividuals(controller.signal);
    return () => controller.abort();
  }, [currentPage, searchQuery]);

  const loadIndividuals = async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(currentPage),
        limit: String(PAGE_SIZE),
      });
      if (searchQuery.trim()) {
        params.append("search", searchQuery.trim());
      }

      const [response, stats] = await Promise.all([
        fetch(`${API_BASE_URL}/jaguars?${params}`, { signal }),
        fetchStatistics(signal),
      ]);

      const data = await response.json();
      setIndividuals(data.jaguars || []);
      setTotalCount(data.total || 0);
      setTotalPages(data.total_pages || 1);
      setStatistics(stats);
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        console.error("Failed to load individuals:", err);
      }
    } finally {
      setLoading(false);
    }
  };

  const getImageUrl = (jaguar: JaguarImage): string | null => {
    if (jaguar.images && jaguar.images.length > 0) {
      return jaguar.images[0].url || jaguar.images[0].path;
    }
    if (jaguar.image_url) return jaguar.image_url;
    if (jaguar.file_name) return `${API_BASE_URL}/${jaguar.file_name.replace(/\\/g, "/")}`;
    return null;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "Unknown";
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
      {/* Header */}
      <div className="sticky top-0 z-10 backdrop-blur-lg bg-background/80 border-b border-border">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center gap-4">
            <SidebarTrigger />
            <div className="flex items-center gap-3">
              <Cat className="h-8 w-8 text-emerald-500" />
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-500 to-teal-500 bg-clip-text text-transparent">
                  Individuals
                </h1>
                <p className="text-sm text-muted-foreground">
                  Each registered jaguar and all their recorded detections
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-8">
        {/* Stats row */}
        {statistics && (
          <div className="flex gap-4 mb-8">
            <div className="bg-card border rounded-xl px-5 py-3 flex items-center gap-3">
              <Cat className="h-5 w-5 text-emerald-500" />
              <div>
                <p className="text-xs text-muted-foreground">Individuals</p>
                <p className="text-2xl font-bold">{statistics.total_jaguars}</p>
              </div>
            </div>
            <div className="bg-card border rounded-xl px-5 py-3 flex items-center gap-3">
              <Eye className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-xs text-muted-foreground">Total Sightings</p>
                <p className="text-2xl font-bold">{statistics.total_sightings}</p>
              </div>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-6 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="pl-9"
          />
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: PAGE_SIZE }).map((_, i) => (
              <Skeleton key={i} className="h-72 rounded-2xl" />
            ))}
          </div>
        ) : individuals.length === 0 ? (
          <div className="text-center py-20 text-muted-foreground">
            <Cat className="h-12 w-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium">No individuals found</p>
            <p className="text-sm mt-1">
              {searchQuery ? "Try a different search term." : "Upload and identify jaguars to build your database."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {individuals.map((jaguar, idx) => {
              const imageUrl = getImageUrl(jaguar);
              return (
                <motion.div
                  key={jaguar.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                >
                  <Card
                    className="overflow-hidden cursor-pointer group hover:shadow-lg hover:border-emerald-500/50 transition-all duration-200"
                    onClick={() => navigate(`/image/${jaguar.id}`)}
                  >
                    {/* Image */}
                    <div className="relative h-44 bg-muted overflow-hidden">
                      {imageUrl ? (
                        <img
                          src={imageUrl}
                          alt={jaguar.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <ImageOff className="h-8 w-8 text-muted-foreground/40" />
                        </div>
                      )}
                      <span className="absolute top-2 right-2 bg-black/60 text-white text-xs font-medium px-2 py-0.5 rounded-full">
                        <Eye className="h-3 w-3 mr-1" />
                        {jaguar.times_seen ?? 0}
                      </span>
                    </div>

                    <CardHeader className="pb-1 pt-3">
                      <CardTitle className="text-base truncate">{jaguar.name}</CardTitle>
                    </CardHeader>

                    <CardContent className="pb-4 space-y-1 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>First seen: {formatDate(jaguar.first_seen)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>Last seen: {formatDate(jaguar.last_seen)}</span>
                      </div>
                      <div className="flex items-center gap-1 mt-2">
                        <Eye className="h-3 w-3" />
                        <span>
                          {jaguar.times_seen ?? 0} detection{(jaguar.times_seen ?? 0) !== 1 ? "s" : ""}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 mt-10">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => p - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages} ({totalCount} individuals)
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default IndividualsPage;
