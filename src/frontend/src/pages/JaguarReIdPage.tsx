import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ImageUploader from "@/components/ImageUploader";
import ResultsDisplay from "@/components/ResultsDisplay";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Sparkles, Upload, Plus, AlertCircle, X, Link2 } from "lucide-react";
import {
  identifyJaguar,
  registerNewJaguar,
  suggestNames,
  linkToExistingJaguar,
} from "@/services/api";

interface TopMatch {
  id: string;
  name: string;
  similarity: number;
  times_seen: number;
  image_url: string | null;
  has_image: boolean;
}

interface MatchResult {
  match: boolean;
  jaguar_id?: string;
  jaguar_name?: string;
  confidence: number;
  similarity: number;
  species?: string;
  all_scores?: Record<string, number>;
  closest_jaguar_name?: string | null;
  closest_jaguar_id?: string | null;
  top_matches?: TopMatch[];
}

const JaguarReIdPage = () => {
  const [image, setImage] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string>("");
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showNamingDialog, setShowNamingDialog] = useState(false);
  const [newJaguarName, setNewJaguarName] = useState<string>("");
  const [suggestedNames, setSuggestedNames] = useState<
    Array<{ name: string; category: string; description: string }>
  >([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [errorDialogMessage, setErrorDialogMessage] = useState<string>("");

  // Handlers that clear error message on new input
  const handleImageUpload = (file: File | null) => {
    setImage(file);
    setErrorMessage("");
  };

  const handleUrlChange = (url: string) => {
    setImageUrl(url);
    setErrorMessage("");
  };

  // Helper function to download image from URL in browser and convert to File
  const downloadImageFromUrl = async (url: string): Promise<File> => {
    const response = await fetch(url, {
      mode: 'cors',
      credentials: 'omit',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to download image: ${response.statusText}`);
    }
    
    const blob = await response.blob();
    const filename = url.split('/').pop()?.split('?')[0] || 'image.jpg';
    return new File([blob], filename, { type: blob.type || 'image/jpeg' });
  };

  const fetchNameSuggestions = async () => {
    setLoadingSuggestions(true);
    try {
      // If user provided a URL, download it in the browser first
      let fileToSend = image;
      if (!fileToSend && imageUrl.trim()) {
        try {
          fileToSend = await downloadImageFromUrl(imageUrl.trim());
        } catch (error) {
          console.error("Failed to download image for name suggestions:", error);
        }
      }

      const data = await suggestNames(fileToSend || undefined, undefined);
      setSuggestedNames(data.suggestions || []);
    } catch (error) {
      console.error("Failed to fetch name suggestions:", error);
      setSuggestedNames([]);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleSubmit = async () => {
    // Check if we have an image
    const hasImage = image || imageUrl.trim();

    if (!hasImage) {
      setErrorMessage("Please upload or provide a URL for the jaguar image.");
      return;
    }

    setLoading(true);
    setErrorMessage("");

    try {
      // If user provided a URL, download it in the browser first
      let fileToSend = image;
      if (!fileToSend && imageUrl.trim()) {
        try {
          fileToSend = await downloadImageFromUrl(imageUrl.trim());
        } catch (error) {
          throw new Error(`Failed to download image: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }

      // Always send as file (no URL parameter)
      const data = await identifyJaguar(fileToSend || undefined, undefined);

      setMatchResult(data);

      // If no match found, fetch name suggestions and show naming dialog
      if (!data.match) {
        fetchNameSuggestions();
        setShowNamingDialog(true);
      } else {
        setShowResults(true);
      }
    } catch (error) {
      console.error(error);
      const errorMsg =
        error instanceof Error ? error.message : "Failed to identify jaguar.";
      setErrorMessage(errorMsg);

      // Show all errors in dialog with formatted message
      let formattedError = errorMsg;

      // Format validation error messages with simplified message
      if (
        errorMsg.includes("does not appear") ||
        errorMsg.includes("not a jaguar") ||
        errorMsg.includes("No animal detected") ||
        errorMsg.includes("unusual similarity") ||
        errorMsg.includes("different species")
      ) {
        formattedError = "Please upload a clear image of a jaguar";
      }

      setErrorDialogMessage(formattedError);
      setShowErrorDialog(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveNewJaguar = async () => {
    if (!newJaguarName.trim()) {
      setErrorDialogMessage("Please enter a name for this jaguar.");
      setShowErrorDialog(true);
      return;
    }

    setLoading(true);
    setErrorMessage("");

    try {
      // If user provided a URL, download it in the browser first
      let fileToSend = image;
      if (!fileToSend && imageUrl.trim()) {
        try {
          fileToSend = await downloadImageFromUrl(imageUrl.trim());
        } catch (error) {
          throw new Error(`Failed to download image: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }

      const data = await registerNewJaguar(
        fileToSend,
        newJaguarName.trim(),
        undefined, // Always send as file, not URL
      );

      setShowNamingDialog(false);
      setShowResults(true);
      setMatchResult({
        match: false,
        jaguar_id: data.jaguar_id,
        jaguar_name: newJaguarName.trim(),
        confidence: matchResult?.confidence ?? 1.0,
        similarity: 0,
      });
    } catch (error) {
      console.error(error);
      const errorMsg =
        error instanceof Error ? error.message : "Failed to register jaguar.";
      setErrorMessage(errorMsg);

      // Format validation error messages with simplified message
      let formattedError = errorMsg;
      if (
        errorMsg.includes("does not appear") ||
        errorMsg.includes("not a jaguar") ||
        errorMsg.includes("No animal detected") ||
        errorMsg.includes("unusual similarity") ||
        errorMsg.includes("different species")
      ) {
        formattedError = "Please upload a clear image of a jaguar";
      }

      // Close naming dialog so error dialog is visible
      setShowNamingDialog(false);
      setErrorDialogMessage(formattedError);
      setShowErrorDialog(true);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkToExisting = async (jaguarId: string, jaguarName: string) => {
    setLoading(true);
    setErrorMessage("");

    try {
      // If user provided a URL, download it in the browser first
      let fileToSend = image;
      if (!fileToSend && imageUrl.trim()) {
        try {
          fileToSend = await downloadImageFromUrl(imageUrl.trim());
        } catch (error) {
          throw new Error(`Failed to download image: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }

      const data = await linkToExistingJaguar(
        fileToSend,
        jaguarId,
        undefined,
      );

      setShowNamingDialog(false);
      setShowResults(true);
      setMatchResult({
        match: true, // Show as match since user manually linked it
        jaguar_id: data.jaguar_id,
        jaguar_name: jaguarName,
        confidence: matchResult?.confidence ?? 1.0,
        similarity: matchResult?.similarity ?? 0.65, // Use the similarity from identification
      });
    } catch (error) {
      console.error(error);
      const errorMsg =
        error instanceof Error ? error.message : "Failed to link to jaguar.";
      setErrorMessage(errorMsg);

      // Close naming dialog so error dialog is visible
      setShowNamingDialog(false);
      setErrorDialogMessage(errorMsg);
      setShowErrorDialog(true);
    } finally {
      setLoading(false);
    }
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
                  Jaguar Identification
                </h1>
                <p className="text-sm text-muted-foreground">
                  Upload images or videos to identify individual jaguars
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-8">
        {/* Hero Description */}
        <section className="mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-lg text-muted-foreground max-w-3xl">
              Upload an image or video to identify if it matches any known individual jaguar in our database, 
              or register it as a new jaguar. Supports JPG, PNG, MP4, AVI, MOV formats.
            </p>
          </motion.div>
        </section>

        {/* Upload Section */}
        <section className="mb-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="max-w-2xl mx-auto mb-6">
              <div className="space-y-3">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Upload className="h-4 w-4" />
                  Upload Jaguar Image or Video
                </label>
                <ImageUploader
                  onImageUpload={handleImageUpload}
                  onUrlChange={handleUrlChange}
                  imageNumber={1}
                  isLoading={loading}
                />
              </div>
            </div>

            <div className="flex justify-center">
              <Button
                onClick={handleSubmit}
                disabled={loading || (!image && !imageUrl)}
                size="lg"
                className="px-8 py-6 text-lg rounded-full shadow-lg hover:shadow-xl transition-all"
              >
                {loading ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                      className="mr-2 h-5 w-5 border-2 border-current border-t-transparent rounded-full"
                    />
                    Classifying Species...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-5 w-5" />
                    Classify Species
                  </>
                )}
              </Button>
            </div>

          

            {errorMessage && !loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 text-center"
              >
                <div className="inline-block px-6 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg max-w-2xl">
                  <p className="text-sm text-red-700 dark:text-red-300 font-medium">
                    {errorMessage}
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    Please upload a clear image of a jaguar
                  </p>
                </div>
              </motion.div>
            )}
          </motion.div>
        </section>

        {/* Naming Dialog for New Jaguars */}
        <Dialog open={showNamingDialog} onOpenChange={setShowNamingDialog}>
          <DialogContent className="max-w-5xl max-h-[85vh]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                New Jaguar Detected
              </DialogTitle>
              <DialogDescription>
                This jaguar doesn't match any known individual in our database.
                {matchResult?.similarity !== undefined && matchResult.similarity > 0 && (
                  <span className="block mt-2 text-sm font-medium">
                    Closest existing individual:
                    {matchResult.closest_jaguar_name ? (
                      <strong> {matchResult.closest_jaguar_name}</strong>
                    ) : null}{" "}
                    at {(matchResult.similarity * 100).toFixed(1)}%
                    <span className="text-xs text-muted-foreground ml-1">
                      (below the 70% match threshold)
                    </span>
                  </span>
                )}
                <span className="block mt-2">
                  You can either register this as a new jaguar, or link it to an existing one.
                </span>
              </DialogDescription>
            </DialogHeader>

            {/* Two-Column Layout: Top Matches Left, Form Right */}
            <div className="grid md:grid-cols-[300px_1fr] gap-6">
              {/* LEFT: Top Matches Section with Vertical Scroll */}
              {matchResult?.top_matches && matchResult.top_matches.length > 0 && (
                <div className="border-r pr-6 space-y-3">
                  <div className="flex items-center gap-2">
                    <Link2 className="h-4 w-4 text-blue-500" />
                    <h4 className="text-sm font-semibold">Top Matches</h4>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Click to link to existing
                  </p>
                  
                  {/* Vertical Scrollable Matches */}
                  <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                    {loading ? (
                      // Loading skeletons
                      [...Array(3)].map((_, idx) => (
                        <div
                          key={idx}
                          className="flex gap-3 p-3 rounded-lg border border-border animate-pulse"
                        >
                          <div className="w-20 h-20 bg-muted rounded-md flex-shrink-0"></div>
                          <div className="flex-1 space-y-2">
                            <div className="h-4 bg-muted rounded w-3/4"></div>
                            <div className="h-3 bg-muted rounded w-1/2"></div>
                            <div className="h-3 bg-muted rounded w-1/2"></div>
                          </div>
                        </div>
                      ))
                    ) : (
                      matchResult.top_matches.map((match) => (
                        <button
                          key={match.id}
                          onClick={() => handleLinkToExisting(match.id, match.name)}
                          disabled={loading}
                          className="w-full flex gap-3 p-3 rounded-lg border border-border hover:bg-accent/50 hover:border-blue-500 transition-all group disabled:opacity-50 disabled:cursor-not-allowed text-left"
                        >
                          {match.image_url ? (
                            <img
                              src={match.image_url}
                              alt={match.name}
                              className="w-20 h-20 object-cover rounded-md flex-shrink-0"
                            />
                          ) : (
                            <div className="w-20 h-20 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
                              <span className="text-xs text-muted-foreground text-center">No image</span>
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-sm truncate" title={match.name}>{match.name}</div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {(match.similarity * 100).toFixed(1)}% match
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Seen {match.times_seen}×
                            </div>
                            {!match.has_image && (
                              <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                                ⚠️ No ref img
                              </div>
                            )}
                          </div>
                          <Link2 className="h-4 w-4 text-muted-foreground group-hover:text-blue-500 transition-colors flex-shrink-0 mt-1" />
                        </button>
                      ))
                    )}
                  </div>
                  
                  {!loading && matchResult.top_matches.length > 0 && (
                    <p className="text-xs text-muted-foreground text-center pt-2 border-t">
                      {matchResult.top_matches.length} matches found
                    </p>
                  )}
                </div>
              )}

              {/* RIGHT: New Jaguar Form */}
              <div className="flex flex-col min-h-[400px]">
                {/* Form Content - Scrollable */}
                <div className="flex-1 space-y-4 overflow-y-auto pr-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Jaguar Name</label>
                    <Input
                      placeholder="e.g., Luna, Shadow, Spot..."
                      value={newJaguarName}
                      onChange={(e) => setNewJaguarName(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSaveNewJaguar()}
                      disabled={loading}
                    />
                  </div>

                  {/* AI Name Suggestions */}
                  {loadingSuggestions ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      <span>Generating AI suggestions...</span>
                    </div>
                  ) : (
                    suggestedNames.length > 0 && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-purple-500" />
                          AI Name Suggestions
                        </label>
                        <p className="text-xs text-muted-foreground">
                          These are suggested <strong>names for this new individual</strong> — not jaguars already in the database.
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {suggestedNames.map((suggestion, idx) => (
                            <button
                              key={idx}
                              onClick={() => setNewJaguarName(suggestion.name)}
                              className="px-3 py-2 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 border border-purple-200 dark:border-purple-800 rounded-lg transition-colors group"
                              title={suggestion.description}
                            >
                              <div className="text-sm font-medium text-purple-700 dark:text-purple-300">
                                {suggestion.name}
                              </div>
                              <div className="text-xs text-purple-600 dark:text-purple-400">
                                {suggestion.category}
                              </div>
                            </button>
                          ))}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Click a suggestion to use it
                        </p>
                      </div>
                    )
                  )}
                </div>

                {/* Action Buttons - Fixed at Bottom */}
                <div className="flex items-center gap-3 pt-4 mt-4 border-t">
                  <Button
                    variant="outline"
                    onClick={() => setShowNamingDialog(false)}
                    disabled={loading}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSaveNewJaguar}
                    disabled={loading || !newJaguarName.trim()}
                    className="flex-1"
                  >
                    {loading ? "Saving..." : "Save Jaguar"}
                  </Button>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Results Dialog */}
        {matchResult && (
          <ResultsDisplay
            matchResult={matchResult}
            open={showResults}
            onClose={() => setShowResults(false)}
          />
        )}

        {/* Error Dialog - Modern Animated */}
        <AnimatePresence>
          {showErrorDialog && (
            <>
              {/* Dialog */}
              <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: 20 }}
                  transition={{ type: "spring", duration: 0.5, bounce: 0.3 }}
                  className="relative w-full max-w-lg bg-background rounded-2xl shadow-2xl border border-border overflow-hidden"
                >
                  {/* Header with gradient */}
                  <div className="bg-gradient-to-r from-red-500/10 via-orange-500/10 to-red-500/10 p-6 border-b border-red-500/20">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <motion.div
                          initial={{ scale: 0, rotate: -180 }}
                          animate={{ scale: 1, rotate: 0 }}
                          transition={{
                            delay: 0.2,
                            type: "spring",
                            stiffness: 200,
                          }}
                          className="flex items-center justify-center w-12 h-12 rounded-full bg-red-500/20 text-red-500"
                        >
                          <AlertCircle className="h-6 w-6" />
                        </motion.div>
                        <div>
                          <h3 className="text-xl font-semibold text-foreground">
                            Validation Failed
                          </h3>
                          <p className="text-sm text-muted-foreground mt-0.5">
                            Image validation failed
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 rounded-full hover:bg-red-500/10"
                        onClick={() => setShowErrorDialog(false)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      className="space-y-4"
                    >
                      <div className="bg-muted/50 rounded-xl p-4 border border-border">
                        <p className="text-sm leading-relaxed text-foreground">
                          {errorDialogMessage}
                        </p>
                      </div>

                      <div className="flex items-start gap-3 text-sm text-muted-foreground">
                        <div className="flex-shrink-0 mt-0.5">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        </div>
                        <p>
                          Our AI model is specifically trained to identify
                          jaguars. Please ensure your image contains a clear
                          view of a jaguar.
                        </p>
                      </div>
                    </motion.div>
                  </div>

                  {/* Footer */}
                  <div className="px-6 pb-6 flex gap-3 justify-end">
                    <Button
                      onClick={() => setShowErrorDialog(false)}
                      className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white shadow-lg shadow-red-500/20"
                    >
                      Try Again
                    </Button>
                  </div>
                </motion.div>
              </div>
            </>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="border-t mt-12">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="text-center text-sm text-muted-foreground">
            <p>Wildlife Conservation Technology • Powered by Deep Learning</p>
            <p className="mt-1">
              Helping protect endangered species through AI
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JaguarReIdPage;
