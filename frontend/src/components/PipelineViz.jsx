import { Upload, ScanLine, BarChart3, FileOutput } from "lucide-react";

const STEPS = [
  { icon: Upload, label: "Upload", key: "upload" },
  { icon: ScanLine, label: "Detect", key: "detect" },
  { icon: BarChart3, label: "Quantify", key: "quantify" },
  { icon: FileOutput, label: "Report", key: "report" },
];

export default function PipelineViz({ activeStep = -1, completed = false }) {
  return (
    <div data-testid="pipeline-viz" className="flex items-center justify-center gap-1 sm:gap-2">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const isDone = completed || i < activeStep;
        const isActive = i === activeStep;
        return (
          <div key={step.key} className="flex items-center">
            <div
              data-testid={`pipeline-step-${step.key}`}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                isActive
                  ? "bg-[#0F52BA] text-white"
                  : isDone
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : "bg-slate-50 text-slate-400 border border-slate-200"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`w-4 sm:w-8 h-px mx-0.5 ${
                isDone ? "bg-emerald-300" : "bg-slate-200"
              }`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
