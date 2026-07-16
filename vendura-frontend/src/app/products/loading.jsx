import Container from "@/components/Container";

export default function Loading() {
  return (
    <main className="flex-1 py-6 md:py-16">
      <Container>
        <section className="grid gap-12 justify-center grid-cols-[repeat(auto-fill,250px)]">
          {Array.from({ length: 10}).map((_, i) => (
            <div key={i} className="flex flex-col gap-2 border border-border bg-surface shadow-sm overflow-hidden w-55">
                <div className="bg-border w-full h-40 animate-pulse" />

                <div className="flex flex-col gap-3 px-4 py-3">
                    <div className="bg-border h-4 w-3/4 rounded animate-pulse" />
                    <div className="bg-border h-4 w-1/3 rounded animate-pulse" />
                </div>

            </div>
          ))}
        </section>
      </Container>
    </main>
  );
}
