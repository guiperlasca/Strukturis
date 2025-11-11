import { FileText, Zap, Shield, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";

const features = [
  {
    icon: FileText,
    title: "Escritórios Jurídicos",
    description: "Converta petições, contratos e documentos judiciais escaneados em texto editável instantaneamente.",
  },
  {
    icon: Zap,
    title: "Departamentos de RH",
    description: "Digitalize currículos, documentos pessoais e formulários com precisão e agilidade.",
  },
  {
    icon: Shield,
    title: "Contabilidade",
    description: "Transforme notas fiscais, recibos e demonstrativos escaneados em dados estruturados.",
  },
  {
    icon: TrendingUp,
    title: "Economia de Tempo",
    description: "Reduza 90% do tempo gasto em transcrição manual e minimize erros humanos.",
  },
];

export const FeaturesSection = () => {
  return (
    <section className="py-16">
      <div className="mb-12 text-center">
        <h2 className="mb-4 text-3xl font-bold text-foreground">
          Solução Profissional para Seu Negócio
        </h2>
        <p className="text-lg text-muted-foreground">
          Automatize a transcrição de documentos digitalizados com IA avançada
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card
              key={feature.title}
              className="group p-6 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10"
            >
              <div className="mb-4 inline-flex rounded-lg bg-gradient-primary p-3">
                <Icon className="h-6 w-6 text-primary-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="text-sm text-muted-foreground">
                {feature.description}
              </p>
            </Card>
          );
        })}
      </div>
    </section>
  );
};
