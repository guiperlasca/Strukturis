import { CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";

const useCases = [
  {
    category: "Documentos Jurídicos",
    items: [
      "Petições e pareceres escaneados",
      "Contratos e procurações antigas",
      "Documentos judiciais arquivados",
    ],
  },
  {
    category: "Recursos Humanos",
    items: [
      "Currículos físicos digitalizados",
      "Documentos pessoais de colaboradores",
      "Formulários e fichas de admissão",
    ],
  },
  {
    category: "Contabilidade & Fiscal",
    items: [
      "Notas fiscais antigas escaneadas",
      "Recibos e comprovantes",
      "Demonstrativos e relatórios",
    ],
  },
];

export const UseCasesSection = () => {
  return (
    <section className="py-16">
      <div className="mb-12 text-center">
        <h2 className="mb-4 text-3xl font-bold text-foreground">
          Casos de Uso
        </h2>
        <p className="text-lg text-muted-foreground">
          Ideal para diversos tipos de documentos corporativos
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {useCases.map((useCase) => (
          <Card key={useCase.category} className="p-6">
            <h3 className="mb-4 text-xl font-semibold text-foreground">
              {useCase.category}
            </h3>
            <ul className="space-y-3">
              {useCase.items.map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-success" />
                  <span className="text-sm text-muted-foreground">{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </section>
  );
};
