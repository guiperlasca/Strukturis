import { Card } from "@/components/ui/card";

const stats = [
  { value: "90%", label: "Redução de Tempo" },
  { value: "95%+", label: "Precisão OCR" },
  { value: "100+", label: "Páginas/Hora" },
  { value: "24/7", label: "Disponibilidade" },
];

export const StatsSection = () => {
  return (
    <section className="py-12">
      <Card className="bg-gradient-primary p-8 text-center shadow-lg">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="space-y-2">
              <div className="text-4xl font-bold text-primary-foreground">
                {stat.value}
              </div>
              <div className="text-sm text-primary-foreground/90">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </section>
  );
};
