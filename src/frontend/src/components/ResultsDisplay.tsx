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

  const circumference = 2 * Math.PI * 60;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl p-0 overflow-hidden">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, type: "spring" }}
          className="w-full"
        >
          <div className="bg-card p-6">
            <DialogHeader className="mb-6">
              <DialogTitle className="text-2xl font-bold text-center">
                {match ? "Match Found!" : "New Jaguar Registered"}
              </DialogTitle>
              <DialogDescription className="text-center text-sm">
                {match
                  ? "This jaguar matches an existing individual in our database"
                  : "Successfully registered as a new jaguar identity"}
              </DialogDescription>
            </DialogHeader>

            <div className="grid md:grid-cols-[auto_1fr] gap-6 items-start">
              {/* Circular Progress - Smaller */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
                className="flex justify-center"
              >
                <div className="relative">
                  <svg className="w-40 h-40 transform -rotate-90">
                    {/* Background circle */}
                    <circle
                      cx="80"
                      cy="80"
                      r="60"
                      stroke="currentColor"
                      strokeWidth="10"
                      fill="none"
                      className="text-muted/20"
                    />
                    {/* Progress circle */}
                    <motion.circle
                      cx="80"
                      cy="80"
                      r="60"
                      stroke="currentColor"
                      strokeWidth="10"
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
                      <div className="text-3xl font-bold mb-1">
                        {match ? `${Math.round(similarity * 100)}%` : `${percentage}%`}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {match ? "Match" : "Confidence"}
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
                className="space-y-4"
              >
                {/* Verdict */}
                <div
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl border-2",
                    match
                      ? "bg-green-500/10 border-green-500/50"
                      : "bg-blue-500/10 border-blue-500/50",
                  )}
                >
                  {match ? (
                    <>
                      <CheckCircle2 className="h-6 w-6 text-green-500 shrink-0" />
                      <div>
                        <h4 className="font-bold text-base">Known Jaguar</h4>
                        <p className="text-xs text-muted-foreground">
                          {jaguar_name || `ID: ${jaguar_id}`}
                        </p>
                      </div>
                    </>
                  ) : (
                    <>
                      <User className="h-6 w-6 text-blue-500 shrink-0" />
                      <div>
                        <h4 className="font-bold text-base">New Identity</h4>
                        <p className="text-xs text-muted-foreground">
                          {jaguar_name}
                        </p>
                      </div>
                    </>
                  )}
                </div>

                {/* Species Classification - Compact */}
                {species && (
                  <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border-2 border-purple-500/30 p-3 rounded-xl">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Award className="h-4 w-4 text-purple-500" />
                        <h4 className="font-bold text-xs">Species</h4>
                      </div>
                      <div className="text-lg font-bold capitalize">{species}</div>
                    </div>
                    {all_scores && Object.keys(all_scores).length > 0 && (
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(all_scores)
                          .sort(([, a], [, b]) => b - a)
                          .slice(0, 4)
                          .map(([speciesName, score]) => (
                            <div key={speciesName} className="flex items-center gap-1 text-xs">
                              <span className="capitalize truncate flex-1">{speciesName}:</span>
                              <span className="font-mono font-medium">
                                {(score * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Stats - Horizontal */}
                <div className="grid grid-cols-3 gap-3">
                  {match && (
                    <div className="bg-secondary/50 p-3 rounded-lg">
                      <div className="flex items-center gap-1 mb-1">
                        <Database className="h-3 w-3 text-primary" />
                        <span className="text-xs font-medium">Similarity</span>
                      </div>
                      <div className="text-xl font-bold">
                        {(similarity * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                  <div className={cn("bg-secondary/50 p-3 rounded-lg", !match && "col-span-2")}>
                    <div className="flex items-center gap-1 mb-1">
                      <TrendingUp className="h-3 w-3 text-primary" />
                      <span className="text-xs font-medium">Confidence</span>
                    </div>
                    <div className="text-xl font-bold">{percentage}%</div>
                  </div>
                  {match && (
                    <div className="bg-secondary/50 p-3 rounded-lg">
                      <div className="flex items-center gap-1 mb-1">
                        <User className="h-3 w-3 text-primary" />
                        <span className="text-xs font-medium">ID</span>
                      </div>
                      <div className="text-sm font-bold truncate" title={jaguar_name || jaguar_id}>
                        {jaguar_name || jaguar_id}
                      </div>
                    </div>
                  )}
                </div>

                {/* Threshold Info - Compact */}
                <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded-lg">
                  {match ? (
                    <p>
                      Similarity {Math.round(similarity * 100)}% above 70% threshold = confident match with <strong>{jaguar_name || jaguar_id}</strong>
                    </p>
                  ) : (
                    <p>
                      {percentage}% species confidence • Not found in database
                    </p>
                  )}
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
