import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, X, Check, Image as ImageIcon, Link as LinkIcon, Video, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface ImageUploaderProps {
    onImageUpload: (file: File | null) => void;
    onUrlChange?: (url: string) => void;
    imageNumber: number;
    isLoading?: boolean;
}

const ImageUploader = ({ onImageUpload, onUrlChange, imageNumber, isLoading = false }: ImageUploaderProps) => {
    const [preview, setPreview] = useState<string | null>(null);
    const [isHovered, setIsHovered] = useState(false);
    const [imageUrl, setImageUrl] = useState<string>('');
    const [useUrl, setUseUrl] = useState(false);
    const [isVideo, setIsVideo] = useState(false);
    const [videoUrl, setVideoUrl] = useState<string>('');
    const [isVideoPlaying, setIsVideoPlaying] = useState(false);

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

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (file && !isLoading) {
            onImageUpload(file);
            
            // Check if file is a video
            const fileIsVideo = file.type.startsWith('video/');
            setIsVideo(fileIsVideo);
            
            if (fileIsVideo) {
                // Store the video URL for playback
                const videoObjectUrl = URL.createObjectURL(file);
                setVideoUrl(videoObjectUrl);
                try {
                    // Extract a random frame from the video for thumbnail
                    const frameUrl = await extractVideoFrame(file);
                    setPreview(frameUrl);
                } catch (error) {
                    console.error('Failed to extract video frame:', error);
                    // Fallback to showing the video file directly
                    setPreview(videoObjectUrl);
                }
            } else {
                // For images, use the file directly
                setPreview(URL.createObjectURL(file));
                setVideoUrl('');
            }
            
            setUseUrl(false);
            setImageUrl('');
        }
    }, [onImageUpload, isLoading]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 
            'image/*': ['.jpeg', '.png', '.jpg'],
            'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        },
        multiple: false,
        disabled: isLoading,
    });

    const handleRemoveImage = () => {
        if (!isLoading) {
            setPreview(null);
            onImageUpload(null);
            setImageUrl('');
            setUseUrl(false);
            setIsVideo(false);
            setVideoUrl('');
            setIsVideoPlaying(false);
        }
    };

    const handleUrlSubmit = () => {
        if (imageUrl.trim() && !isLoading) {
            setPreview(imageUrl);
            setUseUrl(true);
            // Try to detect if URL is a video based on extension
            const urlLower = imageUrl.toLowerCase();
            const isVideoUrl = urlLower.includes('.mp4') || urlLower.includes('.avi') || 
                               urlLower.includes('.mov') || urlLower.includes('.mkv') || 
                               urlLower.includes('.wmv');
            setIsVideo(isVideoUrl);
            onImageUpload(null);
            if (onUrlChange) {
                onUrlChange(imageUrl);
            }
        }
    };

    const handleUrlChange = (value: string) => {
        setImageUrl(value);
        if (!value) {
            setPreview(null);
            setUseUrl(false);
            if (onUrlChange) {
                onUrlChange('');
            }
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: imageNumber * 0.1 }}
            className="flex flex-col space-y-4"
        >
            {/* URL Input Section */}
            <div className="flex gap-2">
                <div className="relative flex-1">
                    <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        type="url"
                        placeholder="Or paste image/video URL..."
                        value={imageUrl}
                        onChange={(e) => handleUrlChange(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
                        disabled={isLoading}
                        className="pl-10"
                    />
                </div>
                <Button 
                    onClick={handleUrlSubmit} 
                    disabled={!imageUrl.trim() || isLoading}
                    variant="secondary"
                    size="default"
                >
                    Load
                </Button>
            </div>

            {/* File Upload Section */}
            <div
                {...getRootProps()}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                className={cn(
                    "relative w-full h-80 border-2 border-dashed rounded-2xl flex items-center justify-center overflow-hidden transition-all duration-300",
                    isLoading && "opacity-50 cursor-not-allowed",
                    !isLoading && "cursor-pointer",
                    isDragActive && !isLoading && "border-primary bg-primary/5 scale-105",
                    !isDragActive && !preview && !isLoading && "border-border hover:border-primary/50 hover:bg-accent/50",
                    preview && "border-primary/30"
                )}
            >
                <input {...getInputProps()} />
                
                <AnimatePresence mode="wait">
                    {preview ? (
                        <motion.div
                            key="preview"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="relative w-full h-full"
                        >
                            {isVideo && videoUrl ? (
                                <div className="relative w-full h-full">
                                    <video 
                                        src={videoUrl}
                                        controls
                                        className="w-full h-full object-cover"
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
                                    src={preview} 
                                    alt="Preview" 
                                    className="w-full h-full object-cover"
                                />
                            )}
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: isHovered && !isLoading && !isVideoPlaying ? 1 : 0 }}
                                className="absolute inset-0 bg-black/50 flex items-center justify-center backdrop-blur-sm"
                            >
                                <div className="text-white text-center">
                                    {isVideo ? (
                                        <Video className="h-12 w-12 mx-auto mb-2" />
                                    ) : (
                                        <ImageIcon className="h-12 w-12 mx-auto mb-2" />
                                    )}
                                    <p className="text-sm">
                                        {isLoading ? 'Analysis in progress...' : 'Click or drag to change'}
                                    </p>
                                </div>
                            </motion.div>
                            <motion.div
                                initial={{ scale: 0, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                className="absolute top-4 right-4 bg-green-500 text-white p-2 rounded-full shadow-lg"
                            >
                                <Check className="h-4 w-4" />
                            </motion.div>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="upload"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex flex-col items-center p-8 text-center"
                        >
                            <motion.div
                                animate={{ 
                                    y: isDragActive ? -10 : 0,
                                    scale: isDragActive ? 1.1 : 1 
                                }}
                                transition={{ type: "spring", stiffness: 300 }}
                            >
                                <UploadCloud className={cn(
                                    "h-16 w-16 mb-4 transition-colors",
                                    isDragActive ? "text-primary" : "text-muted-foreground"
                                )} />
                            </motion.div>
                            <p className="text-lg font-medium mb-2">
                                {isDragActive ? 'Drop the file here' : 'Drag & drop your image or video'}
                            </p>
                            <p className="text-sm text-muted-foreground mb-4">
                                or click to browse
                            </p>
                            <div className="space-y-2">
                                <div className="flex gap-2 text-xs text-muted-foreground justify-center">
                                    <span className="px-2 py-1 bg-emerald-500/10 text-emerald-600 rounded font-medium">Images:</span>
                                    <span className="px-2 py-1 bg-secondary rounded">JPG</span>
                                    <span className="px-2 py-1 bg-secondary rounded">PNG</span>
                                    <span className="px-2 py-1 bg-secondary rounded">JPEG</span>
                                </div>
                                <div className="flex gap-2 text-xs text-muted-foreground justify-center">
                                    <span className="px-2 py-1 bg-blue-500/10 text-blue-600 rounded font-medium">Videos:</span>
                                    <span className="px-2 py-1 bg-secondary rounded">MP4</span>
                                    <span className="px-2 py-1 bg-secondary rounded">AVI</span>
                                    <span className="px-2 py-1 bg-secondary rounded">MOV</span>
                                </div>
                                <p className="text-xs text-muted-foreground/70 italic">
                                    Videos longer than 30s will be auto-trimmed
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
            
            <AnimatePresence>
                {preview && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="flex justify-center gap-2"
                    >
                        <Button 
                            variant="outline" 
                            onClick={handleRemoveImage}
                            disabled={isLoading}
                            className="gap-2"
                        >
                            <X className="h-4 w-4" /> 
                            {isVideo ? 'Remove Video' : 'Remove Image'}
                        </Button>
                        {useUrl && imageUrl && (
                            <div className="px-3 py-2 bg-secondary rounded-md text-xs text-muted-foreground flex items-center gap-2">
                                <LinkIcon className="h-3 w-3" />
                                Loaded from URL
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default ImageUploader;
