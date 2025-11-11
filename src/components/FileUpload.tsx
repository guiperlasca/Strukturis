import { useCallback, useState } from "react";
import { Upload, FileText, Image as ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
}

export const FileUpload = ({ onFileSelect, isProcessing }: FileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      const file = files[0];

      if (file && (file.type.includes("pdf") || file.type.includes("image"))) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div
      className={cn(
        "relative rounded-2xl border-2 border-dashed transition-all duration-300",
        isDragging
          ? "border-primary bg-primary/5 shadow-glow"
          : "border-border bg-card hover:border-primary/50 hover:bg-primary/5",
        isProcessing && "pointer-events-none opacity-50"
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <label className="flex min-h-[400px] cursor-pointer flex-col items-center justify-center gap-6 p-12">
        <div className="rounded-full bg-gradient-primary p-6 shadow-lg">
          <Upload className="h-12 w-12 text-primary-foreground" />
        </div>

        <div className="text-center">
          <h3 className="mb-2 text-xl font-semibold text-foreground">
            Arraste e solte seus arquivos aqui
          </h3>
          <p className="text-sm text-muted-foreground">
            ou clique para selecionar
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Tamanho máximo: 50MB
          </p>
        </div>

        <div className="flex gap-4">
          <div className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2">
            <FileText className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium text-secondary-foreground">PDF</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2">
            <ImageIcon className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium text-secondary-foreground">Imagens</span>
          </div>
        </div>

        <input
          type="file"
          className="hidden"
          accept=".pdf,image/*"
          onChange={handleFileInput}
          disabled={isProcessing}
        />
      </label>
    </div>
  );
};
