import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Heart,
  MessageCircle,
  Calendar,
  Camera,
  Eye,
  Share2,
  ArrowLeft,
  Clock,
  Loader2,
} from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  fetchJaguarDetail,
  fetchJaguars,
  fetchJaguarComments,
  addJaguarComment,
  fetchJaguarLikes,
  toggleJaguarLike,
  type JaguarComment,
} from "@/services/api";

interface ImageDetail {
  id: string;
  jaguar_id: string;
  jaguar_name: string;
  image_url: string;
  created_at: string;
  times_seen: number;
  first_seen: string;
  last_seen: string;
  metadata?: {
    latitude?: number;
    longitude?: number;
    location_name?: string;
    camera_trap_id?: string;
    photographer?: string;
    notes?: string;
  };
}

const ImageDetailPage = () => {
  const { jaguarId } = useParams<{ jaguarId: string }>();
  const navigate = useNavigate();

  const [imageDetail, setImageDetail] = useState<ImageDetail | null>(null);
  const [relatedImages, setRelatedImages] = useState<ImageDetail[]>([]);
  const [comments, setComments] = useState<JaguarComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [togglingLike, setTogglingLike] = useState(false);
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [newComment, setNewComment] = useState("");

  useEffect(() => {
    loadImageDetail();
    loadRelatedImages();
    loadComments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jaguarId]);

  const loadImageDetail = async () => {
    setLoading(true);
    try {
      if (!jaguarId) throw new Error("No jaguar ID provided");

      const data = await fetchJaguarDetail(jaguarId);

      // Determine image URL from multiple sources
      let imageUrl = "";
      if (data.images && data.images.length > 0) {
        imageUrl = data.images[0].url || data.images[0].path || "";
      }

      setImageDetail({
        id: data.id + "-image-0", // Generate image ID
        jaguar_id: data.id,
        jaguar_name: data.name,
        image_url: imageUrl,
        created_at: data.first_seen,
        times_seen: data.times_seen,
        first_seen: data.first_seen,
        last_seen: data.last_seen,
        metadata: {},
      });

      // Load like count from database
      const likes = await fetchJaguarLikes(data.id);
      setLikeCount(likes);
    } catch (error) {
      console.error("Error loading image detail:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadRelatedImages = async () => {
    try {
      // Fetch jaguars excluding the current one, limit to 3
      const jaguars = await fetchJaguars(3, jaguarId);

      setRelatedImages(
        jaguars.map((j) => ({
          id: j.id,
          jaguar_id: j.id,
          jaguar_name: j.name,
          image_url: j.images?.[0]?.url || j.image_url || "",
          created_at: j.first_seen,
          times_seen: j.times_seen,
          first_seen: j.first_seen,
          last_seen: j.last_seen,
        })),
      );
    } catch (error) {
      console.error("Error loading related images:", error);
    }
  };

  const loadComments = async () => {
    setLoadingComments(true);
    try {
      if (!jaguarId) return;
      const comments = await fetchJaguarComments(jaguarId);
      setComments(comments);
    } catch (error) {
      console.error("Error loading comments:", error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleLike = async () => {
    if (togglingLike) return; // Prevent double-clicks

    setTogglingLike(true);
    // Optimistic update
    const previousLiked = liked;
    const previousCount = likeCount;
    setLiked(!liked);
    setLikeCount(liked ? likeCount - 1 : likeCount + 1);

    try {
      if (!jaguarId) return;
      const result = await toggleJaguarLike(jaguarId);
      // Update with actual values from server
      setLiked(result.liked);
      setLikeCount(result.count);
    } catch (error) {
      console.error("Error toggling like:", error);
      // Revert on error
      setLiked(previousLiked);
      setLikeCount(previousCount);
    } finally {
      setTogglingLike(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim() || !jaguarId) return;

    setSubmittingComment(true);
    try {
      await addJaguarComment(jaguarId, "You", newComment);
      setNewComment("");
      // Reload comments
      await loadComments();
    } catch (error) {
      console.error("Error adding comment:", error);
    } finally {
      setSubmittingComment(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60)
      return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24)
      return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
    return formatDate(dateString);
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
        {/* Header Skeleton */}
        <div className="sticky top-0 z-10 backdrop-blur-lg bg-background/80 border-b border-border">
          <div className="max-w-7xl mx-auto px-8 py-4">
            <div className="flex items-center gap-4">
              <Skeleton className="h-10 w-10 rounded-md" />
              <Skeleton className="h-9 w-32" />
            </div>
          </div>
        </div>

        {/* Main Content Skeleton */}
        <div className="max-w-7xl mx-auto p-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content - 2/3 width */}
            <div className="lg:col-span-2 space-y-6">
              {/* Hero Image Skeleton */}
              <Skeleton className="w-full aspect-video rounded-2xl" />

              {/* Action Bar Skeleton */}
              <div className="flex items-center gap-4 px-2">
                <Skeleton className="h-12 flex-1 max-w-xs" />
                <Skeleton className="h-12 w-28" />
              </div>

              {/* Metadata Cards Skeleton */}
              <div className="grid grid-cols-2 gap-4">
                {[...Array(4)].map((_, i) => (
                  <Card key={i}>
                    <CardHeader className="pb-3">
                      <Skeleton className="h-4 w-24" />
                    </CardHeader>
                    <CardContent>
                      <Skeleton className="h-8 w-32 mb-2" />
                      <Skeleton className="h-3 w-full" />
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Comments Section Skeleton */}
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-40" />
                </CardHeader>
                <CardContent>
                  {/* Add Comment Skeleton */}
                  <div className="mb-6">
                    <div className="flex gap-3">
                      <Skeleton className="h-10 w-10 rounded-full" />
                      <div className="flex-1">
                        <Skeleton className="h-10 w-full mb-2" />
                        <Skeleton className="h-9 w-32" />
                      </div>
                    </div>
                  </div>

                  <Separator className="my-4" />

                  {/* Comments List Skeleton */}
                  <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="flex gap-3">
                        <Skeleton className="h-10 w-10 rounded-full" />
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-3 w-16" />
                          </div>
                          <Skeleton className="h-4 w-full" />
                          <Skeleton className="h-4 w-3/4" />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar - 1/3 width */}
            <div className="space-y-6">
              {/* Related Images Skeleton */}
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent className="space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i}>
                      <Skeleton className="w-full aspect-video rounded-lg mb-2" />
                      <Skeleton className="h-4 w-full mb-1" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Conservation Info Skeleton */}
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-28" />
                </CardHeader>
                <CardContent className="space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-6 w-32 mt-4" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!imageDetail) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-muted-foreground">Image not found</p>
          <Button onClick={() => navigate("/gallery")} className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Gallery
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
      {/* Header */}
      <div className="sticky top-0 z-10 backdrop-blur-lg bg-background/80 border-b border-border">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center gap-4">
            <SidebarTrigger />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/gallery")}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Gallery
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content - 2/3 width */}
          <div className="lg:col-span-2 space-y-6">
            {/* Hero Image */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="relative aspect-video bg-muted rounded-2xl overflow-hidden shadow-2xl"
            >
              <img
                src={imageDetail.image_url}
                alt={imageDetail.jaguar_name}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-8">
                <h1 className="text-4xl font-bold text-white mb-2">
                  {imageDetail.jaguar_name}
                </h1>
                <p className="text-white/80 text-sm">
                  Individual ID: {imageDetail.jaguar_id}
                </p>
              </div>
            </motion.div>

            {/* Action Bar */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="flex items-center gap-4 px-2"
            >
              <Button
                variant={liked ? "default" : "outline"}
                size="lg"
                onClick={handleLike}
                disabled={togglingLike}
                className="flex-1 max-w-xs"
              >
                {togglingLike ? (
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                ) : (
                  <Heart
                    className={`h-5 w-5 mr-2 ${liked ? "fill-current" : ""}`}
                  />
                )}
                {togglingLike ? "Updating..." : liked ? "Liked" : "Like"} (
                {likeCount})
              </Button>
              <Button variant="outline" size="lg">
                <Share2 className="h-5 w-5 mr-2" />
                Share
              </Button>
            </motion.div>

            {/* Metadata Cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="grid grid-cols-2 gap-4"
            >
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Eye className="h-4 w-4 text-blue-500" />
                    Sightings
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{imageDetail.times_seen}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Total recorded sightings
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-emerald-500" />
                    First Seen
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm font-semibold">
                    {formatDate(imageDetail.first_seen)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Initial registration
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Clock className="h-4 w-4 text-purple-500" />
                    Last Seen
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm font-semibold">
                    {formatDate(imageDetail.last_seen)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Most recent sighting
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Camera className="h-4 w-4 text-orange-500" />
                    Captured
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm font-semibold">
                    {formatDate(imageDetail.created_at)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Image upload date
                  </p>
                </CardContent>
              </Card>
            </motion.div>

            {/* Comments Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageCircle className="h-5 w-5" />
                    Comments ({comments.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* Add Comment */}
                  <div className="mb-6">
                    <div className="flex gap-3">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold">
                          U
                        </div>
                      </div>
                      <div className="flex-1">
                        <Input
                          placeholder="Add a comment..."
                          value={newComment}
                          onChange={(e) => setNewComment(e.target.value)}
                          onKeyDown={(e) =>
                            e.key === "Enter" && handleAddComment()
                          }
                          className="mb-2"
                        />
                        <Button
                          size="sm"
                          onClick={handleAddComment}
                          disabled={!newComment.trim() || submittingComment}
                        >
                          {submittingComment ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Posting...
                            </>
                          ) : (
                            "Post Comment"
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>

                  <Separator className="my-4" />

                  {/* Comments List */}
                  <div className="space-y-4">
                    {loadingComments ? (
                      // Comment Loading Skeletons
                      [...Array(3)].map((_, i) => (
                        <div key={i} className="flex gap-3">
                          <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-2">
                              <Skeleton className="h-4 w-28" />
                              <Skeleton className="h-3 w-20" />
                            </div>
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-5/6" />
                          </div>
                        </div>
                      ))
                    ) : comments.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <MessageCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                        <p>No comments yet. Be the first to comment!</p>
                      </div>
                    ) : (
                      comments.map((comment) => (
                        <motion.div
                          key={comment.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="flex gap-3"
                        >
                          <div className="flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-sm font-semibold text-white">
                              {getInitials(comment.author)}
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-semibold text-sm">
                                {comment.author}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatRelativeTime(comment.created_at)}
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {comment.content}
                            </p>
                          </div>
                        </motion.div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Sidebar - 1/3 width */}
          <div className="space-y-6">
            {/* Related Images */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Related Jaguars</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {relatedImages.map((related) => (
                    <motion.div
                      key={related.jaguar_id}
                      whileHover={{ scale: 1.02 }}
                      onClick={() => navigate(`/image/${related.jaguar_id}`)}
                      className="cursor-pointer group"
                    >
                      <div className="relative aspect-video bg-muted rounded-lg overflow-hidden mb-2">
                        <img
                          src={related.image_url}
                          alt={related.jaguar_name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          loading="lazy"
                        />
                      </div>
                      <h4 className="font-semibold text-sm group-hover:text-primary transition-colors">
                        {related.jaguar_name}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                        <Eye className="h-3 w-3" />
                        {related.times_seen} sightings
                      </div>
                    </motion.div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>

            {/* Conservation Info */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
            >
              <Card className="bg-gradient-to-br from-emerald-50 to-blue-50 dark:from-emerald-950/20 dark:to-blue-950/20">
                <CardHeader>
                  <CardTitle className="text-lg">Conservation</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Every jaguar identification helps us understand population
                    dynamics and protect these magnificent creatures.
                  </p>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">IUCN Status:</span>
                      <span className="px-2 py-1 bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 rounded">
                        Near Threatened
                      </span>
                    </div>
                    <div>
                      <span className="font-semibold">Threats:</span> Habitat
                      loss, poaching, human-wildlife conflict
                    </div>
                    <div>
                      <span className="font-semibold">Range:</span> Central &
                      South America
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageDetailPage;
