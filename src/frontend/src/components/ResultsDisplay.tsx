import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, TrendingUp, Award } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from '@/components/ui/dialog';

interface ResultsDisplayProps {
    similarity: number;
    open: boolean;
    onClose: () => void;
}

const ResultsDisplay = ({ similarity, open, onClose }: ResultsDisplayProps) => {
    const isSameJaguar = similarity >= 0.75;
    const percentage = Math.round(similarity * 100);
    
    const circumference = 2 * Math.PI * 70;
    const offset = circumference - (percentage / 100) * circumference;

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl p-0 overflow-hidden">
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, type: "spring" }}
                    className="w-full"
                >
                    <div className="bg-card p-8">
                        <DialogHeader className="mb-8">
                            <DialogTitle className="text-3xl font-bold text-center">
                                Analysis Complete
                            </DialogTitle>
                            <DialogDescription className="text-center text-base">
                                AI-powered pattern matching results
                            </DialogDescription>
                        </DialogHeader>

                <div className="grid md:grid-cols-2 gap-8 items-center">
                    {/* Circular Progress */}
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
                        className="flex justify-center"
                    >
                        <div className="relative">
                            <svg className="w-56 h-56 transform -rotate-90">
                                {/* Background circle */}
                                <circle
                                    cx="112"
                                    cy="112"
                                    r="70"
                                    stroke="currentColor"
                                    strokeWidth="12"
                                    fill="none"
                                    className="text-muted/20"
                                />
                                {/* Progress circle */}
                                <motion.circle
                                    cx="112"
                                    cy="112"
                                    r="70"
                                    stroke="currentColor"
                                    strokeWidth="12"
                                    fill="none"
                                    strokeLinecap="round"
                                    initial={{ strokeDashoffset: circumference }}
                                    animate={{ strokeDashoffset: offset }}
                                    transition={{ duration: 1.5, ease: "easeOut" }}
                                    strokeDasharray={circumference}
                                    className={cn(
                                        isSameJaguar ? "text-green-500" : "text-red-500"
                                    )}
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center flex-col">
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: 0.5 }}
                                    className="text-center"
                                >
                                    <div className="text-5xl font-bold mb-1">{percentage}%</div>
                                    <div className="text-sm text-muted-foreground">Match Score</div>
                                </motion.div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Results Info */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 }}
                        className="space-y-6"
                    >
                        {/* Verdict */}
                        <div className={cn(
                            "flex items-center gap-3 p-4 rounded-2xl border-2",
                            isSameJaguar 
                                ? "bg-green-500/10 border-green-500/50" 
                                : "bg-red-500/10 border-red-500/50"
                        )}>
                            {isSameJaguar ? (
                                <>
                                    <CheckCircle2 className="h-8 w-8 text-green-500 shrink-0" />
                                    <div>
                                        <h4 className="font-bold text-lg">Same Jaguar</h4>
                                        <p className="text-sm text-muted-foreground">High confidence match detected</p>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <XCircle className="h-8 w-8 text-red-500 shrink-0" />
                                    <div>
                                        <h4 className="font-bold text-lg">Different Jaguars</h4>
                                        <p className="text-sm text-muted-foreground">Distinct individuals identified</p>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-secondary/50 p-4 rounded-xl">
                                <div className="flex items-center gap-2 mb-2">
                                    <TrendingUp className="h-4 w-4 text-primary" />
                                    <span className="text-sm font-medium">Similarity</span>
                                </div>
                                <div className="text-2xl font-bold">{similarity.toFixed(4)}</div>
                            </div>
                            <div className="bg-secondary/50 p-4 rounded-xl">
                                <div className="flex items-center gap-2 mb-2">
                                    <Award className="h-4 w-4 text-primary" />
                                    <span className="text-sm font-medium">Confidence</span>
                                </div>
                                <div className="text-2xl font-bold">
                                    {isSameJaguar ? 'High' : 'Low'}
                                </div>
                            </div>
                        </div>

                        {/* Threshold Info */}
                        <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded-lg">
                            <p>
                                <strong>Threshold:</strong> 0.75 • 
                                Scores above this threshold indicate the same individual
                            </p>
                        </div>
                    </motion.div>
                </div>
                    </div>
                </motion.div>
            </DialogContent>
        </Dialog>
    );
};

export default ResultsDisplay;
