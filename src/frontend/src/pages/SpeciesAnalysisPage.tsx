import { useState } from "react";
import { Upload, Sparkles, AlertCircle, ChevronDown, ChevronUp, Play } from "lucide-react";
import { analyzeSpecies, type SpeciesAnalysis } from "../services/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { motion, AnimatePresence } from "framer-motion";

export default function SpeciesAnalysisPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<SpeciesAnalysis | null>(null);
  const [error, setError] = useState<string>("");
  const [isVideoFile, setIsVideoFile] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["species", "subspecies", "physical"])
  );

  // Helper function to extract a random frame from video
  const extractVideoFrame = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      video.preload = 'metadata';
      video.muted = true;
      video.playsInline = true;

      video.onloadedmetadata = () => {
        // Seek to a random time between 10% and 90% of video duration
        const duration = video.duration;
        const randomTime = duration * (0.1 + Math.random() * 0.8);
        video.currentTime = randomTime;
      };

      video.onseeked = () => {
        try {
          // Set canvas dimensions to video dimensions
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;

          // Draw the video frame to canvas
          ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);

          // Convert canvas to data URL
          const frameUrl = canvas.toDataURL('image/jpeg', 0.8);
          
          // Clean up
          URL.revokeObjectURL(video.src);
          resolve(frameUrl);
        } catch (error) {
          reject(error);
        }
      };

      video.onerror = () => {
        URL.revokeObjectURL(video.src);
        reject(new Error('Failed to load video'));
      };

      // Load the video
      video.src = URL.createObjectURL(file);
    });
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Check if file is a video
      const isVideo = file.type.startsWith('video/');
      setIsVideoFile(isVideo);
      
      if (isVideo) {
        // Store the video URL for playback
        const videoObjectUrl = URL.createObjectURL(file);
        setVideoUrl(videoObjectUrl);
        try {
          // Extract a random frame from the video for thumbnail
          const frameUrl = await extractVideoFrame(file);
          setImagePreview(frameUrl);
        } catch (error) {
          console.error('Failed to extract video frame:', error);
          // Fallback to showing the video file directly
          setImagePreview(videoObjectUrl);
        }
      } else {
        // For images, use the file directly
        setImagePreview(URL.createObjectURL(file));
        setVideoUrl("");
      }
      
      setAnalysis(null);
      setError("");
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError("Please select an image first");
      return;
    }

    setAnalyzing(true);
    setError("");

    try {
      const result = await analyzeSpecies(selectedFile);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-600 dark:text-green-400";
    if (confidence >= 0.6) return "text-yellow-600 dark:text-yellow-400";
    return "text-orange-600 dark:text-orange-400";
  };

  return (
    <div className="flex-1 overflow-auto">
      <div className="container mx-auto p-6 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Species Analysis
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Advanced AI-powered species identification and biological characteristics analysis. 
            Upload images or videos (JPG, PNG, MP4, AVI, MOV) for detailed classification.
            Videos longer than 30 seconds will be automatically trimmed.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Image or Video</CardTitle>
              <CardDescription>
                Upload a jaguar image or video for comprehensive species analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 text-center hover:border-purple-400 transition-colors">
                <input
                  type="file"
                  accept="image/*,video/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  {imagePreview ? (
                    <div className="relative mb-4">
                      {isVideoFile && videoUrl ? (
                        <div className="relative">
                          <video
                            src={videoUrl}
                            controls
                            className="max-h-64 mx-auto rounded-lg"
                            onPlay={() => setIsVideoPlaying(true)}
                            onPause={() => setIsVideoPlaying(false)}
                            onEnded={() => setIsVideoPlaying(false)}
                          />
                          {!isVideoPlaying && (
                            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                              <div className="bg-black/60 rounded-full p-4">
                                <Play className="h-12 w-12 text-white fill-white" />
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <img
                          src={imagePreview}
                          alt="Preview"
                          className="max-h-64 mx-auto rounded-lg"
                        />
                      )}
                    </div>
                  ) : (
                    <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  )}
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {imagePreview ? "Click to change file" : "Click to upload image or video"}
                  </p>
                </label>
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={!selectedFile || analyzing}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                {analyzing ? (
                  <>
                    <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Analyze Species
                  </>
                )}
              </Button>

              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results Section */}
          <div className="space-y-4">
            <AnimatePresence>
              {analysis && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-4"
                >
                  {/* Species Info */}
                  <Card>
                    <CardHeader
                      className="cursor-pointer"
                      onClick={() => toggleSection("species")}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">Species Identification</CardTitle>
                          <CardDescription>
                            Detection Confidence:{" "}
                            <span
                              className={getConfidenceColor(
                                analysis.species.detection_confidence
                              )}
                            >
                              {(analysis.species.detection_confidence * 100).toFixed(1)}%
                            </span>
                          </CardDescription>
                        </div>
                        {expandedSections.has("species") ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </CardHeader>
                    {expandedSections.has("species") && (
                      <CardContent className="space-y-3">
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Scientific Name
                          </p>
                          <p className="font-semibold italic">
                            {analysis.species.scientific_name}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Common Name
                          </p>
                          <p className="font-semibold">{analysis.species.common_name}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Family:</span>{" "}
                            {analysis.species.taxonomy.family}
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Genus:</span>{" "}
                            {analysis.species.taxonomy.genus}
                          </div>
                        </div>
                      </CardContent>
                    )}
                  </Card>

                  {/* Subspecies Analysis */}
                  <Card>
                    <CardHeader
                      className="cursor-pointer"
                      onClick={() => toggleSection("subspecies")}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">Subspecies Analysis</CardTitle>
                          <CardDescription>
                            Most Likely: {analysis.subspecies_analysis.most_likely.common_name}
                          </CardDescription>
                        </div>
                        {expandedSections.has("subspecies") ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </CardHeader>
                    {expandedSections.has("subspecies") && (
                      <CardContent className="space-y-4">
                        <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg space-y-2">
                          <div className="flex items-center justify-between">
                            <p className="font-semibold">
                              {analysis.subspecies_analysis.most_likely.common_name}
                            </p>
                            <span
                              className={`text-sm font-medium ${getConfidenceColor(
                                analysis.subspecies_analysis.most_likely.confidence
                              )}`}
                            >
                              {(analysis.subspecies_analysis.most_likely.confidence * 100).toFixed(
                                1
                              )}
                              %
                            </span>
                          </div>
                          <p className="text-sm italic text-gray-600 dark:text-gray-400">
                            {analysis.subspecies_analysis.most_likely.name}
                          </p>
                          <p className="text-sm">
                            <span className="font-medium">Region:</span>{" "}
                            {analysis.subspecies_analysis.most_likely.region}
                          </p>
                          <p className="text-sm">
                            {analysis.subspecies_analysis.most_likely.characteristics}
                          </p>
                        </div>

                        {analysis.subspecies_analysis.alternatives.length > 0 && (
                          <div className="space-y-2">
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                              Alternative Candidates:
                            </p>
                            {analysis.subspecies_analysis.alternatives.map((alt, idx) => (
                              <div
                                key={idx}
                                className="p-2 bg-gray-50 dark:bg-gray-800/50 rounded text-sm space-y-1"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-medium">{alt.common_name}</span>
                                  <span className="text-xs text-gray-500">
                                    {(alt.confidence * 100).toFixed(1)}%
                                  </span>
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">
                                  {alt.region}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}

                        <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                          {analysis.subspecies_analysis.note}
                        </p>
                      </CardContent>
                    )}
                  </Card>

                  {/* Physical Characteristics */}
                  <Card>
                    <CardHeader
                      className="cursor-pointer"
                      onClick={() => toggleSection("physical")}
                    >
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">Physical Characteristics</CardTitle>
                        {expandedSections.has("physical") ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </CardHeader>
                    {expandedSections.has("physical") && (
                      <CardContent className="space-y-3">
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Coat Color</p>
                            <p className="font-medium">
                              {analysis.physical_characteristics.coat_color}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Body Build</p>
                            <p className="font-medium">
                              {analysis.physical_characteristics.body_build}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Pattern Visibility</p>
                            <p className="font-medium">
                              {analysis.physical_characteristics.pattern_visibility}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Size Class</p>
                            <p className="font-medium">
                              {analysis.physical_characteristics.size_class}
                            </p>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                            Weight Range
                          </p>
                          <p className="text-sm font-medium">
                            {analysis.physical_characteristics.estimated_weight_range}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                            Distinctive Features
                          </p>
                          <ul className="text-sm space-y-1">
                            {analysis.physical_characteristics.distinctive_features.map(
                              (feature, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <span className="text-purple-600 dark:text-purple-400">
                                    •
                                  </span>
                                  {feature}
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      </CardContent>
                    )}
                  </Card>

                  {/* Pattern Analysis */}
                  <Card>
                    <CardHeader
                      className="cursor-pointer"
                      onClick={() => toggleSection("pattern")}
                    >
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">Pattern Analysis</CardTitle>
                        {expandedSections.has("pattern") ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </CardHeader>
                    {expandedSections.has("pattern") && (
                      <CardContent className="space-y-3">
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Rosette Density</p>
                            <p className="font-medium">
                              {analysis.pattern_analysis.rosette_density}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Rosette Size</p>
                            <p className="font-medium">
                              {analysis.pattern_analysis.rosette_size}
                            </p>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                            Unique Markers
                          </p>
                          <div className="text-sm space-y-1">
                            <p>
                              <span className="font-medium">Facial:</span>{" "}
                              {analysis.pattern_analysis.unique_markers.facial_markings}
                            </p>
                            <p>
                              <span className="font-medium">Body:</span>{" "}
                              {analysis.pattern_analysis.unique_markers.body_spots}
                            </p>
                            <p>
                              <span className="font-medium">Tail:</span>{" "}
                              {analysis.pattern_analysis.unique_markers.tail_rings}
                            </p>
                          </div>
                        </div>
                        <div
                          className={`p-3 rounded-lg ${
                            analysis.metadata.suitable_for_reid
                              ? "bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800"
                              : "bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800"
                          }`}
                        >
                          <p className="text-sm font-medium">
                            {analysis.pattern_analysis.distinctiveness}
                          </p>
                        </div>
                      </CardContent>
                    )}
                  </Card>

                  {/* Age Estimation */}
                  <Card>
                    <CardHeader
                      className="cursor-pointer"
                      onClick={() => toggleSection("age")}
                    >
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">Age Estimation</CardTitle>
                        {expandedSections.has("age") ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </CardHeader>
                    {expandedSections.has("age") && (
                      <CardContent className="space-y-3">
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Category</p>
                            <p className="font-medium capitalize">
                              {analysis.age_estimation.category}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Estimated Range</p>
                            <p className="font-medium">
                              {analysis.age_estimation.estimated_range}
                            </p>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                            Confidence:{" "}
                            <span
                              className={getConfidenceColor(analysis.age_estimation.confidence)}
                            >
                              {(analysis.age_estimation.confidence * 100).toFixed(1)}%
                            </span>
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                            Indicators
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {analysis.age_estimation.indicators.map((indicator, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs"
                              >
                                {indicator}
                              </span>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    )}
                  </Card>

                  {/* Conservation Status */}
                  <Card>
                    <CardHeader
                      className="cursor-pointer"
                      onClick={() => toggleSection("conservation")}
                    >
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">Conservation Status</CardTitle>
                        {expandedSections.has("conservation") ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </CardHeader>
                    {expandedSections.has("conservation") && (
                      <CardContent className="space-y-3">
                        <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                          <p className="text-sm font-medium">
                            IUCN Status: {analysis.conservation_status.iucn_status}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Population Trend: {analysis.conservation_status.population_trend}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            Main Threats
                          </p>
                          <div className="grid grid-cols-2 gap-2">
                            {analysis.conservation_status.threats.map((threat, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs text-center"
                              >
                                {threat}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Habitat</p>
                          <p className="text-sm">{analysis.conservation_status.habitat}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Behavior</p>
                          <p className="text-sm">{analysis.conservation_status.behavior}</p>
                        </div>
                      </CardContent>
                    )}
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
