import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2 } from "lucide-react";

interface ImagePreviewProps {
  originalImage: string;
  processedImage: string;
  improvements: string[];
}

export const ImagePreview = ({
  originalImage,
  processedImage,
  improvements,
}: ImagePreviewProps) => {
  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="mb-2 text-lg font-semibold text-foreground">
          Correção Automática Aplicada
        </h3>
        <div className="flex flex-wrap gap-2">
          {improvements.map((improvement, index) => (
            <Badge key={index} variant="secondary" className="gap-1">
              <CheckCircle2 className="h-3 w-3 text-success" />
              {improvement}
            </Badge>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">Original</p>
          <div className="overflow-hidden rounded-lg border border-border">
            <img
              src={originalImage}
              alt="Original"
              className="h-auto w-full object-contain"
              style={{ maxHeight: "300px" }}
            />
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">
            Imagem Processada
          </p>
          <div className="overflow-hidden rounded-lg border border-border bg-secondary">
            <img
              src={processedImage}
              alt="Processada"
              className="h-auto w-full object-contain"
              style={{ maxHeight: "300px" }}
            />
          </div>
        </div>
      </div>
    </Card>
  );
};
