"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, CheckCircle2, Loader2, FolderOpen } from "lucide-react";

interface FolderPickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentFolder: string;
  onSelectFolder: (folder: string) => void;
}

export function FolderPickerDialog({
  open,
  onOpenChange,
  currentFolder,
  onSelectFolder,
}: FolderPickerDialogProps) {
  const [folderPath, setFolderPath] = useState(currentFolder);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    errors: string[];
  } | null>(null);

  const handleValidate = async () => {
    if (!folderPath.trim()) return;

    setIsValidating(true);
    setValidationResult(null);

    try {
      const response = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rootFolder: folderPath }),
      });

      const result = await response.json();
      setValidationResult(result);
    } catch (error) {
      setValidationResult({
        valid: false,
        errors: ["Failed to validate folder path"],
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleConfirm = () => {
    if (validationResult?.valid) {
      onSelectFolder(folderPath);
      onOpenChange(false);
    }
  };

  const handleInputChange = (value: string) => {
    setFolderPath(value);
    setValidationResult(null);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5" />
            Select Project Folder
          </DialogTitle>
          <DialogDescription>
            Enter the path to a demo project folder containing the experiment
            runs you want to analyze.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="folder-path">Project Root Path</Label>
            <div className="flex gap-2">
              <Input
                id="folder-path"
                value={folderPath}
                onChange={(e) => handleInputChange(e.target.value)}
                placeholder="/home/user/projects/demo"
                className="font-mono text-sm"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={handleValidate}
                disabled={isValidating || !folderPath.trim()}
              >
                {isValidating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Validate"
                )}
              </Button>
            </div>
          </div>

          {/* Validation result */}
          {validationResult && (
            <div
              className={`rounded-lg border p-3 ${
                validationResult.valid
                  ? "border-[oklch(0.6_0.18_145)] bg-[oklch(0.95_0.03_145)]"
                  : "border-[oklch(0.55_0.2_25)] bg-[oklch(0.95_0.03_25)]"
              }`}
            >
              <div className="flex items-start gap-2">
                {validationResult.valid ? (
                  <CheckCircle2 className="h-4 w-4 text-[oklch(0.5_0.15_145)] mt-0.5" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-[oklch(0.5_0.15_25)] mt-0.5" />
                )}
                <div className="text-sm">
                  {validationResult.valid ? (
                    <span className="text-[oklch(0.4_0.1_145)]">
                      Valid project folder found
                    </span>
                  ) : (
                    <div className="space-y-1">
                      <span className="text-[oklch(0.4_0.15_25)] font-medium">
                        Invalid project folder:
                      </span>
                      <ul className="list-disc pl-4 text-[oklch(0.45_0.1_25)]">
                        {validationResult.errors.map((error, i) => (
                          <li key={i}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Help text */}
          <div className="rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground">
            <p className="font-medium mb-1">Required files:</p>
            <ul className="list-disc pl-4 space-y-0.5 font-mono">
              <li>logs/results.jsonl</li>
              <li>logs/state.json</li>
              <li>manifest.yaml</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!validationResult?.valid}
          >
            Open Project
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
