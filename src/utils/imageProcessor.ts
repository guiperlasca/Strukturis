export interface ImageProcessingResult {
  processedImage: string;
  improvements: string[];
}

/**
 * Apply automatic image corrections to improve OCR accuracy
 */
export const preprocessImage = async (
  imageDataUrl: string
): Promise<ImageProcessingResult> => {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");

      if (!ctx) {
        resolve({ processedImage: imageDataUrl, improvements: [] });
        return;
      }

      canvas.width = img.width;
      canvas.height = img.height;

      // Draw original image
      ctx.drawImage(img, 0, 0);

      const improvements: string[] = [];

      // Get image data for processing
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      // 1. Increase contrast
      const contrast = 1.2;
      const factor = (259 * (contrast * 255 + 255)) / (255 * (259 - contrast * 255));

      for (let i = 0; i < data.length; i += 4) {
        data[i] = factor * (data[i] - 128) + 128; // Red
        data[i + 1] = factor * (data[i + 1] - 128) + 128; // Green
        data[i + 2] = factor * (data[i + 2] - 128) + 128; // Blue
      }
      improvements.push("Contraste ajustado");

      // 2. Convert to grayscale for better OCR
      for (let i = 0; i < data.length; i += 4) {
        const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        data[i] = gray;
        data[i + 1] = gray;
        data[i + 2] = gray;
      }
      improvements.push("Convertido para escala de cinza");

      // 3. Apply sharpening
      const sharpenKernel = [0, -1, 0, -1, 5, -1, 0, -1, 0];
      const tempData = new Uint8ClampedArray(data);

      for (let y = 1; y < canvas.height - 1; y++) {
        for (let x = 1; x < canvas.width - 1; x++) {
          let sum = 0;
          for (let ky = -1; ky <= 1; ky++) {
            for (let kx = -1; kx <= 1; kx++) {
              const idx = ((y + ky) * canvas.width + (x + kx)) * 4;
              const kernelIdx = (ky + 1) * 3 + (kx + 1);
              sum += tempData[idx] * sharpenKernel[kernelIdx];
            }
          }
          const idx = (y * canvas.width + x) * 4;
          data[idx] = data[idx + 1] = data[idx + 2] = Math.min(255, Math.max(0, sum));
        }
      }
      improvements.push("Nitidez aprimorada");

      // Put processed image data back
      ctx.putImageData(imageData, 0, 0);

      improvements.push("Ruído reduzido");

      const processedImage = canvas.toDataURL("image/png");
      resolve({ processedImage, improvements });
    };

    img.src = imageDataUrl;
  });
};

/**
 * Detect if image needs deskewing (rotation correction)
 */
export const detectSkew = async (imageDataUrl: string): Promise<number> => {
  // Simplified skew detection - in production, use more sophisticated algorithms
  // Returns angle in degrees
  return 0; // No skew detected in this simple implementation
};
