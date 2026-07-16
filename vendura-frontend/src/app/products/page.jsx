import Container from "@/components/Container";
import api from "@/lib/api";

export default async function ProductsPage() {
  let products = [];
  let error = "";
  try {
    const response = await api.get("/api/products/");
    products = response.data?.results || [];
  } catch {
    error = "Não foi possivel carregar os produtos. Tente novamente";
  }

  return (
    <main className="flex-1 py-6 md:py-16">
      <Container>
        <section className="grid gap-12 justify-center grid-cols-[repeat(auto-fill,250px)]">
          {error && (
            <p className="bg-red-100 text-red-700 px-4 py-3 rounded-xl border border-red-200 font-medium text-sm">
              {error}
            </p>
          )}
          {products.map((product) => (
            <article
              key={product.id}
              className="flex flex-col justify-between items-start gap-2 border border-border bg-surface rounded-lg shadow-sm hover:-translate-y-1 transition-all duration-200 cursor-pointer overflow-hidden w-60"
            >
              <div className=" bg-gray-300 w-full h-40 " />
              <div className="flex flex-col gap-3 px-4 py-3">
                <h3 className="font-medium text-base text-text-primary line-clamp-2 text-ellipsis">
                  {product.name}
                </h3>
                <span className="text-text-secondary font-medium text-lg ">
                  R$ {product.price}
                </span>
              </div>
            </article>
          ))}
        </section>
      </Container>
    </main>
  );
}
