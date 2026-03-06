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
  DialogFooter,
} from "@/components/ui/dialog";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Sparkles, Upload, Plus, AlertCircle, X } from "lucide-react";
import {
  identifyJaguar,
  registerNewJaguar,
  suggestNames,
} from "@/services/api";

interface MatchResult {
  match: boolean;
  jaguar_id?: string;
  jaguar_name?: string;
  confidence: number;
  similarity: number;
  species?: string;
  all_scores?: Record<string, number>;
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
        confidence: 1.0,
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

      setErrorDialogMessage(formattedError);
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

            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 text-center"
              >
                <div className="inline-block px-6 py-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">
                    ⏱️ CPU Processing: This may take 5-10 minutes
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    Processing: Detection → Validation → Feature Extraction
                  </p>
                </div>
              </motion.div>
            )}

            {errorMessage && !loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 text-center"
              >
                <div className="inline-block px-6 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg max-w-2xl">
                  <p className="text-sm text-red-700 dark:text-red-300 font-medium">
                    ⚠️ {errorMessage}
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
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                New Jaguar Detected
              </DialogTitle>
              <DialogDescription>
                This jaguar doesn't match any known individual in our database.
                {matchResult?.similarity !== undefined && (
                  <span className="block mt-2 text-sm font-medium">
                    Best match similarity:{" "}
                    {(matchResult.similarity * 100).toFixed(1)}%
                    <span className="text-xs text-muted-foreground ml-1">
                      (threshold: 75%)
                    </span>
                  </span>
                )}
                <span className="block mt-2">
                  Please assign a name to register it.
                </span>
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
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
                      AI Suggestions
                    </label>
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
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowNamingDialog(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSaveNewJaguar}
                disabled={loading || !newJaguarName.trim()}
              >
                {loading ? "Saving..." : "Save Jaguar"}
              </Button>
            </DialogFooter>
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
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
                onClick={() => setShowErrorDialog(false)}
              />

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
