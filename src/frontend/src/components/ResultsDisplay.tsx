import { motion } from "framer-motion";
import { CheckCircle2, TrendingUp, Award, User, Database } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface MatchResult {
  match: boolean;
  jaguar_id?: string;
  jaguar_name?: string;
  confidence: number;
  similarity: number;
  species?: string;
  all_scores?: Record<string, number>;
}

interface ResultsDisplayProps {
  matchResult: MatchResult;
  open: boolean;
  onClose: () => void;
}

const ResultsDisplay = ({
  matchResult,
  open,
  onClose,
}: ResultsDisplayProps) => {
  const { match, jaguar_id, jaguar_name, confidence, similarity, species, all_scores } = matchResult;
  const percentage = Math.round(confidence * 100);

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
                {match ? "Match Found!" : "New Jaguar Registered"}
              </DialogTitle>
              <DialogDescription className="text-center text-base">
                {match
                  ? "This jaguar matches an existing individual in our database"
                  : "Successfully registered as a new jaguar identity"}
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
                      className={cn(match ? "text-green-500" : "text-blue-500")}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.5 }}
                      className="text-center"
                    >
                      <div className="text-5xl font-bold mb-1">
                        {percentage}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Match Score
                      </div>
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
                <div
                  className={cn(
                    "flex items-center gap-3 p-4 rounded-2xl border-2",
                    match
                      ? "bg-green-500/10 border-green-500/50"
                      : "bg-blue-500/10 border-blue-500/50",
                  )}
                >
                  {match ? (
                    <>
                      <CheckCircle2 className="h-8 w-8 text-green-500 shrink-0" />
                      <div>
                        <h4 className="font-bold text-lg">Known Jaguar</h4>
                        <p className="text-sm text-muted-foreground">
                          Matched: {jaguar_name || `ID: ${jaguar_id}`}
                        </p>
                      </div>
                    </>
                  ) : (
                    <>
                      <User className="h-8 w-8 text-blue-500 shrink-0" />
                      <div>
                        <h4 className="font-bold text-lg">New Identity</h4>
                        <p className="text-sm text-muted-foreground">
                          Registered as: {jaguar_name}
                        </p>
                      </div>
                    </>
                  )}
                </div>

                {/* Species Classification */}
                {species && (
                  <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border-2 border-purple-500/30 p-4 rounded-2xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Award className="h-5 w-5 text-purple-500" />
                      <h4 className="font-bold text-sm">Species Classification</h4>
                    </div>
                    <div className="text-xl font-bold capitalize mb-1">{species}</div>
                    {all_scores && Object.keys(all_scores).length > 0 && (
                      <div className="mt-3 space-y-1">
                        <p className="text-xs text-muted-foreground mb-2">All Species Scores:</p>
                        {Object.entries(all_scores)
                          .sort(([, a], [, b]) => b - a)
                          .map(([speciesName, score]) => (
                            <div key={speciesName} className="flex items-center gap-2">
                              <div className="flex-1 bg-muted/50 rounded-full h-2 overflow-hidden">
                                <div
                                  className={cn(
                                    "h-full rounded-full transition-all",
                                    speciesName === species
                                      ? "bg-purple-500"
                                      : "bg-muted-foreground/20"
                                  )}
                                  style={{ width: `${score * 100}%` }}
                                />
                              </div>
                              <span className="text-xs capitalize w-16">{speciesName}</span>
                              <span className="text-xs font-mono w-12 text-right">
                                {(score * 100).toFixed(1)}%
                              </span>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4">
                  {match && (
                    <div className="bg-secondary/50 p-4 rounded-xl col-span-2">
                      <div className="flex items-center gap-2 mb-2">
                        <Database className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium">
                          Jaguar Identity
                        </span>
                      </div>
                      <div className="text-xl font-bold">
                        {jaguar_name || jaguar_id}
                      </div>
                      {jaguar_id && jaguar_name && (
                        <div className="text-xs text-muted-foreground mt-1">
                          ID: {jaguar_id}
                        </div>
                      )}
                    </div>
                  )}
                  <div
                    className={cn(
                      "bg-secondary/50 p-4 rounded-xl",
                      !match && "col-span-2",
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">
                        {match ? "Similarity" : "Confidence"}
                      </span>
                    </div>
                    <div className="text-2xl font-bold">
                      {match ? similarity.toFixed(4) : `${percentage}%`}
                    </div>
                  </div>
                  {match && (
                    <div className="bg-secondary/50 p-4 rounded-xl">
                      <div className="flex items-center gap-2 mb-2">
                        <Award className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium">Confidence</span>
                      </div>
                      <div className="text-2xl font-bold">{percentage}%</div>
                    </div>
                  )}
                </div>

                {/* Threshold Info */}
                {match && (
                  <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded-lg">
                    <p>
                      <strong>Match Threshold:</strong> 0.80 • Scores above this
                      indicate a confident match with an existing jaguar
                    </p>
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        </motion.div>
      </DialogContent>
    </Dialog>
  );
};

export default ResultsDisplay;
