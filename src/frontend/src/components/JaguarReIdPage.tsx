import { useState } from 'react';
import { motion } from 'framer-motion';
import ImageUploader from '@/components/ImageUploader';
import ResultsDisplay from '@/components/ResultsDisplay';
import { AppSidebar } from '@/components/AppSidebar';
import { Button } from '@/components/ui/button';
import { SidebarProvider, SidebarTrigger, SidebarInset } from '@/components/ui/sidebar';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Sparkles, Upload } from 'lucide-react';

const JaguarReIdPage = () => {
    const [image1, setImage1] = useState<File | null>(null);
    const [image2, setImage2] = useState<File | null>(null);
    const [url1, setUrl1] = useState<string>('');
    const [url2, setUrl2] = useState<string>('');
    const [similarity, setSimilarity] = useState<number | null>(null);
    const [loading, setLoading] = useState(false);
    const [showResults, setShowResults] = useState(false);

    // Use /api prefix for nginx proxy, fallback to localhost:8000 for development
    const API_URL = import.meta.env.VITE_API_URL || '/api';

    const handleSubmit = async () => {
        // Check if we have either files or URLs for both images
        const hasImage1 = image1 || url1.trim();
        const hasImage2 = image2 || url2.trim();
        
        if (!hasImage1 || !hasImage2) {
            alert('Please upload or provide URLs for both images.');
            return;
        }

        setLoading(true);
        const formData = new FormData();
        
        // Add files if provided
        if (image1) {
            formData.append('files', image1);
        }
        if (image2) {
            formData.append('files', image2);
        }
        
        // Add URLs if provided (and no corresponding file)
        if (!image1 && url1.trim()) {
            formData.append('url1', url1.trim());
        }
        if (!image2 && url2.trim()) {
            formData.append('url2', url2.trim());
        }

        try {
            const response = await fetch(`${API_URL}/predict`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Something went wrong with the prediction.');
            }

            const data = await response.json();
            setSimilarity(data.similarity);
            setShowResults(true);
        } catch (error) {
            console.error(error);
            alert(error instanceof Error ? error.message : 'Failed to get similarity score.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <SidebarProvider>
            <div className="flex min-h-screen w-full">
                <AppSidebar />
                <SidebarInset className="flex-1">
                    {/* Header */}
                    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
                        <div className="flex h-16 items-center gap-4 px-6">
                            <SidebarTrigger />
                            <div className="flex-1" />
                            <ThemeToggle />
                        </div>
                    </header>

                    {/* Main Content */}
                    <main className="flex-1 p-6">
                        {/* Hero Section */}
                        <section className="mb-8">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6 }}
                            >
                                <h1 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-primary via-primary to-primary/60 bg-clip-text text-transparent">
                                    Jaguar Re-Identification
                                </h1>
                                <p className="text-lg text-muted-foreground max-w-3xl">
                                    Advanced AI-powered pattern recognition to identify individual jaguars from their unique coat patterns
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
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                                    <div className="space-y-3">
                                        <label className="text-sm font-medium flex items-center gap-2">
                                            <Upload className="h-4 w-4" />
                                            First Jaguar Image
                                        </label>
                                        <ImageUploader 
                                            onImageUpload={setImage1} 
                                            onUrlChange={setUrl1}
                                            imageNumber={1}
                                            isLoading={loading}
                                        />
                                    </div>
                                    <div className="space-y-3">
                                        <label className="text-sm font-medium flex items-center gap-2">
                                            <Upload className="h-4 w-4" />
                                            Second Jaguar Image
                                        </label>
                                        <ImageUploader 
                                            onImageUpload={setImage2} 
                                            onUrlChange={setUrl2}
                                            imageNumber={2}
                                            isLoading={loading}
                                        />
                                    </div>
                                </div>

                                <div className="flex justify-center">
                                    <Button 
                                        onClick={handleSubmit} 
                                        disabled={loading || (!image1 && !url1) || (!image2 && !url2)} 
                                        size="lg"
                                        className="px-8 py-6 text-lg rounded-full shadow-lg hover:shadow-xl transition-all"
                                    >
                                        {loading ? (
                                            <>
                                                <motion.div
                                                    animate={{ rotate: 360 }}
                                                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                                    className="mr-2 h-5 w-5 border-2 border-current border-t-transparent rounded-full"
                                                />
                                                Analyzing Patterns...
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="mr-2 h-5 w-5" />
                                                Compare Jaguars
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
                                                Processing: Detection → Segmentation → Feature Extraction
                                            </p>
                                        </div>
                                    </motion.div>
                                )}
                            </motion.div>
                        </section>

                        {/* Results Dialog */}
                        {similarity !== null && (
                            <ResultsDisplay 
                                similarity={similarity} 
                                open={showResults}
                                onClose={() => setShowResults(false)}
                            />
                        )}
                    </main>

                    {/* Footer */}
                    <footer className="border-t py-6 px-6">
                        <div className="text-center text-sm text-muted-foreground">
                            <p>Wildlife Conservation Technology • Powered by Deep Learning</p>
                            <p className="mt-1">Helping protect endangered species through AI</p>
                        </div>
                    </footer>
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
};

export default JaguarReIdPage;
