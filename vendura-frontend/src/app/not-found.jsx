import Link from "next/link";

export default function NotFound() {
  return (
    <main className="bg-background flex-1 flex flex-col justify-center items-center text-center p-6 gap-2">
        <h1 className="font-extrabold text-3xl text-text-primary">Ih, deu ruim!</h1>
        <p className="font-medium text-text-secondary text-lg max-w-md text-balance">Alguém chutou a tomada dessa página. Mas não se preocupe, o resto do site continua funcionando!</p>

        <Link href='/' className="px-4 py-2 bg-accent hover:bg-accent-hover rounded-lg text-white text-base font-medium transition-all duration-200 active:scale-98">Voltar para Home</Link>
    </main>
  );
}
